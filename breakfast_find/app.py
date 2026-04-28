from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from flask import Flask, abort, g, jsonify, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "breakfast.db"
TAIPEI_TZ = timezone(timedelta(hours=8))

STATUS_LABELS = {
    "pending": "待接單",
    "accepted": "已接單",
    "making": "製作中",
    "ready": "可取餐",
    "completed": "已完成",
    "cancelled": "已取消",
}

ALLOWED_TRANSITIONS = {  # 訂單狀態轉換規則
    "pending": ["accepted", "cancelled"],
    "accepted": ["making", "cancelled"],
    "making": ["ready"],
    "ready": ["completed"],
    "completed": [],
    "cancelled": [],
}

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        db = sqlite3.connect(DATABASE, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")  # 開 WAL，讓讀寫同時進行時比較穩
        db.execute("PRAGMA foreign_keys=ON")  # 開外鍵，避免主表刪掉後明細還留著
        g.db = db
    return g.db


@app.teardown_appcontext
def close_db(error: BaseException | None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def now_text() -> str:
    return datetime.now(TAIPEI_TZ).strftime("%Y-%m-%d %H:%M:%S")


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def status_text(status: str) -> str:
    return STATUS_LABELS.get(status, status)


def enrich_order(order: dict[str, Any]) -> dict[str, Any]:
    order["status_text"] = status_text(str(order.get("status", "")))
    order["next_statuses"] = ALLOWED_TRANSITIONS.get(str(order.get("status", "")), [])
    order["next_status_labels"] = {key: status_text(key) for key in order["next_statuses"]}
    return order


def success(data: dict[str, Any] | None = None):
    payload: dict[str, Any] = {"success": True}
    if data:
        payload.update(data)
    return jsonify(payload)


def fail(message: str, status_code: int = 400):
    return jsonify({"success": False, "message": message}), status_code


def clean_required(value: Any, field_name: str, max_len: int = 100) -> str:
    if value is None:
        raise ValueError(f"缺少 {field_name}")
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field_name} 不可空白")
    if len(text) > max_len:
        raise ValueError(f"{field_name} 太長")
    return text


def clean_optional(value: Any, max_len: int = 200) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return text[:max_len]


def parse_int(value: Any, field_name: str, min_value: int | None = None, max_value: int | None = None) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} 必須是整數")
    if min_value is not None and number < min_value:
        raise ValueError(f"{field_name} 不可小於 {min_value}")
    if max_value is not None and number > max_value:
        raise ValueError(f"{field_name} 不可大於 {max_value}")
    return number


def parse_option_ids(value: Any) -> list[int]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("option_ids 必須是陣列")
    option_ids = [parse_int(item, "option_id", 1) for item in value]
    if len(option_ids) != len(set(option_ids)):
        raise ValueError("option_ids 不可重複")
    return option_ids


