import os
import sqlite3
from flask import Flask, render_template, request, jsonify

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "../marketscraper/marketscraper/market_product.db")

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_supermarket_id(conn, name):
    cur = conn.cursor()
    cur.execute("SELECT id FROM supermarkets WHERE name=?", (name,))
    row = cur.fetchone()
    return row[0] if row else None

def get_products(supermarket_name, request_args):
    q = request_args.get("q", "").strip()
    category = request_args.get("category", "").strip()
    subcategory = request_args.get("subcategory", "").strip()
    favorite = request_args.get("favorite", "").strip()

    conn = get_db()
    sm_id = get_supermarket_id(conn, supermarket_name)
    if sm_id is None:
        return None, [], [], q, category, subcategory, favorite

    cur = conn.cursor()

    cur.execute(
        "SELECT DISTINCT category FROM products WHERE supermarket_id=? ORDER BY category COLLATE NOCASE",
        (sm_id,)
    )
    categories = [r[0] for r in cur.fetchall() if r[0]]

    subcategories = []
    if category:
        cur.execute(
            "SELECT DISTINCT subcategory FROM products WHERE supermarket_id=? AND category=? ORDER BY subcategory COLLATE NOCASE",
            (sm_id, category)
        )
        subcategories = [r[0] for r in cur.fetchall() if r[0]]

    sql = "SELECT id, name, category, subcategory, price, price_kg, last_seen, favorite FROM products WHERE supermarket_id=?"
    params = [sm_id]

    if q:
        sql += " AND name LIKE ?"
        params.append(f"%{q}%")
    if category:
        sql += " AND category=?"
        params.append(category)
    if subcategory:
        sql += " AND subcategory=?"
        params.append(subcategory)
    if favorite in ("0", "1"):
        sql += " AND favorite=?"
        params.append(int(favorite))

    sql += " ORDER BY category, subcategory, name"

    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()

    return rows, categories, subcategories, q, category, subcategory, favorite


@app.route("/")
def index():
    return render_template('home.html')


@app.route("/skl")
def index_skl():
    rows, categories, subcategories, q, category, subcategory, favorite = get_products("sklavenitis", request.args)
    return render_template("index_skl.html",
                           products=rows,
                           categories=categories,
                           subcategories=subcategories,
                           selected_category=category,
                           selected_subcategory=subcategory,
                           query=q,
                           favorite=favorite)


@app.route("/ab")
def index_ab():
    rows, categories, subcategories, q, category, subcategory, favorite = get_products("ab", request.args)
    return render_template("index_ab.html",
                           products=rows,
                           categories=categories,
                           subcategories=subcategories,
                           selected_category=category,
                           selected_subcategory=subcategory,
                           query=q,
                           favorite=favorite)


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


@app.route("/history/<int:product_id>")
def history(product_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT name, category, subcategory FROM products WHERE id=?", (product_id,))
    prod = cur.fetchone()
    if not prod:
        return jsonify({"ok": False, "error": "Product not found"}), 404
    cur.execute(
        "SELECT price, price_kg, date FROM price_history WHERE product_id=? ORDER BY date DESC, id DESC",
        (product_id,)
    )
    hist = [dict(price=r[0], price_kg=r[1], date=r[2]) for r in cur.fetchall()]
    return jsonify({
        "ok": True,
        "product": {"id": product_id, "name": prod[0], "category": prod[1], "subcategory": prod[2]},
        "history": hist
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)