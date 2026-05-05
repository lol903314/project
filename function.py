import sqlite3
from typing import Any
from datetime import datetime, timedelta, timezone
from model import second_group_order_db
from flask import abort,jsonify,url_for

db=second_group_order_db()
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

def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)

def now_text() -> str:
    return datetime.now(TAIPEI_TZ).strftime("%Y-%m-%d %H:%M:%S")

#把商品頁要求的資料從資料庫products全部取出
def get_active_products() -> list[dict[str, Any]]:
    conn=db.connect()
    cursor=conn.cursor()
    rows = cursor.execute(
        """
        SELECT id, name, description, image_filename, base_price, sort_order
        FROM products
        WHERE is_active = 1
        ORDER BY sort_order ASC, id ASC
        """
    ).fetchall()
    return [row_to_dict(row) for row in rows]

def get_product_or_404(product_id: int) -> dict[str, Any]:
    conn=db.connect()
    cursor=conn.cursor()
    row = cursor.execute(
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
    conn=db.connect()
    cursor=conn.cursor()
    rows = cursor.execute(
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

def load_cart_items(cart_code: str) -> list[dict[str, Any]]:
    conn=db.connect()
    cursor=conn.cursor()
    rows = cursor.execute(
        """
        SELECT id, product_id, product_name, price, quantity, options_text AS options, option_ids, price * quantity AS subtotal
        FROM cart_items
        WHERE cart_code = ?
        ORDER BY id ASC
        """,
        (cart_code,),
    ).fetchall()
    conn.close()
    return [row_to_dict(row) for row in rows]

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
    conn=db.connect()
    cursor=conn.cursor()
    try:
        cursor.execute("BEGIN IMMEDIATE")  # 用交易把主檔、明細、清空購物車綁在一起，避免只成功一半
        cart_rows = cursor.execute(
            """
            SELECT id, product_id, product_name, price, quantity, options_text, option_ids, price * quantity AS subtotal
            FROM cart_items
            WHERE cart_code = ?
            ORDER BY id ASC
            """,
            (cart_code,),
        ).fetchall()
        if not cart_rows:
            cursor.rollback()
            return fail("購物車是空的，無法送出訂單")
        items = [row_to_dict(row) for row in cart_rows]
        if frontend_items and len(frontend_items) != len(items):
            cursor.execute("ROLLBACK")
            return fail("購物車資料已變動，請重新確認後再送出")
        total_amount = sum(item["subtotal"] for item in items)
        current_time = now_text()
        c = cursor.execute(
            """
            INSERT INTO orders (status, total_amount, item_count, customer_name, phone, pickup_time, note, created_at, updated_at)
            VALUES ('pending', ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (total_amount, len(items), customer_name, phone, pickup_time, note, current_time, current_time),
        )
        order_id = c.lastrowid
        for item in items:
            cursor.execute(
                """
                INSERT INTO order_items (order_id, product_id, product_name, price, quantity, options_text, option_ids, subtotal)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (order_id, item["product_id"], item["product_name"], item["price"], item["quantity"], item["options_text"], item["option_ids"], item["subtotal"]),
            )
        cursor.execute("DELETE FROM cart_items WHERE cart_code = ?", (cart_code,))  # 訂單成立後就把這台裝置的購物車清掉，避免重複送單
        
    except Exception:
        cursor.rollback()
        raise
    conn.commit()
    conn.close()
    return success({"message": "訂單已建立", "order_id": order_id, "redirect_url": url_for("order_success_page", order_id=order_id)})

def build_priced_item(product_id: int, option_ids: list[int]) -> dict[str, Any]:
    conn=db.connect()
    cursor=conn.cursor()
    product_row = cursor.execute(
        """
        SELECT id, name, base_price
        FROM products
        WHERE id = ? AND is_active = 1
        """,
        (product_id,),
    ).fetchone()
    if product_row is None:
        raise ValueError("找不到商品或商品已下架")
    group_rows = cursor.execute(
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
        option_rows = cursor.execute(
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
    conn.close()
    return {"product_id": product_id, "product_name": product_row["name"], "base_price": base_price, "option_total": option_total, "price": unit_price, "options_text": options_text, "option_ids": sorted_option_ids}

def get_order_by_id(order_id: int) -> dict[str, Any] | None:
    conn=db.connect()
    cursor=conn.cursor()
    row = cursor.execute(
        """
        SELECT id, status, total_amount, item_count, customer_name, phone, pickup_time, note, created_at, updated_at
        FROM orders
        WHERE id = ?
        """,
        (order_id,),
    ).fetchone()
    conn.close()
    return row_to_dict(row) if row else None

def get_order_items(order_id: int) -> list[dict[str, Any]]:
    conn=db.connect()
    cursor=conn.cursor()
    rows = cursor.execute(
        """
        SELECT id, product_id, product_name, price, quantity, options_text AS options, option_ids, subtotal
        FROM order_items
        WHERE order_id = ?
        ORDER BY id ASC
        """,
        (order_id,),
    ).fetchall()
    conn.close()
    return [row_to_dict(row) for row in rows]

def get_all_orders(status_filter: str | None = None) -> list[dict[str, Any]]:
    conn=db.connect()
    cursor=conn.cursor()
    if status_filter:
        order_rows = cursor.execute(
            """
            SELECT id, status, total_amount, item_count, customer_name, phone, pickup_time, note, created_at, updated_at
            FROM orders
            WHERE status = ?
            ORDER BY id DESC
            """,
            (status_filter,),
        ).fetchall()
    else:
        order_rows = cursor.execute(
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
    conn.close()
    return orders

def get_today_stats() -> dict[str, Any]:
    conn=db.connect()
    cursor=conn.cursor()
    today_prefix = now_text()[:10] + "%"
    summary = cursor.execute(
        """
        SELECT COUNT(*) AS order_count, COALESCE(SUM(total_amount), 0) AS revenue
        FROM orders
        WHERE created_at LIKE ? AND status != 'cancelled'
        """,
        (today_prefix,),
    ).fetchone()
    status_rows = cursor.execute(
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
    conn.close()
    return {"date": now_text()[:10], "order_count": summary["order_count"], "revenue": summary["revenue"], "status_counts": status_counts, "status_labels": STATUS_LABELS}