def init_db() -> None:
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            image_filename TEXT NOT NULL DEFAULT 'default.jpg',
            base_price INTEGER NOT NULL CHECK(base_price >= 0),
            is_active INTEGER NOT NULL DEFAULT 1,
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS product_options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            option_group TEXT NOT NULL,
            option_name TEXT NOT NULL,
            extra_price INTEGER NOT NULL DEFAULT 0 CHECK(extra_price >= 0),
            is_active INTEGER NOT NULL DEFAULT 1,
            sort_order INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_product_options_product_id
            ON product_options(product_id);

        CREATE TABLE IF NOT EXISTS cart_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cart_code TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            base_price INTEGER NOT NULL CHECK(base_price >= 0),
            option_total INTEGER NOT NULL DEFAULT 0 CHECK(option_total >= 0),
            price INTEGER NOT NULL CHECK(price >= 0),
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            options_text TEXT NOT NULL DEFAULT '',
            option_ids TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(product_id) REFERENCES products(id)
        );

        CREATE INDEX IF NOT EXISTS idx_cart_items_cart_code
            ON cart_items(cart_code);

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT NOT NULL DEFAULT 'pending',
            total_amount INTEGER NOT NULL CHECK(total_amount >= 0),
            item_count INTEGER NOT NULL CHECK(item_count >= 0),
            customer_name TEXT NOT NULL DEFAULT '',
            phone TEXT NOT NULL DEFAULT '',
            pickup_time TEXT NOT NULL DEFAULT '',
            note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_orders_status
            ON orders(status);

        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            price INTEGER NOT NULL CHECK(price >= 0),
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            options_text TEXT NOT NULL DEFAULT '',
            option_ids TEXT NOT NULL DEFAULT '',
            subtotal INTEGER NOT NULL CHECK(subtotal >= 0),
            FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_order_items_order_id
            ON order_items(order_id);
        """
    )
    ensure_schema_upgrades(db)
    seed_products(db)
    db.commit()
    db.close()


def ensure_schema_upgrades(db: sqlite3.Connection) -> None:  # 舊版資料庫相容處理
    product_columns = db.execute("PRAGMA table_info(products)").fetchall()
    column_names = [row[1] for row in product_columns]
    if "image_filename" not in column_names:
        db.execute("ALTER TABLE products ADD COLUMN image_filename TEXT NOT NULL DEFAULT 'default.jpg'")


def seed_products(db: sqlite3.Connection) -> None:
    count = db.execute("SELECT COUNT(*) AS count FROM products").fetchone()[0]
    if count > 0:
        return
    current_time = now_text()
    products = [
        {"name": "九層塔炒海瓜子", "description": "海瓜子、九層塔、蒜末、薑末、米酒", "base_price": 170, "sort_order": 1, "image_filename": "九層塔炒海瓜子.jpg"},
        {"name": "五更腸旺", "description": "豬大腸、鴨血、花椒粒、蒜苗、辣椒", "base_price": 180, "sort_order": 2, "image_filename": "五更腸旺.jpg"},
        {"name": "牛肉炒飯", "description": "牛肉、雞蛋、蔥花、香Q米飯", "base_price": 130, "sort_order": 3, "image_filename": "牛肉炒飯.jpg"},
        {"name": "白灼蝦", "description": "鮮草蝦、蒜蓉醬", "base_price": 180, "sort_order": 4, "image_filename": "白灼蝦.jpg"},
        {"name": "豆酥鱈魚", "description": "鱈魚、豆酥、蔥花、米酒、蒜末、辣椒末", "base_price": 180, "sort_order": 5, "image_filename": "豆酥鱈魚.jpg"},
        {"name": "空心菜炒牛肉", "description": "牛肉、空心菜、米酒、蒜末、辣椒末", "base_price": 150, "sort_order": 6, "image_filename": "空心菜炒牛肉.jpg"},
        {"name": "空心菜炒羊肉", "description": "羊肉、空心菜、米酒、蒜末、辣椒末", "base_price": 150, "sort_order": 7, "image_filename": "空心菜炒羊肉.jpg"},
        {"name": "芹菜炒花枝", "description": "花枝、米酒、芹菜、胡蘿蔔", "base_price": 150, "sort_order": 8, "image_filename": "芹菜炒花枝.jpg"},
        {"name": "芹菜炒蝦仁", "description": "蝦仁、米酒、芹菜、胡蘿蔔", "base_price": 150, "sort_order": 9, "image_filename": "芹菜炒蝦仁.jpg"},
        {"name": "金沙蝦球", "description": "鮮蝦仁、洋蔥、蒜末、鹹蛋黃", "base_price": 170, "sort_order": 10, "image_filename": "金沙蝦球.jpg"},
        {"name": "青椒肉絲", "description": "豬肉絲、青椒、辣椒", "base_price": 120, "sort_order": 11, "image_filename": "青椒肉絲.jpg"},
        {"name": "涼拌蘆筍", "description": "蘆筍、美奶滋", "base_price": 100, "sort_order": 12, "image_filename": "涼拌蘆筍.jpg"},
        {"name": "清炒高麗菜", "description": "高麗菜、蒜頭、胡蘿蔔", "base_price": 90, "sort_order": 13, "image_filename": "清炒高麗菜.jpg"},
        {"name": "滑蛋蝦仁", "description": "蝦仁、雞蛋", "base_price": 140, "sort_order": 14, "image_filename": "滑蛋蝦仁.jpg"},
        {"name": "蔥爆牛肉", "description": "牛肉、蔥段、洋蔥、蒜末、乾辣椒", "base_price": 160, "sort_order": 15, "image_filename": "蔥爆牛肉.jpg"},
        {"name": "蔥爆羊肉", "description": "羊肉、蔥段、洋蔥、蒜末、乾辣椒", "base_price": 160, "sort_order": 16, "image_filename": "蔥爆羊肉.jpg"},
        {"name": "蝦仁炒飯", "description": "蝦仁、雞蛋、蔥花、香Q米飯", "base_price": 130, "sort_order": 17, "image_filename": "蝦仁炒飯.jpg"},
        {"name": "糖醋排骨", "description": "豬小排、鳳梨片、白芝麻", "base_price": 170, "sort_order": 18, "image_filename": "糖醋排骨.jpg"},
        {"name": "糖醋魚片", "description": "鮮魚片、青椒、甜椒、鳳梨片", "base_price": 180, "sort_order": 19, "image_filename": "糖醋魚片.jpg"},
        {"name": "薑絲大腸", "description": "豬大腸、嫩薑、辣椒、酸菜", "base_price": 160, "sort_order": 20, "image_filename": "薑絲大腸.jpg"},
        {"name": "蠔油牛肉", "description": "牛肉、蔥段、薑片、蒜末、乾辣椒", "base_price": 170, "sort_order": 21, "image_filename": "蠔油牛肉.jpg"},
        {"name": "鐵板豆腐", "description": "雞蛋豆腐、洋蔥、蒜末、蔥段", "base_price": 110, "sort_order": 22, "image_filename": "鐵板豆腐.jpg"},
        {"name": "九層塔煎蛋", "description": "雞蛋、九層塔", "base_price": 90, "sort_order": 23, "image_filename": "九層塔煎蛋.jpg"},
    ]
    for product in products:
        cursor = db.execute(
            """
            INSERT INTO products (name, description, image_filename, base_price, is_active, sort_order, created_at, updated_at)
            VALUES (?, ?, ?, ?, 1, ?, ?, ?)
            """,
            (product["name"], product["description"], product["image_filename"], product["base_price"], product["sort_order"], current_time, current_time),
        )
        product_id = cursor.lastrowid
        add_options_for_food(db, product_id)


def add_options_for_food(db: sqlite3.Connection, product_id: int) -> None:
    options = [
        (product_id, "辣度", "不辣", 0, 1),
        (product_id, "辣度", "小辣", 0, 2),
        (product_id, "辣度", "中辣", 0, 3),
        (product_id, "辣度", "大辣", 0, 4),
        (product_id, "加飯", "不要", 0, 5),
        (product_id, "加飯", "加飯", 10, 6),
    ]
    insert_options(db, options)


def add_options_for_drink(db: sqlite3.Connection, product_id: int) -> None:
    options = [
        (product_id, "溫度", "冰", 0, 1),
        (product_id, "溫度", "熱", 0, 2),
        (product_id, "甜度", "全糖", 0, 3),
        (product_id, "甜度", "少糖", 0, 4),
        (product_id, "甜度", "半糖", 0, 5),
        (product_id, "甜度", "微糖", 0, 6),
        (product_id, "甜度", "無糖", 0, 7),
    ]
    insert_options(db, options)


def insert_options(db: sqlite3.Connection, options: list[tuple[int, str, str, int, int]]) -> None:
    db.executemany(
        """
        INSERT INTO product_options (product_id, option_group, option_name, extra_price, is_active, sort_order)
        VALUES (?, ?, ?, ?, 1, ?)
        """,
        options,
    )


@app.route("/")
def index():
    return redirect(url_for("product_list_page"))


@app.route("/product")
@app.route("/products")
def product_list_page():
    products = get_active_products()
    return render_template("product_list.html", products=products)


@app.route("/product/<int:product_id>")
def product_detail_page(product_id: int):
    product = get_product_or_404(product_id)
    option_groups = get_option_groups(product_id)
    return render_template("product_detail.html", product=product, option_groups=option_groups)


@app.route("/cart")
def cart_page():
    return render_template("cart.html")


@app.route("/checkout")
def checkout_page():
    return render_template("checkout.html")


@app.route("/order_success/<int:order_id>")
def order_success_page(order_id: int):
    order = get_order_by_id(order_id)
    if order is None:
        abort(404)
    items = get_order_items(order_id)
    return render_template("order_success.html", order=enrich_order(order), items=items)


@app.route("/order_list")
def order_list_page():
    orders = get_all_orders()
    return render_template("order_list.html", orders=orders)


@app.route("/admin/orders")
def admin_orders_page():
    status_filter = request.args.get("status", "").strip()
    if status_filter and status_filter not in STATUS_LABELS:
        status_filter = ""
    orders = get_all_orders(status_filter or None)
    stats = get_today_stats()
    return render_template("admin_orders.html", orders=orders, stats=stats, statuses=STATUS_LABELS, current_status=status_filter)


@app.route("/api/products")
def products_json():
    return success({"products": get_active_products()})


@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    data = request.get_json(silent=True) or {}
    try:
        cart_code = clean_required(data.get("cart_code"), "cart_code", 80)
        product_id = parse_int(data.get("product_id"), "product_id", 1)
        quantity = parse_int(data.get("quantity"), "quantity", 1, 99)
        option_ids = parse_option_ids(data.get("option_ids", []))
        priced_item = build_priced_item(product_id, option_ids)
    except ValueError as exc:
        return fail(str(exc))
    db = get_db()
    current_time = now_text()
    option_ids_text = ",".join(str(option_id) for option_id in priced_item["option_ids"])
    existing = db.execute(
        """
        SELECT id, quantity
        FROM cart_items
        WHERE cart_code = ? AND product_id = ? AND option_ids = ?
        """,
        (cart_code, product_id, option_ids_text),
    ).fetchone()
    if existing:  # 相同商品加上相同選項就直接合併，避免購物車重複很多列
        new_quantity = existing["quantity"] + quantity
        db.execute(
            """
            UPDATE cart_items
            SET quantity = ?, product_name = ?, base_price = ?, option_total = ?, price = ?, options_text = ?, updated_at = ?
            WHERE id = ?
            """,
            (new_quantity, priced_item["product_name"], priced_item["base_price"], priced_item["option_total"], priced_item["price"], priced_item["options_text"], current_time, existing["id"]),
        )
        item_id = existing["id"]
    else:
        cursor = db.execute(
            """
            INSERT INTO cart_items (cart_code, product_id, product_name, base_price, option_total, price, quantity, options_text, option_ids, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (cart_code, product_id, priced_item["product_name"], priced_item["base_price"], priced_item["option_total"], priced_item["price"], quantity, priced_item["options_text"], option_ids_text, current_time, current_time),
        )
        item_id = cursor.lastrowid
    db.commit()
    return success({"message": "已加入購物車", "item_id": item_id})


