import os
import sqlite3
from flask import Flask, render_template, request, jsonify, redirect, url_for

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "../marketscraper/marketscraper/market_product.db")

app = Flask(__name__)

SUPERMARKETS = {
    "sklavenitis": "Σκλαβενίτης",
    "ab": "ΑΒ Βασιλόπουλος",
}


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
    selected_supermarket = request_args.get("market", "").strip()

    conn = get_db()
    cur = conn.cursor()

    supermarket_filter = None
    if supermarket_name != "all":
        supermarket_filter = get_supermarket_id(conn, supermarket_name)
        if supermarket_filter is None:
            conn.close()
            return None, [], [], [], q, category, subcategory, favorite, selected_supermarket

    if supermarket_name == "all" and selected_supermarket:
        supermarket_filter = get_supermarket_id(conn, selected_supermarket)

    cur.execute("SELECT name FROM supermarkets ORDER BY name")
    available_supermarkets = [r[0] for r in cur.fetchall() if r[0]]

    if supermarket_filter is None:
        cur.execute(
            """
            SELECT DISTINCT COALESCE(canonical_category, category) AS category_name
            FROM products
            WHERE COALESCE(canonical_category, category) IS NOT NULL
            ORDER BY category_name COLLATE NOCASE
            """
        )
    else:
        cur.execute(
            """
            SELECT DISTINCT COALESCE(canonical_category, category) AS category_name
            FROM products
            WHERE supermarket_id=?
              AND COALESCE(canonical_category, category) IS NOT NULL
            ORDER BY category_name COLLATE NOCASE
            """,
            (supermarket_filter,)
        )
    categories = [r[0] for r in cur.fetchall() if r[0]]

    subcategories = []
    if category:
        if supermarket_filter is None:
            cur.execute(
                """
                SELECT DISTINCT COALESCE(canonical_subcategory, subcategory) AS subcategory_name
                FROM products
                WHERE COALESCE(canonical_category, category)=?
                  AND COALESCE(canonical_subcategory, subcategory) IS NOT NULL
                ORDER BY subcategory_name COLLATE NOCASE
                """,
                (category,)
            )
        else:
            cur.execute(
                """
                SELECT DISTINCT COALESCE(canonical_subcategory, subcategory) AS subcategory_name
                FROM products
                WHERE supermarket_id=?
                  AND COALESCE(canonical_category, category)=?
                  AND COALESCE(canonical_subcategory, subcategory) IS NOT NULL
                ORDER BY subcategory_name COLLATE NOCASE
                """,
                (supermarket_filter, category)
            )
        subcategories = [r[0] for r in cur.fetchall() if r[0]]

    sql = """
    SELECT
        p.id,
        p.name,
        p.category,
        p.subcategory,
        p.canonical_category,
        p.canonical_subcategory,
        p.price,
        p.price_kg,
        p.last_seen,
        p.favorite,
        s.name AS supermarket_code
    FROM products p
    JOIN supermarkets s ON s.id = p.supermarket_id
    WHERE 1=1
    """
    params = []

    if supermarket_filter is not None:
        sql += " AND p.supermarket_id=?"
        params.append(supermarket_filter)

    if q:
        sql += " AND p.name LIKE ?"
        params.append(f"%{q}%")
    if category:
        sql += " AND COALESCE(p.canonical_category, p.category)=?"
        params.append(category)
    if subcategory:
        sql += " AND COALESCE(p.canonical_subcategory, p.subcategory)=?"
        params.append(subcategory)
    if favorite in ("0", "1"):
        sql += " AND p.favorite=?"
        params.append(int(favorite))

    sql += """
    ORDER BY
        COALESCE(p.canonical_category, p.category),
        COALESCE(p.canonical_subcategory, p.subcategory),
        p.name
    """

    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()

    return rows, categories, subcategories, available_supermarkets, q, category, subcategory, favorite, selected_supermarket


@app.route("/")
def index():
    rows, categories, subcategories, available_supermarkets, q, category, subcategory, favorite, selected_supermarket = \
        get_products("all", request.args)

    return render_template(
        "products.html",
        products=rows,
        supermarket="all",
        supermarket_name="Όλα τα supermarkets",
        categories=categories,
        subcategories=subcategories,
        available_supermarkets=available_supermarkets,
        selected_market=selected_supermarket,
        selected_category=category,
        selected_subcategory=subcategory,
        query=q,
        favorite=favorite,
        is_unified=True,
        supermarkets=SUPERMARKETS,
    )


@app.route("/products/<supermarket>")
def products(supermarket):
    if supermarket not in SUPERMARKETS:
        return redirect(url_for("index"))

    rows, categories, subcategories, available_supermarkets, q, category, subcategory, favorite, selected_supermarket = \
        get_products(supermarket, request.args)

    return render_template(
        "products.html",
        products=rows,
        supermarket=supermarket,
        supermarket_name=SUPERMARKETS[supermarket],
        categories=categories,
        subcategories=subcategories,
        available_supermarkets=available_supermarkets,
        selected_market=selected_supermarket,
        selected_category=category,
        selected_subcategory=subcategory,
        query=q,
        favorite=favorite,
        is_unified=False,
        supermarkets=SUPERMARKETS,
    )


@app.route("/skl")
def index_skl():
    return redirect(url_for("products", supermarket="sklavenitis", **request.args))


@app.route("/ab")
def index_ab():
    return redirect(url_for("products", supermarket="ab", **request.args))


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
    conn.close()

    return jsonify({"ok": True, "favorite": new_val})


@app.route("/history/<int:product_id>")
def history(product_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT p.name,
               COALESCE(p.canonical_category, p.category),
               COALESCE(p.canonical_subcategory, p.subcategory),
               s.name
        FROM products p
        JOIN supermarkets s ON s.id = p.supermarket_id
        WHERE p.id=?
        """,
        (product_id,)
    )
    prod = cur.fetchone()
    if not prod:
        return jsonify({"ok": False, "error": "Product not found"}), 404

    cur.execute(
        "SELECT price, price_kg, date FROM price_history WHERE product_id=? ORDER BY date DESC, id DESC",
        (product_id,)
    )
    hist = [dict(price=r[0], price_kg=r[1], date=r[2]) for r in cur.fetchall()]
    conn.close()

    return jsonify({
        "ok": True,
        "product": {
            "id": product_id,
            "name": prod[0],
            "category": prod[1],
            "subcategory": prod[2],
            "supermarket": prod[3],
        },
        "history": hist
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)