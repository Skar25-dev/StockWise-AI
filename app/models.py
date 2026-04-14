from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    category = Column(String)
    current_stock = Column(Integer)
    price = Column(Float)

class DailySale(Base):
    __tablename__ = "daily_sales"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    date = Column(Date)
    quantity = Column(Integer) # Cuánto se vendió ese día

    product = relationship("Product")
