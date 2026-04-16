from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.ai.predictor import predict_sales

app = FastAPI(title="StockWise AI API")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
    
@app.get("/")
def read_root():
    return {"message": {"StockWise AI API is running"}}

@app.get("/predict/{product_name}")
def get_prediction(product_name: str, db: Session = Depends(get_db)):
    prediction = predict_sales(db, product_name)

    if prediction is None:
        raise HTTPException(status_code=404, detail = "Producto no encontrado o sin datos suficientes")
    
    return {
        "product": product_name,
        "predicted_sales_next_day": prediction,
        "unit": "units"
    }
