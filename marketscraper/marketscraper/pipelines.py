import sqlite3
from email.message import EmailMessage
from itemadapter import ItemAdapter
from datetime import date
import os
import smtplib

email = os.environ["GMAIL_USR"]
password = os.environ["GMAIL_PW"]

class SQLitePipeline:
    def open_spider(self, spider):
        self.connection = sqlite3.connect("products.db")
        self.cursor = self.connection.cursor()
        self.create_tables()
        self.price_fluct_lines = []

    def close_spider(self, spider):

        body = "\n".join(self.price_fluct_lines)
        self.send_mail(body)

        self.connection.commit()
        self.connection.close()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                category TEXT,
                subcategory TEXT,
                price REAL,
                price_kg REAL,
                last_seen DATE,
                favorite INT DEFAULT 0,
                UNIQUE(name, category, subcategory)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                price REAL,
                price_kg REAL,
                date DATE,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        category = adapter.get('category')
        subcategory = adapter.get('subcategory')
        products = adapter.get('products')

        price_fluct = []


        for prod in products:
            name = prod.get('name')
            price = prod.get('price')
            price_kg = prod.get('price/kg')

            self.cursor.execute("""
                INSERT OR IGNORE INTO products (name, category, subcategory, price, price_kg, last_seen)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, category, subcategory, price, price_kg, str(date.today())))

            #Block to notify price change
            #Δεδομένου ότι περιέχεται το προϊόν στο table, και έρχεται απλά με νέα τιμή.
            #Γίνεται ignore στο instert και θα πάει για update τιμής.
            #Πρίν το update τιμής, φέρνω το παλιό με μια select και συγκρίνω.
            #Αν υπάρχει διαφορά τιμής υπάρχοντος αγαπημένου προϊόντος, ειδοποιείται.
            self.cursor.execute("""
                SELECT name, price, favorite
                FROM products
                WHERE name = ? AND category = ? AND subcategory = ?
            """, (name, category, subcategory))
            row = self.cursor.fetchone()



            if row[0] == name and row[2] == 1 and not row[1] == price:
                self.price_fluct_lines.append(f'Αγαπημένο {prod['name']}\n'
                                              f'Νέα τιμή: {prod["price"]}\n'
                                              f'Παλιά τιμή: {row[1]}\n')


            #upd database with new price
            self.cursor.execute("""
                UPDATE products
                SET price=?, price_kg=?, last_seen=?
                WHERE name=? AND category=? AND subcategory=?
            """, (price, price_kg, str(date.today()), name, category, subcategory))


        return item

    def send_mail(self, body):
        msg = EmailMessage()
        msg["From"] = "zervolaos29@gmail.com"
        msg["To"] = "zervolaos29@gmail.com"
        msg["Subject"] = f"Ekptwseis {date.today()}"
        msg.set_content(body, subtype="plain", charset="utf-8")

        with smtplib.SMTP("smtp.gmail.com", 587) as mailcon:
            mailcon.starttls()
            mailcon.login(email, password)
            mailcon.send_message(msg)
