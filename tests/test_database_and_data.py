from sqlalchemy import func

import generate_data
from app.database import get_database_url
from app.models import DailySale, Product


# ---------- Selección de base de datos ----------

def test_database_url_defaults_to_sqlite():
    url = get_database_url({})
    assert url.startswith("sqlite:///") and url.endswith("stockwise.db")


def test_database_url_uses_environment_variable():
    url = get_database_url({"DATABASE_URL": "postgresql://admin:pw@db:5432/stockwise_db"})
    assert url == "postgresql://admin:pw@db:5432/stockwise_db"


# ---------- Generador de datos ----------

def test_generate_data_can_run_twice_without_integrity_error(db_session):
    """Regresión: la segunda ejecución fallaba por el nombre de producto único."""
    generate_data.seed_smart_data(db_session)
    generate_data.seed_smart_data(db_session)

    assert db_session.query(Product).count() == 3
    assert db_session.query(func.count(DailySale.id)).scalar() == 3 * 730


def test_sales_are_linked_to_their_product(db_session):
    sale = db_session.query(DailySale).first()
    assert sale.product.id == sale.product_id
