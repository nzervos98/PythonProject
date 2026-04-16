from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Supermarket(Base):
    __tablename__ = "supermarkets"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)  # supermarket names

    products = relationship("Product", back_populates="supermarket")
    taxonomy_mappings = relationship("SourceTaxonomyMapping", back_populates="supermarket")


class CanonicalTaxonomy(Base):
    __tablename__ = "canonical_taxonomy"

    id = Column(Integer, primary_key=True)

    category_code = Column(String, nullable=False)
    category_label = Column(String, nullable=False)

    subcategory_code = Column(String, nullable=True)
    subcategory_label = Column(String, nullable=True)

    is_active = Column(Integer, default=1)
    sort_order = Column(Integer, default=0)

    source_mappings = relationship("SourceTaxonomyMapping", back_populates="canonical_taxonomy")
    products = relationship("Product", back_populates="canonical_taxonomy")

class SourceTaxonomyMapping(Base):
    __tablename__ = "source_taxonomy_mappings"

    id = Column(Integer, primary_key=True)

    supermarket_id = Column(Integer, ForeignKey("supermarkets.id"), nullable=False)
    source_category = Column(String, nullable=False)
    source_subcategory = Column(String, nullable=True)

    canonical_taxonomy_id = Column(Integer, ForeignKey("canonical_taxonomy.id"), nullable=False)

    mapping_type = Column(String, default="exact_pair")  # exact_pair / category_fallback
    is_active = Column(Integer, default=1)
    notes = Column(String, nullable=True)

    supermarket = relationship("Supermarket", back_populates="taxonomy_mappings")
    canonical_taxonomy = relationship("CanonicalTaxonomy", back_populates="source_mappings")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)

    supermarket_id = Column(Integer, ForeignKey("supermarkets.id"), nullable=False)

    name = Column(String, nullable=False)

    # Raw/source taxonomy όπως έρχεται από κάθε supermarket
    category = Column(String, nullable=True)
    subcategory = Column(String, nullable=True)

    # Canonical taxonomy
    canonical_taxonomy_id = Column(Integer, ForeignKey("canonical_taxonomy.id"), nullable=True)
    canonical_category = Column(String, nullable=True)
    canonical_subcategory = Column(String, nullable=True)

    price = Column(Float, nullable=True)
    price_kg = Column(Float, nullable=True)
    last_seen = Column(Date, nullable=True)

    favorite = Column(Integer, default=0)  # 0/1

    supermarket = relationship("Supermarket", back_populates="products")
    canonical_taxonomy = relationship("CanonicalTaxonomy", back_populates="products")
    history = relationship(
        "PriceHistory",
        back_populates="product",
        cascade="all, delete-orphan",
    )


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    price = Column(Float, nullable=True)
    price_kg = Column(Float, nullable=True)
    date = Column(Date, nullable=True)

    product = relationship("Product", back_populates="history")


def init_db(db_path: str = "market_product.db"):
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    print("Database initialized successfully.")
    return engine


if __name__ == "__main__":
    init_db()