import joblib
import pytest
from sqlalchemy import create_engine

from app.ai import feature_engineer, predictor, trainer
from app.database import Base
from app.models import DailySale, Product

from .conftest import DAYS_OF_HISTORY

FEATURES = ["month", "day_of_week", "is_weekend", "sales_lag_1", "rolling_mean_7"]


# ---------- Feature engineering ----------

def test_features_are_built_and_incomplete_rows_dropped(db_session):
    df = feature_engineer.prepare_features(db_session.get_bind())

    assert set(FEATURES) <= set(df.columns)
    assert not df.isna().any().any()
    # sales_lag_7 necesita 7 días previos: se pierden 7 filas por producto
    assert len(df) == 2 * (DAYS_OF_HISTORY - 7)
    assert (df["is_weekend"] == (df["day_of_week"] >= 5).astype(int)).all()


def test_rolling_mean_is_the_mean_of_the_last_7_days(db_session):
    df = feature_engineer.prepare_features(db_session.get_bind())
    cafe = df[df["product_name"] == "Café"].reset_index(drop=True)

    # Dos filas consecutivas: lag_1 de la segunda == quantity de la primera
    assert cafe.loc[1, "sales_lag_1"] == cafe.loc[0, "quantity"]
    # La media móvil de un patrón semanal (10..16) es siempre 13
    assert cafe["rolling_mean_7"].round(6).eq(13.0).all()


# ---------- Entrenamiento ----------

def test_train_model_saves_a_loadable_model(db_session, isolated_model):
    trainer.train_model(bind=db_session.get_bind())

    model_path = isolated_model / "stock_model.pkl"
    assert model_path.exists()
    assert hasattr(joblib.load(model_path), "predict")


def test_train_model_with_empty_database_raises():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with pytest.raises(Exception):
        trainer.train_model(bind=engine)


# ---------- Predictor ----------

def test_predict_without_model_raises_clear_error(db_session):
    with pytest.raises(predictor.ModelNotTrainedError):
        predictor.predict_sales_range(db_session, "Café")


def test_predict_returns_requested_horizon_with_non_negative_values(db_session, trained_model):
    forecast = predictor.predict_sales_range(db_session, "Café", days_to_forecast=30)

    assert len(forecast) == 30
    assert all(point["value"] >= 0 for point in forecast)
    assert set(forecast[0]) == {"date", "value"}


def test_predict_unknown_product_returns_none(db_session, trained_model):
    """Antes lanzaba AttributeError ('NoneType' has no attribute 'id')."""
    assert predictor.predict_sales_range(db_session, "No existe") is None


def test_predict_with_less_than_7_sales_returns_none(db_session, trained_model):
    nuevo = Product(name="Nuevo", category="Hogar", current_stock=1, price=1.0)
    db_session.add(nuevo)
    db_session.flush()
    db_session.add(DailySale(product_id=nuevo.id, date=__import__("datetime").date.today(), quantity=3))
    db_session.commit()

    assert predictor.predict_sales_range(db_session, "Nuevo") is None
