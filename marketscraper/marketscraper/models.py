from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Supermarket(Base):
    __tablename__ = "supermarkets"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)  # "sklavenitis", "ab"

    products = relationship("Product", back_populates="supermarket")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    supermarket_id = Column(Integer, ForeignKey("supermarkets.id"), nullable=False)
    name = Column(String, nullable=False)
    category = Column(String)
    subcategory = Column(String)
    price = Column(Float)
    price_kg = Column(Float)
    last_seen = Column(Date)
    favorite = Column(Integer, default=0)  # True/False logikh

    supermarket = relationship("Supermarket", back_populates="products")
    history = relationship("PriceHistory", back_populates="product",
                               cascade="all, delete-orphan")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id         = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    price      = Column(Float)
    price_kg   = Column(Float)
    date       = Column(Date)

    product = relationship("Product", back_populates="history")


def init_db(db_path: str = "market_product.db"):
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    print("Database initialized successfully.")
    return engine


if __name__ == "__main__":
    init_db()