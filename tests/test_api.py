import pytest
from fastapi.testclient import TestClient

from app import main
from app.models import DailySale, Product


@pytest.fixture
def client(db_session):
    # Sin "with TestClient": no se ejecuta el lifespan (create_all)
    main.app.dependency_overrides[main.get_db] = lambda: db_session
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()


def test_dashboard_lists_products(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "Café" in response.text and "Consola" in response.text


def test_chart_data_returns_history_forecast_and_inventory_status(client, db_session, trained_model):
    consola = db_session.query(Product).filter_by(name="Consola").one()  # stock 3

    data = client.get(f"/api/chart-data/{consola.id}").json()

    assert data["product_name"] == "Consola"
    assert len(data["history"]) == 15
    assert len(data["forecast"]) == 30
    assert data["inventory"]["current"] == 3
    # Stock 3 frente a una demanda de ~13 uds/día: crítico
    assert data["inventory"]["day"]["color"] == "critical"
    assert data["inventory"]["month"]["color"] == "critical"
    assert data["inventory"]["month"]["recommendation"] > 0


def test_chart_data_with_enough_stock_is_optimal(client, db_session, trained_model):
    cafe = db_session.query(Product).filter_by(name="Café").one()
    cafe.current_stock = 100_000
    db_session.commit()

    data = client.get(f"/api/chart-data/{cafe.id}").json()

    assert data["inventory"]["day"]["color"] == "optimal"
    assert data["inventory"]["month"]["color"] == "optimal"
    assert data["inventory"]["month"]["recommendation"] == 0


def test_chart_data_unknown_product_returns_404(client, trained_model):
    assert client.get("/api/chart-data/9999").status_code == 404


def test_chart_data_without_trained_model_returns_503(client, db_session):
    producto = db_session.query(Product).first()

    response = client.get(f"/api/chart-data/{producto.id}")

    assert response.status_code == 503
    assert "trainer" in response.json()["detail"]


def test_chart_data_with_too_little_history_returns_400(client, db_session, trained_model):
    """Regresión: antes lanzaba TypeError (500) al indexar forecast[0] siendo None."""
    from datetime import date

    nuevo = Product(name="Nuevo", category="Hogar", current_stock=1, price=1.0)
    db_session.add(nuevo)
    db_session.flush()
    db_session.add(DailySale(product_id=nuevo.id, date=date.today(), quantity=2))
    db_session.commit()

    response = client.get(f"/api/chart-data/{nuevo.id}")

    assert response.status_code == 400
