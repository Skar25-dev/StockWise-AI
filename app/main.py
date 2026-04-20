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
    
    history = [{"date": s.date.strftime("%d  %b"), "value": s.quantity} for s in reversed(sales)]
    forecast = predict_sales_range(db, product.name, days_to_forecast=30)
    
    tomorrow_demand = forecast[0]['value']
    month_demand = sum([f['value'] for f in forecast])
    current_stock = product.current_stock

    day_status = "ÓPTIMO"
    day_color = "optimal"
    day_rec = 0

    if current_stock < tomorrow_demand:
        day_status = "CRÍTICO (Agotado mañana)"
        day_color = "critical"
        day_rec = int(tomorrow_demand * 1.5 - current_stock) # Pedido de urgencia
    
    month_status = "ÓPTIMO"
    month_color = "optimal"
    month_safety = month_demand * 1.2 # Stock deseado (demanda + 20% de seguridad)
    month_rec = max(0, int(month_safety - current_stock))

    if current_stock < (month_demand * 0.5):
        month_status = "CRÍTICO (Rotura este mes)"
        month_color = "critical"
    elif current_stock < month_demand:
        month_status = "BAJO (No cubre el mes)"
        month_color = "low"
    
    return {
        "history": history,
        "forecast": forecast,
        "product_name": product.name,
        "inventory": {
            "current": current_stock,
            "day": {
                "status": day_status,
                "color": day_color,
                "recommendation": day_rec,
                "demand": round(tomorrow_demand, 1)
            },
            "month": {
                "status": month_status,
                "color": month_color,
                "recommendation": month_rec,
                "demand": round(month_demand)
            }
        }
    }