@app.route("/get_cart_items")
def get_cart_items():
    cart_code = request.args.get("cart_code", "").strip()
    if not cart_code:
        return fail("缺少 cart_code")
    items = load_cart_items(cart_code)
    total_amount = sum(item["subtotal"] for item in items)
    total_quantity = sum(item["quantity"] for item in items)
    return success({"items": items, "count": len(items), "total_quantity": total_quantity, "total_amount": total_amount})


@app.route("/update_cart_item", methods=["POST"])
def update_cart_item():
    data = request.get_json(silent=True) or {}
    try:
        item_id = parse_int(data.get("item_id"), "item_id", 1)
        new_quantity = parse_int(data.get("new_quantity"), "new_quantity")
    except ValueError as exc:
        return fail(str(exc))
    db = get_db()
    existing = db.execute("SELECT id FROM cart_items WHERE id = ?", (item_id,)).fetchone()
    if existing is None:
        return fail("找不到這筆購物車商品", 404)
    if new_quantity <= 0:
        db.execute("DELETE FROM cart_items WHERE id = ?", (item_id,))
    else:
        db.execute("UPDATE cart_items SET quantity = ?, updated_at = ? WHERE id = ?", (new_quantity, now_text(), item_id))
    db.commit()
    return success({"message": "購物車已更新"})


