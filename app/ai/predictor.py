import joblib
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import Product, DailySale
from pathlib import Path

MODEL_PATH = Path(__file__).resolve().parent / "model_store" / "stock_model.pkl"
model = joblib.load(MODEL_PATH)

def predict_sales_range(db: Session, product_name: str, days_to_forecast: int = 30):
    product = db.query(Product).filter(Product.name == product_name).first()
    
    last_sales = db.query(DailySale).filter(DailySale.product_id == product.id)\
                   .order_by(DailySale.date.desc()).limit(7).all()

    if len(last_sales) < 7:
        return None

    current_window = [s.quantity for s in reversed(last_sales)]
    predictions = []
    future_date = datetime.now() + timedelta(days=1)

    for _ in range(days_to_forecast):
        month = future_date.month
        day_of_week = future_date.weekday()
        is_weekend = 1 if day_of_week >= 5 else 0
        sales_lag_1 = current_window[-1]
        rolling_mean_7 = np.mean(current_window)

        input_df = pd.DataFrame([[month, day_of_week, is_weekend, sales_lag_1, rolling_mean_7]],
                                columns=['month', 'day_of_week', 'is_weekend', 'sales_lag_1', 'rolling_mean_7'])
        
        pred = max(0, model.predict(input_df)[0])
        
        predictions.append({
            "date": future_date.strftime("%d %b"),
            "value": round(float(pred), 2)
        })

        current_window.pop(0)
        current_window.append(pred)
        future_date += timedelta(days=1)
    
    return predictions