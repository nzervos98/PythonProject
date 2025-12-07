import sqlite3

DB_PATH = "products.db"
con = sqlite3.connect(DB_PATH)
cur = con.cursor()

for trg in ("trg_fav_on_add_initial_history", "trg_fav_off_delete_history", "trg_append_history_on_price_change"):
    cur.execute(f"DROP TRIGGER IF EXISTS {trg}")

cur.execute("""
CREATE TRIGGER trg_fav_on_add_initial_history
AFTER UPDATE OF favorite ON products
WHEN NEW.favorite = 1 AND OLD.favorite = 0
BEGIN
  INSERT INTO price_history (product_id, price, price_kg, date)
  VALUES (NEW.id, NEW.price, NEW.price_kg, DATE('now'));
END;
""")

cur.execute("""
CREATE TRIGGER trg_fav_off_delete_history
AFTER UPDATE OF favorite ON products
WHEN NEW.favorite = 0 AND OLD.favorite = 1
BEGIN
  DELETE FROM price_history WHERE product_id = OLD.id;
END;
""")

cur.execute("""
CREATE TRIGGER trg_append_history_on_price_change
AFTER UPDATE OF price, price_kg ON products
WHEN NEW.favorite = 1 AND (
       IFNULL(NEW.price, -999999) <> IFNULL(OLD.price, -999999)
    OR IFNULL(NEW.price_kg, -999999) <> IFNULL(OLD.price_kg, -999999)
)
BEGIN
  INSERT INTO price_history (product_id, price, price_kg, date)
  VALUES (NEW.id, NEW.price, NEW.price_kg, DATE('now'));
END;
""")

con.commit()
con.close()
print("Triggers created/updated successfully.")