@app.route("/delete_cart_item", methods=["POST"])
def delete_cart_item():
    data = request.get_json(silent=True) or {}
    try:
        item_id = parse_int(data.get("item_id"), "item_id", 1)
    except ValueError as exc:
        return fail(str(exc))
    db = get_db()
    cursor = db.execute("DELETE FROM cart_items WHERE id = ?", (item_id,))
    db.commit()
    if cursor.rowcount == 0:
        return fail("找不到這筆購物車商品", 404)
    return success({"message": "商品已刪除"})


@app.route("/submit_order", methods=["POST"])
def submit_order():
    return create_order_from_payload(request.get_json(silent=True) or {})


@app.route("/api/orders", methods=["POST"])
def create_order_api():
    return create_order_from_payload(request.get_json(silent=True) or {})


def create_order_from_payload(data: dict[str, Any]):
    frontend_items = data.get("items", [])
    try:
        cart_code = clean_required(data.get("cart_code"), "cart_code", 80)
        customer_name = clean_required(data.get("customer_name"), "顧客姓名", 40)
        phone = clean_required(data.get("phone"), "電話", 30)
        pickup_time = clean_required(data.get("pickup_time"), "取餐時間", 30)
        note = clean_optional(data.get("note"), 200)
    except ValueError as exc:
        return fail(str(exc))
    db = get_db()
    try:
        db.execute("BEGIN IMMEDIATE")  # 用交易把主檔、明細、清空購物車綁在一起，避免只成功一半
        cart_rows = db.execute(
            """
            SELECT id, product_id, product_name, price, quantity, options_text, option_ids, price * quantity AS subtotal
            FROM cart_items
            WHERE cart_code = ?
            ORDER BY id ASC
            """,
            (cart_code,),
        ).fetchall()
        if not cart_rows:
            db.rollback()
            return fail("購物車是空的，無法送出訂單")
        items = [row_to_dict(row) for row in cart_rows]
        if frontend_items and len(frontend_items) != len(items):
            db.execute("ROLLBACK")
            return fail("購物車資料已變動，請重新確認後再送出")
        total_amount = sum(item["subtotal"] for item in items)
        current_time = now_text()
        cursor = db.execute(
            """
            INSERT INTO orders (status, total_amount, item_count, customer_name, phone, pickup_time, note, created_at, updated_at)
            VALUES ('pending', ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (total_amount, len(items), customer_name, phone, pickup_time, note, current_time, current_time),
        )
        order_id = cursor.lastrowid
        for item in items:
            db.execute(
                """
                INSERT INTO order_items (order_id, product_id, product_name, price, quantity, options_text, option_ids, subtotal)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (order_id, item["product_id"], item["product_name"], item["price"], item["quantity"], item["options_text"], item["option_ids"], item["subtotal"]),
            )
        db.execute("DELETE FROM cart_items WHERE cart_code = ?", (cart_code,))  # 訂單成立後就把這台裝置的購物車清掉，避免重複送單
        db.commit()
    except Exception:
        db.rollback()
        raise
    return success({"message": "訂單已建立", "order_id": order_id, "redirect_url": url_for("order_success_page", order_id=order_id)})


