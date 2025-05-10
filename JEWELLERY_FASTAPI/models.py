from JEWELLERY_FASTAPI.database import Base
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.sql import func


class User(Base):
    __tablename__ = "users"
    id = Column(Integer,primary_key=True,index=True)
    username = Column(String(50),nullable=False)
    email = Column(String(100),unique=True,nullable=False)
    password = Column(String(100),nullable=False)

# class Category(Base):
#     __tablename__="categories"
#     id = Column(Integer,primary_key=True,index=True)
#     name = Column(String(100),unique=True,nullable=False)

class Products(Base):
    __tablename__ = "products"
    id = Column(Integer,primary_key=True,index=True)
    name = Column(String(50),nullable=False)
    image = Column(String,nullable=False)
    description = Column(String(200))
    price = Column(Float)
    stock = Column(Integer)
    category = Column(String(100))


class Cart(Base):
    __tablename__="cart"
    id = Column(Integer,primary_key=True,index=True)
    user_id = Column(Integer,ForeignKey("users.id"),nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"),nullable=False)
    quantity=Column(Integer, nullable=False, default=1)

class Orders(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    total_price = Column(Float, nullable=False)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())



