# product_manager_rest_validated.py

import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
from sqlalchemy import create_engine, Column, Integer as SQLInt, String, Float as SQLFloat
from sqlalchemy.orm import sessionmaker, declarative_base

# ---------------- Database Configuration -----------------
DB_USER = 'manager'
DB_PASSWORD = 'eniso123'
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'myproducts'

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ---------------- Database Setup -----------------
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Product(Base):
    __tablename__ = "products"
    id = Column(SQLInt, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    stock = Column(SQLInt, nullable=False)
    price = Column(SQLFloat, nullable=False)

Base.metadata.create_all(engine)

# ---------------- Pydantic Models with Validation -----------------
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, example="Laptop")
    stock: int = Field(..., ge=0, le=10000, example=10)
    price: float = Field(..., ge=0.0, le=1000000.0, example=999.99)

    @validator("name")
    def name_not_blank(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be blank")
        return v

class ProductUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100, example="Laptop Pro")
    stock: int | None = Field(None, ge=0, le=10000, example=15)
    price: float | None = Field(None, ge=0.0, le=1000000.0, example=1099.99)

    @validator("name")
    def name_not_blank(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Name cannot be blank")
        return v

class ProductResponse(BaseModel):
    id: int
    name: str
    stock: int
    price: float

# ---------------- FastAPI App -----------------
app = FastAPI(title="Inventory REST API with Validation", version="1.0")

# ---------------- CRUD Endpoints -----------------
@app.post("/products/", response_model=ProductResponse)
def create_product(product: ProductCreate):
    session = Session()
    try:
        new_product = Product(name=product.name, stock=product.stock, price=product.price)
        session.add(new_product)
        session.commit()
        session.refresh(new_product)
        return new_product
    finally:
        session.close()

@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int):
    session = Session()
    try:
        product = session.query(Product).filter_by(id=product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product ID {product_id} not found")
        return product
    finally:
        session.close()

@app.put("/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, update: ProductUpdate):
    session = Session()
    try:
        product = session.query(Product).filter_by(id=product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product ID {product_id} not found")

        if update.name is not None:
            product.name = update.name
        if update.stock is not None:
            product.stock = update.stock
        if update.price is not None:
            product.price = update.price

        session.commit()
        session.refresh(product)
        return product
    finally:
        session.close()

@app.delete("/products/{product_id}", response_model=dict)
def delete_product(product_id: int):
    session = Session()
    try:
        product = session.query(Product).filter_by(id=product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product ID {product_id} not found")
        session.delete(product)
        session.commit()
        return {"message": f"Product ID {product_id} deleted successfully"}
    finally:
        session.close()

# ---------------- Run Instructions -----------------
# Run this API with: uvicorn product_manager_rest_validated:app --reload --host 0.0.0.0 --port 8000