@app.route("/orders")
def orders_json():
    return success({"orders": get_all_orders()})


@app.route("/api/admin/orders/<int:order_id>/status", methods=["POST"])
def update_order_status(order_id: int):
    data = request.get_json(silent=True) or {}
    new_status = str(data.get("status", "")).strip()
    if new_status not in STATUS_LABELS:
        return fail("不合法的訂單狀態")
    db = get_db()
    row = db.execute("SELECT id, status FROM orders WHERE id = ?", (order_id,)).fetchone()
    if row is None:
        return fail("找不到這張訂單", 404)
    current_status = row["status"]
    allowed = ALLOWED_TRANSITIONS.get(current_status, [])
    if new_status not in allowed:
        return fail(f"狀態不能從 {status_text(current_status)} 改成 {status_text(new_status)}")
    db.execute("UPDATE orders SET status = ?, updated_at = ? WHERE id = ?", (new_status, now_text(), order_id))
    db.commit()
    return success({"message": "訂單狀態已更新", "status": new_status, "status_text": status_text(new_status)})


@app.route("/api/admin/stats/today")
def today_stats_json():
    return success({"stats": get_today_stats()})


@app.route("/health")
def health():
    return success({"message": "ok"})


def get_active_products() -> list[dict[str, Any]]:
    db = get_db()
    rows = db.execute(
        """
        SELECT id, name, description, image_filename, base_price, sort_order
        FROM products
        WHERE is_active = 1
        ORDER BY sort_order ASC, id ASC
        """
    ).fetchall()
    return [row_to_dict(row) for row in rows]


