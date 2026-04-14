import pandas as pd
from sqlalchemy import create_engine
from app.database import DB_PATH

def prepare_features():
    engine = create_engine(f"sqlite:///{DB_PATH}")
    query = """
    SELECT ds.date, ds.quantity, p.name as product_name
    FROM daily_sales ds
    JOIN products p on ds.product_id = p.id
    """

    df = pd.read_sql(query, engine)
    df['date'] = pd.to_datetime(df['date'])

    df = df.sort_values(['product_name', 'date'])

    df['month'] = df['date'].dt.month
    df['days_of_week'] = df['date'].dt.dayofweek # 0=Lunes, 6=Domingo
    df['is_weekend'] = df['days_of_week'].apply(lambda x: 1 if x >= 5 else 0)

    # Creamos columnas con la venta del día anterior (lag_1) y de hace una semana (lag_7)
    df['sales_lag_1'] = df.groupby('product_name')['quantity'].shift(1)
    df['sales_lag_7'] = df.groupby('product_name')['quantity'].shift(7)

    # Media móvil de los últimos 7 días
    df['rolling_mean_7'] = df.groupby('product_name')['quantity'].transform(
        lambda x: x.rolling(window=7).mean()
    )

    df = df.dropna()

    print("✅ Feature Engineering completado.")
    print(f"Dataset listo con {df.shape[0]} filas y {df.shape[1]} columnas.")

    return df

if __name__ == "__main__":
    features_df = prepare_features()

    print("\n--- Vista previa del dataset 'inteligente' ---")
    cols_to_show = ['product_name', 'quantity', 'month', 'sales_lag_1', 'rolling_mean_7']
    print(features_df[cols_to_show].tail(10))