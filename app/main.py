import os
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pathlib import Path
from app.database import SessionLocal, engine
from app.models import Product, DailySale
from app.ai.predictor import predict_sales

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
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    sales = db.query(DailySale).filter(DailySale.product_id == product_id)\
              .order_by(DailySale.date.asc()).all()
    
    recent_sales = sales[-30:] if len(sales) > 30 else sales

    if not recent_sales:
        raise HTTPException(status_code=404, detail="No hay datos de ventas")

    prediction = predict_sales(db, product.name)

    return {
        "labels": [s.date.strftime("%d %b") for s in recent_sales],
        "values": [s.quantity for s in recent_sales],
        "prediction": prediction,
        "product_name": product.name
    }