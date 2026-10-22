import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from app.ai.feature_engineer import prepare_features

MODEL_DIR = Path(__file__).resolve().parent / "model_store"

def train_model(bind=None, model_dir=None):
    df = prepare_features(bind)

    features = ['month', 'day_of_week', 'is_weekend', 'sales_lag_1', 'rolling_mean_7']
    X = df[features]
    y = df['quantity']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print(f"🧠 Entrenando modelo con {len(X_train)} registros...")

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    rmse = root_mean_squared_error(y_test, predictions)

    print("\n--- 📊 RESULTADOS DEL MODELO ---")
    print(f"Error Medio Absoluto (MAE): {mae:.2f} unidades")
    print(f"Raíz del Error Cuadrático (RMSE): {rmse:.2f} unidades")
    print("--------------------------------")

    model_dir = Path(model_dir) if model_dir is not None else MODEL_DIR
    model_dir.mkdir(parents=True, exist_ok=True)

    model_path = model_dir / "stock_model.pkl"
    joblib.dump(model, model_path)

    print(f"✅ Modelo guardado con éxito en: {model_path}")
    return model

if __name__ == "__main__":
    train_model()