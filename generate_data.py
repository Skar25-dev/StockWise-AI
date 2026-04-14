import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.database import SessionLocal, engine, Base
from app.models import Product, DailySale

Base.metadata.create_all(bind=engine)
db = SessionLocal()

def seed_smart_data():
    products_config = [
        {"name": "Consola NextGen", "cat": "Electrónica", "base": 15, "trend": 0.02, "season": 1.0}, # Sube un 2% cada mes
        {"name": "Piscina Inflable", "cat": "Hogar", "base": 2, "trend": 0, "season": "summer"}, # Solo vende en verano
        {"name": "Café Premium", "cat": "Alimentos", "base": 20, "trend": 0, "season": 1.0}, # Estable
    ]

    db.query(DailySale).delete()

    for p_conf in products_config:
        p = Product(
            name=p_conf["name"], 
            category=p_conf["cat"], 
            current_stock=100, 
            price=50.0
        )
        db.add(p)
        db.flush()

        start_date = datetime.now() - timedelta(days=730)

        for i in range(730):
            current_date = start_date + timedelta(days=i)
            month = current_date.month

            seasonal_multiplier = 1.0
            if p_conf["season"] == "summer":
                if month in [6, 7, 8]: seasonal_multiplier = 5.0 # Vende x5 en verano
                else: seasonal_multiplier = 0.2                  # Casi nada el resto del año
            
            # Lógica de tendencia (crecimiento lineal)
            trend_multiplier = 1 + (p_conf["trend"] * (i - 30)) # Es el mes actual

            #Ruido aleatorio (variación diaria normal)
            noise = np.random.normal(0, 2)

            # Cálculo final de ventas diarias
            sales_val = int(max(0, (p_conf["base"] * seasonal_multiplier * trend_multiplier) + noise))

            sale = DailySale(product_id=p.id, date=current_date.date(), quantity=sales_val)
            db.add(sale)
        
    db.commit()
    print("✅ Historia de 2 años generada para todos los productos.")

if __name__ == "__main__":
    seed_smart_data()