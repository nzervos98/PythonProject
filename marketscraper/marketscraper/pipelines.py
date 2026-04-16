from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from itemadapter import ItemAdapter

from .models import Supermarket, Product, PriceHistory
from .taxonomy_resolver import resolve_canonical_taxonomy, normalize_taxonomy_text


class SQLAlchemyPipeline:

    def open_spider(self, spider):
        import os

        db_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "market_product.db"
        )
        engine = create_engine(f"sqlite:///{db_path}")

        self.Session = sessionmaker(bind=engine)

        session = self.Session()
        supermarket = session.query(Supermarket).filter_by(name=spider.name).first()

        if supermarket is None:
            supermarket = Supermarket(name=spider.name)
            session.add(supermarket)
            session.commit()

        self.supermarket_id = supermarket.id
        session.close()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        session = self.Session()

        category = normalize_taxonomy_text(adapter.get("category"))
        item_subcategory = normalize_taxonomy_text(adapter.get("subcategory") or "")
        products = adapter.get("products") or []

        for prod in products:
            name = prod.get("name")
            if not name:
                continue

            price = prod.get("price")
            price_kg = prod.get("price/kg")
            subcategory = normalize_taxonomy_text(prod.get("subcat") or item_subcategory)

            product = session.query(Product).filter_by(
                name=name,
                supermarket_id=self.supermarket_id
            ).first()

            # -------------------------------------------------
            # INSERT
            # -------------------------------------------------
            if product is None:
                canonical = resolve_canonical_taxonomy(
                    session=session,
                    supermarket_id=self.supermarket_id,
                    source_category=category,
                    source_subcategory=subcategory,
                )

                product = Product(
                    supermarket_id=self.supermarket_id,
                    name=name,
                    category=category,
                    subcategory=subcategory,
                    canonical_taxonomy_id=canonical.id if canonical else None,
                    canonical_category=canonical.category_label if canonical else None,
                    canonical_subcategory=canonical.subcategory_label if canonical else None,
                    price=price,
                    price_kg=price_kg,
                    last_seen=date.today(),
                    favorite=0,
                )
                session.add(product)

            # -------------------------------------------------
            # UPDATE
            # -------------------------------------------------
            else:
                if product.favorite == 1 and product.price != price:
                    history = PriceHistory(
                        product_id=product.id,
                        price=product.price,
                        price_kg=product.price_kg,
                        date=date.today(),
                    )
                    session.add(history)

                product.price = price
                product.price_kg = price_kg
                product.last_seen = date.today()

                # raw category: μπορείς να το ενημερώνεις μόνο αν έχει τιμή
                if category:
                    product.category = category

                # IMPORTANT:
                # blank subcategory ΔΕΝ overwrite-άρει υπάρχουσα
                if subcategory:
                    product.subcategory = subcategory

                    canonical = resolve_canonical_taxonomy(
                        session=session,
                        supermarket_id=self.supermarket_id,
                        source_category=category,
                        source_subcategory=subcategory,
                    )

                    # αν βρεθεί canonical, το ενημερώνουμε
                    if canonical:
                        product.canonical_taxonomy_id = canonical.id
                        product.canonical_category = canonical.category_label
                        product.canonical_subcategory = canonical.subcategory_label

        session.commit()
        session.close()
        return item

    def close_spider(self, spider):
        pass