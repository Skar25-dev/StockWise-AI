from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.ai import predictor, trainer
from app.database import Base
from app.models import DailySale, Product

DAYS_OF_HISTORY = 40


@pytest.fixture
def db_session():
    """SQLite en memoria con 2 productos y 40 días de ventas deterministas."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    products = [
        Product(name="Café", category="Alimentos", current_stock=500, price=5.0),
        Product(name="Consola", category="Electrónica", current_stock=3, price=300.0),
    ]
    session.add_all(products)
    session.flush()

    today = date.today()
    for product in products:
        for age in range(DAYS_OF_HISTORY, 0, -1):
            session.add(
                DailySale(
                    product_id=product.id,
                    date=today - timedelta(days=age),
                    quantity=10 + (age % 7),
                )
            )
    session.commit()

    yield session

    session.close()
    engine.dispose()


@pytest.fixture(autouse=True)
def isolated_model(tmp_path_factory, monkeypatch):
    """Aísla el modelo de IA: por defecto no hay ninguno y no se toca el real."""
    model_dir = tmp_path_factory.mktemp("model_store")
    monkeypatch.setattr(predictor, "MODEL_PATH", model_dir / "stock_model.pkl")
    monkeypatch.setattr(predictor, "_model", None)
    monkeypatch.setattr(trainer, "MODEL_DIR", model_dir)
    return model_dir


@pytest.fixture
def trained_model(db_session):
    """Entrena un modelo real (pequeño) con los datos del fixture y lo deja cargable."""
    trainer.train_model(bind=db_session.get_bind())
    return predictor.get_model()
