import sqlite3
from datetime import datetime

class second_group_order_db:
    #初始化資料庫
    def __init__(self,db_name='second_group_order.db'):
        self.db_name=db_name
        
    #串接sqlite3
    def connect(self):
        conn=sqlite3.connect(self.db_name)
        conn.row_factory=sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        return conn
    
    def now_text(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    #建立資料表membership
    def create_table(self):
        conn=self.connect()
        cursor=conn.cursor()
        sql='''
            CREATE TABLE IF NOT EXISTS MEMBERSHIP(
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                USER TEXT UNIQUE,
                PASSWORD TEXT,
                NAME TEXT,
                EMAIL TEXT,
                IS_VERIFIED INTEGER DEFAULT 0);
            
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
        '''        
        cursor.executescript(sql)
        
        #-----------------------------------------
        self.ensure_schema_upgrades(conn)
        self.seed_products(conn)
        #-----------------------------------------
        
        conn.commit()
        conn.close()
        
    #------------------------------------------------------------------------------------------------------------------------------------------------------------
    def ensure_schema_upgrades(self,conn):
        product_columns = conn.execute("PRAGMA table_info(products)").fetchall()
        column_names = [row[1] for row in product_columns]
        if "image_filename" not in column_names:
            conn.execute("ALTER TABLE products ADD COLUMN image_filename TEXT NOT NULL DEFAULT 'default.jpg'")

    def seed_products(self,conn):
        count = conn.execute("SELECT COUNT(*) AS count FROM products").fetchone()[0]
        if count > 0:
            return
        current_time = self.now_text()
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
            cursor = conn.execute(
                """
                INSERT INTO products (name, description, image_filename, base_price, is_active, sort_order, created_at, updated_at)
                VALUES (?, ?, ?, ?, 1, ?, ?, ?)
                """,
                (product["name"], product["description"], product["image_filename"], product["base_price"], product["sort_order"], current_time, current_time),
            )
            product_id = cursor.lastrowid
            self.add_options_for_food(conn, product_id)

    def add_options_for_food(self,conn,product_id):
        options = [
            (product_id, "辣度", "不辣", 0, 1),
            (product_id, "辣度", "小辣", 0, 2),
            (product_id, "辣度", "中辣", 0, 3),
            (product_id, "辣度", "大辣", 0, 4),
            (product_id, "加飯", "不要", 0, 5),
            (product_id, "加飯", "加飯", 10, 6),
        ]
        conn.executemany(
            """
            INSERT INTO product_options (product_id, option_group, option_name, extra_price, is_active, sort_order)
            VALUES (?, ?, ?, ?, 1, ?)
            """,
            options,
        )

    def add_options_for_drink(self,conn,product_id) -> None:
        options = [
            (product_id, "溫度", "冰", 0, 1),
            (product_id, "溫度", "熱", 0, 2),
            (product_id, "甜度", "全糖", 0, 3),
            (product_id, "甜度", "少糖", 0, 4),
            (product_id, "甜度", "半糖", 0, 5),
            (product_id, "甜度", "微糖", 0, 6),
            (product_id, "甜度", "無糖", 0, 7),
        ]
        conn.executemany(
            """
            INSERT INTO product_options (product_id, option_group, option_name, extra_price, is_active, sort_order)
            VALUES (?, ?, ?, ?, 1, ?)
            """,
            options,
        )
    #--------------------------------------------------------------------------------------------------------------------
   
    #檢查用戶是否註冊
    def user_exists(self,user):
        conn=self.connect()
        cursor=conn.cursor()
        sql='''
        SELECT 1 FROM MEMBERSHIP WHERE USER=?
        '''
        cursor.execute(sql,(user,))
        data=cursor.fetchone()
        conn.close()
        return data is not None
    
    #新增資料
    def add_user(self,user,password,name,email):
        conn=self.connect()
        cursor=conn.cursor()
        try:
            sql='''
            INSERT INTO MEMBERSHIP(USER,PASSWORD,NAME,EMAIL,IS_VERIFIED)
            VALUES(?,?,?,?,1)
            '''
            cursor.execute(sql,(user,password,name,email))
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()

    #檢查登入用戶
    def check_user(self,user,password):
        conn=self.connect()
        cursor=conn.cursor()
        sql='''
            SELECT * FROM MEMBERSHIP 
            WHERE USER=? AND PASSWORD=?
        '''
        cursor.execute(sql,(user,password))
        data=cursor.fetchone()
        conn.close()
        return data