def get_product_or_404(product_id: int) -> dict[str, Any]:
    db = get_db()
    row = db.execute(
        """
        SELECT id, name, description, image_filename, base_price, sort_order
        FROM products
        WHERE id = ? AND is_active = 1
        """,
        (product_id,),
    ).fetchone()
    if row is None:
        abort(404)
    return row_to_dict(row)


def get_option_groups(product_id: int) -> list[dict[str, Any]]:
    db = get_db()
    rows = db.execute(
        """
        SELECT id, option_group, option_name, extra_price, sort_order
        FROM product_options
        WHERE product_id = ? AND is_active = 1
        ORDER BY sort_order ASC, id ASC
        """,
        (product_id,),
    ).fetchall()
    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        item = row_to_dict(row)
        group_name = item["option_group"]
        if group_name not in grouped:
            grouped[group_name] = {"group_name": group_name, "options": []}
        grouped[group_name]["options"].append(item)
    return list(grouped.values())


def build_priced_item(product_id: int, option_ids: list[int]) -> dict[str, Any]:
    db = get_db()
    product_row = db.execute(
        """
        SELECT id, name, base_price
        FROM products
        WHERE id = ? AND is_active = 1
        """,
        (product_id,),
    ).fetchone()
    if product_row is None:
        raise ValueError("找不到商品或商品已下架")
    group_rows = db.execute(
        """
        SELECT option_group
        FROM product_options
        WHERE product_id = ? AND is_active = 1
        GROUP BY option_group
        ORDER BY MIN(sort_order) ASC
        """,
        (product_id,),
    ).fetchall()
    required_groups = [row["option_group"] for row in group_rows]
    option_rows: list[sqlite3.Row] = []
    if option_ids:
        placeholders = ",".join("?" for _ in option_ids)
        option_rows = db.execute(
            f"""
            SELECT id, option_group, option_name, extra_price, sort_order
            FROM product_options
            WHERE product_id = ? AND is_active = 1 AND id IN ({placeholders})
            ORDER BY sort_order ASC, id ASC
            """,
            [product_id, *option_ids],
        ).fetchall()
    if len(option_rows) != len(option_ids):
        raise ValueError("有選項不存在，或不屬於這個商品")
    selected_groups = [row["option_group"] for row in option_rows]
    if len(selected_groups) != len(set(selected_groups)):
        raise ValueError("每個選項群組只能選一個")
    if set(selected_groups) != set(required_groups):
        raise ValueError("請完整選擇商品選項")
    base_price = int(product_row["base_price"])
    option_total = sum(int(row["extra_price"]) for row in option_rows)
    unit_price = base_price + option_total  # 價格還是以後端重算為準，避免前端自己改數字
    options_text = "、".join(f"{row['option_group']}：{row['option_name']}" for row in option_rows)
    sorted_option_ids = [int(row["id"]) for row in option_rows]
    return {"product_id": product_id, "product_name": product_row["name"], "base_price": base_price, "option_total": option_total, "price": unit_price, "options_text": options_text, "option_ids": sorted_option_ids}


