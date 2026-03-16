from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from itemadapter import ItemAdapter
from marketscraper.models import Supermarket, Product, PriceHistory


class SQLAlchemyPipeline:

    def open_spider(self, spider):
        import os
        DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "market_product.db")
        engine = create_engine(f"sqlite:///{DB_PATH}")

        self.Session = sessionmaker(bind=engine)

        # Βρες ή φτιάξε το supermarket record βάσει spider.name
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

        category = adapter.get('category')
        item_subcategory = adapter.get('subcategory') or ''
        products = adapter.get('products') or []

        for prod in products:
            name = prod.get('name')
            if not name:
                continue

            price = prod.get('price')
            price_kg = prod.get('price/kg')
            subcategory = prod.get('subcat') or item_subcategory

            product = session.query(Product).filter_by(
                name=name,
                supermarket_id=self.supermarket_id
            ).first()

            if product is None:
                product = Product(
                    supermarket_id=self.supermarket_id,
                    name=name,
                    category=category,
                    subcategory=subcategory,
                    price=price,
                    price_kg=price_kg,
                    last_seen=date.today(),
                    favorite=0
                )
                session.add(product)
            else:
                if product.favorite == 1 and product.price != price:
                    history = PriceHistory(
                        product_id=product.id,
                        price=product.price,
                        price_kg=product.price_kg,
                        date=date.today()
                    )
                    session.add(history)

                product.price = price
                product.price_kg = price_kg
                product.subcategory = subcategory
                product.last_seen = date.today()

        session.commit()
        session.close()
        return item

    def close_spider(self, spider):
        pass  # email notification αργότερα