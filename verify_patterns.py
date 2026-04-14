import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

engine = create_engine("sqlite:///./data/stockwise.db")

query = """
SELECT ds.date, ds.quantity, p.name AS product_name 
FROM daily_sales ds 
JOIN products p ON ds.product_id = p.id
"""

df = pd.read_sql(query, engine)

df['date'] = pd.to_datetime(df['date'])
df['month'] = df['date'].dt.to_period('M')

print("--- 📊 ANÁLISIS DE TENDENCIA POR PRODUCTO (Venta Media Mensual) ---")

summary = df.groupby(['product_name', 'month'])['quantity'].mean().unstack(level=0)

print(summary.tail(6))

summary.plot(figsize=(10, 6), marker='o')
plt.title("Tendencia de Ventas Reales (Dataset para IA)")
plt.ylabel("Ventas diarias promedio")
plt.xlabel("Mes")
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(title="Producto")
plt.show()