import os
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pathlib import Path
from app.database import SessionLocal, engine
from app.models import Product, DailySale
from app.ai.predictor import predict_sales_range

app = FastAPI(title="StockWise AI Dashboard")

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "app" / "templates"
STATIC_DIR = BASE_DIR / "app" / "static"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"products": products, "app_name": "StockWise AI"}
    )

@app.get("/api/chart-data/{product_id}")
async def get_chart_data(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        print(f"❌ Error: Producto con ID {product_id} no encontrado")
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    sales = db.query(DailySale).filter(DailySale.product_id == product_id)\
              .order_by(DailySale.date.desc()).limit(15).all()
    
    if len(sales) < 7:
        print(f"⚠️ Error: El producto '{product.name}' solo tiene {len(sales)} ventas. Necesita 7 para la IA.")
        raise HTTPException(status_code=404, detail="Datos insuficientes")

    history = [{"date": s.date.strftime("%d %b"), "value": s.quantity} for s in reversed(sales)]

    forecast_results = predict_sales_range(db, product.name, days_to_forecast=30)

    return {
        "history": history,
        "forecast": forecast_results,
        "product_name": product.name
    }