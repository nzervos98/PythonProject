import os
import sqlite3
from flask import Flask, render_template, request, jsonify

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "../marketscraper/marketscraper/products.db")

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    #extract args in html filter sections w/ get
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    subcategory = request.args.get("subcategory", "").strip()
    favorite = request.args.get("favorite", "").strip()  # "", "1", or "0"

    conn = get_db()
    cur = conn.cursor()

    # fetch filter lists - fetchall when app launches
    cur.execute("SELECT DISTINCT category FROM products ORDER BY category COLLATE NOCASE")
    categories = [r[0] for r in cur.fetchall() if r[0]]

    subcategories = []
    if category:
        cur.execute("SELECT DISTINCT subcategory FROM products WHERE category=? ORDER BY subcategory COLLATE NOCASE", (category,))
        subcategories = [r[0] for r in cur.fetchall() if r[0]]

    # build query
    sql = "SELECT id, name, category, subcategory, price, price_kg, last_seen, favorite FROM products WHERE 1=1"
    params = []
    #word search
    if q:
        sql += " AND name LIKE ?"
        params.append(f"%{q}%")
    #filter by cat
    if category:
        sql += " AND category=?"
        params.append(category)
    #filter by subcat
    if subcategory:
        sql += " AND subcategory=?"
        params.append(subcategory)
    #filter by fav status
    if favorite in ("0", "1"):
        sql += " AND favorite=?"
        params.append(int(favorite))

    sql += " ORDER BY category, subcategory, name"

    cur.execute(sql, params)
    rows = cur.fetchall()

    return render_template("index.html",
                           products=rows,
                           categories=categories,
                           subcategories=subcategories,
                           selected_category=category,
                           selected_subcategory=subcategory,
                           query=q,
                           favorite=favorite)

#com with js function - update fav = 1 or fav = 0 on button click
@app.route("/toggle-favorite/<int:product_id>", methods=["POST"])
def toggle_favorite(product_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT favorite FROM products WHERE id=?", (product_id,))
    row = cur.fetchone()
    if not row:
        return jsonify({"ok": False, "error": "Product not found"}), 404
    new_val = 0 if row[0] == 1 else 1
    cur.execute("UPDATE products SET favorite=? WHERE id=?", (new_val, product_id))
    conn.commit()
    return jsonify({"ok": True, "favorite": new_val})

#select from price history function based on each prod
@app.route("/history/<int:product_id>")
def history(product_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT name, category, subcategory FROM products WHERE id=?", (product_id,))
    prod = cur.fetchone()
    if not prod:
        return jsonify({"ok": False, "error": "Product not found"}), 404
    cur.execute("SELECT price, price_kg, date FROM price_history WHERE product_id=? ORDER BY date DESC, id DESC", (product_id,))
    hist = [dict(price=r[0], price_kg=r[1], date=r[2]) for r in cur.fetchall()]
    return jsonify({
        "ok": True,
        "product": {"id": product_id, "name": prod[0], "category": prod[1], "subcategory": prod[2]},
        "history": hist
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
