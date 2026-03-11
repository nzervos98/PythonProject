from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from itemadapter import ItemAdapter
from models import Supermarket, Product, PriceHistory


class SQLAlchemyPipeline:

    def open_spider(self, spider):
        engine = create_engine("sqlite:///market_product.db")
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
        subcategory = adapter.get('subcategory')
        products = adapter.get('products')

        for prod in products:
            name = prod.get('name')
            price = prod.get('price')
            price_kg = prod.get('price/kg')

            # Βρες ή φτιάξε το προϊόν
            product = session.query(Product).filter_by(
                name=name,
                supermarket_id=self.supermarket_id
            ).first()

            if product is None:
                # Νέο προϊόν → δημιούργησε
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
                # Υπάρχει ήδη → έλεγξε αν άλλαξε η τιμή
                if product.favorite == 1 and product.price != price:
                    history = PriceHistory(
                        product_id=product.id,
                        price=product.price,      # αποθήκευσε την ΠΑΛΙΑ τιμή
                        price_kg=product.price_kg,
                        date=date.today()
                    )
                    session.add(history)

                # Update
                product.price     = price
                product.price_kg  = price_kg
                product.last_seen = date.today()

        session.commit()
        session.close()
        return item

    def close_spider(self, spider):
        pass  # email notification αργότερα