def load_cart_items(cart_code: str) -> list[dict[str, Any]]:
    db = get_db()
    rows = db.execute(
        """
        SELECT id, product_id, product_name, price, quantity, options_text AS options, option_ids, price * quantity AS subtotal
        FROM cart_items
        WHERE cart_code = ?
        ORDER BY id ASC
        """,
        (cart_code,),
    ).fetchall()
    return [row_to_dict(row) for row in rows]


def get_order_by_id(order_id: int) -> dict[str, Any] | None:
    db = get_db()
    row = db.execute(
        """
        SELECT id, status, total_amount, item_count, customer_name, phone, pickup_time, note, created_at, updated_at
        FROM orders
        WHERE id = ?
        """,
        (order_id,),
    ).fetchone()
    return row_to_dict(row) if row else None


def get_order_items(order_id: int) -> list[dict[str, Any]]:
    db = get_db()
    rows = db.execute(
        """
        SELECT id, product_id, product_name, price, quantity, options_text AS options, option_ids, subtotal
        FROM order_items
        WHERE order_id = ?
        ORDER BY id ASC
        """,
        (order_id,),
    ).fetchall()
    return [row_to_dict(row) for row in rows]


def get_all_orders(status_filter: str | None = None) -> list[dict[str, Any]]:
    db = get_db()
    if status_filter:
        order_rows = db.execute(
            """
            SELECT id, status, total_amount, item_count, customer_name, phone, pickup_time, note, created_at, updated_at
            FROM orders
            WHERE status = ?
            ORDER BY id DESC
            """,
            (status_filter,),
        ).fetchall()
    else:
        order_rows = db.execute(
            """
            SELECT id, status, total_amount, item_count, customer_name, phone, pickup_time, note, created_at, updated_at
            FROM orders
            ORDER BY id DESC
            """
        ).fetchall()
    orders: list[dict[str, Any]] = []
    for order_row in order_rows:
        order = enrich_order(row_to_dict(order_row))
        order["items"] = get_order_items(order["id"])
        orders.append(order)
    return orders


def get_today_stats() -> dict[str, Any]:
    db = get_db()
    today_prefix = now_text()[:10] + "%"
    summary = db.execute(
        """
        SELECT COUNT(*) AS order_count, COALESCE(SUM(total_amount), 0) AS revenue
        FROM orders
        WHERE created_at LIKE ? AND status != 'cancelled'
        """,
        (today_prefix,),
    ).fetchone()
    status_rows = db.execute(
        """
        SELECT status, COUNT(*) AS count
        FROM orders
        WHERE created_at LIKE ?
        GROUP BY status
        """,
        (today_prefix,),
    ).fetchall()
    status_counts = {key: 0 for key in STATUS_LABELS}
    for row in status_rows:
        status_counts[row["status"]] = row["count"]
    return {"date": now_text()[:10], "order_count": summary["order_count"], "revenue": summary["revenue"], "status_counts": status_counts, "status_labels": STATUS_LABELS}


with app.app_context():
    init_db()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
