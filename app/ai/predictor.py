import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Product, DailySale
from pathlib import Path

MODEL_PATH = Path(__file__).resolve().parent / "model_store" / "stock_model.pkl"
model = joblib.load(MODEL_PATH)

def predict_sales(db: Session, product_name: str):
    product = db.query(Product).filter(Product.name == product_name).first()
    if not product:
        return None
    
    last_sales = db.query(DailySale)\
                .filter(DailySale.product_id == product.id)\
                .order_by(DailySale.date.desc())\
                .limit(7).all()

    if not last_sales:
        return None

    next_date = datetime.now()

    month = next_date.month
    day_of_week = next_date.weekday()
    is_weekend = 1 if day_of_week >= 5 else 0

    sales_lag_1 = last_sales[0].quantity # La venta más reciente
    rolling_mean_7 = np.mean([s.quantity for s in last_sales])

    input_data = pd.DataFrame([[
        month, day_of_week, is_weekend, sales_lag_1, rolling_mean_7
    ]], columns=['month', 'day_of_week', 'is_weekend', 'sales_lag_1', 'rolling_mean_7'])

    prediction = model.predict(input_data)[0]

    return round(prediction, 2)