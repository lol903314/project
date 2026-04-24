# module.py - 資料紀錄

# 1. 店面基本資訊與圖片配置
# ==========================================
STORE_CONFIG = {
    "name": "二組熱炒",
    "rating": "4.9 (500+)",
    "delivery_info": "20-30 分鐘 | 運費30$",
    "promotion": "滿 $1000 打 85 折 ",
    "images": {
        "logo": "images/Shop-image/store_logo.jpg",    
        "banner": "images/Shop-image/store_logo.jpg"
    }
}

# ==========================================

# 2. 商品清單 串接 SQLite，資料庫查詢取代此處
PRODUCT_LIST = [
    {
        "id": 1,
        "name": "九層塔炒海瓜子",
        "price": 180,
        "img": "images/Product-image/Stir-fried-Clams-with-Basil.jpg",
        "desc": "塔香濃郁，極致鮮甜海味",
        "options": [
            {"title": "辣度", "name": "spicy", "choices": ["不辣", "小辣", "中辣", "大辣"]},
            {"title": "九層塔份量", "name": "basil", "choices": ["正常", "加九層塔", "不要九層塔"]},
            {"title": "口味鹹度", "name": "salt", "choices": ["正常", "淡", "鹹"]}
        ]
    },
    {
        "id": 2,
        "name": "九層塔煎蛋",
        "price": 120,
        "img": "images/Product-image/Basil-Omelet.jpg",
        "desc": "金黃酥嫩，經典塔香層次。",
        "options": [
            {"title": "熟度選擇", "name": "done", "choices": ["標準", "全熟"]},
            {"title": "蔥/塔份量", "name": "veg", "choices": ["正常", "加重九層塔", "不要九層塔"]},
            {"title": "醬料", "name": "sauce", "choices": ["不加醬", "醬油膏", "甜辣醬"]}
        ]
    },
    {
        "id": 3,
        "name": "五更腸旺",
        "price": 230,
        "img": "images/Product-image/Wugeng-Changwang.jpg",
        "desc": "香辣滑嫩，下飯必備經典。",
        "options": [
            {"title": "辣度(必選)", "name": "spicy", "choices": ["微辣", "小辣", "中辣", "大辣"]},
            {"title": "加料區", "name": "add", "choices": ["標準", "加倍鴨血", "加倍大腸"]},
        ]
    },
    {
        "id": 4,
        "name": "牛肉炒飯",
        "price": 180,
        "img": "images/Product-image/beef-friedrice.jpg",
        "desc": "鑊氣十足，鮮嫩牛肉香。",
        "options": [
            {"title": "客製", "name": "custom", "choices": ["不要蔥花", "不要洋蔥", "加辣炒"]},
            {"title": "配菜選擇", "name": "egg", "choices": ["標準", "多一顆蛋"]}
        ]
    },
    {
        "id": 5,
        "name": "白灼蝦",
        "price": 220,
        "img": "images/Product-image/Poached-Shrimp.jpg",
        "desc": "清燙原味，鎖住極致鮮甜。",
        "options": [
            {"title": "沾醬選擇", "name": "sauce", "choices": ["哇沙米醬油", "薑醋汁", "特製辣醬"]},
            {"title": "熟度", "name": "done", "choices": ["剛好", "全熟"]},
        ]
    },
    {
        "id": 6,
        "name": "豆酥鱈魚",
        "price": 200,
        "img": "images/Product-image/Crispy-Bean.jpg",
        "desc": "酥脆豆香，襯托鱈魚鮮嫩。",
        "options": [
            {"title": "豆酥份量", "name": "bean", "choices": ["正常", "加豆酥", "豆酥分開放"]},
            {"title": "辣度", "name": "spicy", "choices": ["不辣", "小辣", "中辣"]},
        ]
    },
    {
        "id": 7,
        "name": "空心菜炒牛肉",
        "price": 180,
        "img": "images/Product-image/Beef-heart.jpg",
        "desc": "清脆空心菜，拌炒嫩牛肉。",
        "options": [
            {"title": "辣度", "name": "spicy", "choices": ["不辣", "小辣", "中辣", "大辣"]},
            {"title": "口味", "name": "flavor", "choices": ["沙茶", "蒜味清炒", "辣炒"]},
            {"title": "肉量調整", "name": "meat", "choices": ["正常", "加肉"]}
        ]
    },
    {
        "id": 8,
        "name": "空心菜炒羊肉",
        "price": 170,
        "img": "images/Product-image/Lamb-heart.jpg",
        "desc": "塔香羊肉，鮮嫩爽脆合一。",
        "options": [
            {"title": "辣度", "name": "spicy", "choices": ["不辣", "小辣", "中辣", "大辣"]},
            {"title": "羶味處理", "name": "smell", "choices": ["正常", "多薑絲", "加沙茶"]},
        ]
    },
    {
        "id": 9,
        "name": "芹菜炒花枝",
        "price": 180,
        "img": "images/Product-image/Squid-celery.jpg",
        "desc": "芹菜清脆，花枝鮮Ｑ彈牙。",
        "options": [
            {"title": "辣度", "name": "spicy", "choices": ["不辣", "小辣", "中辣"]},
            {"title": "客製化", "name": "custom", "choices": ["正常", "不要芹菜", "不要薑片"]}
        ]
    },
    {
        "id": 10,
        "name": "芹菜炒蝦仁",
        "price": 180,
        "img": "images/Product-image/Shrimp-celery.jpg",
        "desc": "香辣滑嫩，下飯必備經典。",
        "options": [
            {"title": "辣度", "name": "spicy", "choices": ["不辣", "小辣", "中辣"]},
            {"title": "加料", "name": "add", "choices": ["不加", "加木耳", "加甜豆"]}
        ]
    },
    {
        "id": 11,
        "name": "金沙蝦球",
        "price": 220,
        "img": "images/Product-image/gold-shrimp.jpg",
        "desc": "芹菜清脆，花枝鮮Ｑ彈牙。",
        "options": [
            {"title": "金沙份量", "name": "egg", "choices": ["正常", "重蛋黃", "輕蛋黃"]},
            {"title": "配菜", "name": "side", "choices": ["彩色蝦餅", "鳳梨片", "不加配菜"]},
            {"title": "口感", "name": "feel", "choices": ["標準", "去美乃滋"]}
        ]
    },
    
    {
        "id": 12,
        "name": "涼拌蘆筍",
        "price": 180,
        "img": "images/Product-image/Asparagus-Salad.jpg",
        "desc": "清爽脆口，夏季解膩首選。",
        "options": [
            {"title": "醬料(必選)", "name": "sauce", "choices": ["美乃滋", "胡麻醬", "和風油醋"]},
            {"title": "花生粉", "name": "powder", "choices": ["加", "不加"]},
        ]
    },
    {
        "id": 13,
        "name": "青椒肉絲",
        "price": 180,
        "img": "images/Product-image/Peppers-Pork.jpg",
        "desc": "青椒脆爽，肉絲鮮嫩滑口。",
        "options": [
            {"title": "辣度", "name": "spicy", "choices": ["不辣", "小辣", "中辣"]},
        ]
    },
   
    {
        "id": 14,
        "name": "清炒高麗菜",
        "price": 180,
        "img": "images/Product-image/fried-Cabbage.jpg",
        "desc": "清脆鮮甜，道地家常原味。",
        "options": [
            {"title": "口感", "name": "texture", "choices": ["脆一點", "軟一點"]},
            {"title": "辣度", "name": "spicy", "choices": ["不辣", "小辣", "中辣"]}
        ]
    },
    {
        "id": 15,
        "name": "滑蛋蝦仁",
        "price": 200,
        "img": "images/Product-image/Shrimp-egg.jpg",
        "desc": "蛋香滑嫩，鮮美彈牙蝦仁。",
        "options": [
            {"title": "蔥花量", "name": "green", "choices": ["正常", "多蔥", "不要蔥"]},
            {"title": "口味", "name": "flavor", "choices": ["原味", "加白胡椒"]}
        ]
    },
    {
        "id": 16,
        "name": "蔥爆牛肉",
        "price": 230,
        "img": "images/Product-image/fried-Beef.jpg",
        "desc": "蔥香噴鼻，牛肉滑嫩入味。",
        "options": [
            {"title": "辣度", "name": "spicy", "choices": ["不辣", "小辣", "中辣", "大辣"]},
            {"title": "口味重點", "name": "style", "choices": ["黑胡椒", "沙茶", "醬油"]}
        ]
    },
    {
        "id": 17,
        "name": "蔥爆羊肉",
        "price": 220,
        "img": "images/Product-image/fried-Lamb.jpg",
        "desc": "蔥香四溢，羊肉鮮嫩爽口。",
        "options": [
            {"title": "辣度", "name": "spicy", "choices": ["不辣", "小辣", "中辣", "大辣"]},
        ]
    },
    {
        "id": 18,
        "name": "蝦仁炒飯",
        "price": 180,
        "img": "images/Product-image/Shrimp-Fried-Rice.jpg",
        "desc": "粒粒分明，鮮美彈牙蝦仁。",
        "options": [
            {"title": "米飯口感", "name": "rice", "choices": ["標準", "軟一點"]},
            {"title": "蔥花/蛋", "name": "custom", "choices": ["都要", "不要蔥", "不要蛋"]},
            {"title": "辣度", "name": "spicy", "choices": ["不辣", "小辣", "中辣"]}
        ]
    },
    {
        "id": 19,
        "name": "糖醋排骨",
        "price": 200,
        "img": "images/Product-image/Sweet&Sour-Pork.jpg",
        "desc": "酸甜入味，酥嫩骨香誘人。",
        "options": [
            {"title": "酸甜比例", "name": "taste", "choices": ["黃金比例", "偏酸", "偏甜"]},
            {"title": "配料", "name": "side", "choices": ["有鳳梨/青椒", "只要排骨"]},
        ]
    },
    {
        "id": 20,
        "name": "糖醋魚片",
        "price": 220,
        "img": "images/Product-image/Sweet&Sour-Fish.jpg",
        "desc": "酸甜酥嫩，無刺鮮美魚片。",
        "options": [
            {"title": "魚片脆度", "name": "crispy", "choices": ["標準", "酥一點"]},
            {"title": "酸甜比例", "name": "taste", "choices": ["黃金比例", "偏酸", "偏甜"]},
        ]
    },
    {
        "id": 21,
        "name": "薑絲大腸",
        "price": 180,
        "img": "images/Product-image/Ginger Strips.jpg",
        "desc": "薑香酸爽，大腸Ｑ彈勁道。",
        "options": [
            {"title": "酸度等級", "name": "sour", "choices": ["標準", "適中", "微酸"]},
            {"title": "大腸口感", "name": "chew", "choices": ["標準", "軟一點"]},
            {"title": "辣度", "name": "spicy", "choices": ["不辣", "小辣", "中辣"]}
        ]
    },
    {
        "id": 22,
        "name": "蠔油牛肉",
        "price": 230,
        "img": "images/Product-image/Beef-Oyster.jpg",
        "desc": "蠔油鮮香，牛肉滑嫩鹹甜。",
        "options": [
            {"title": "辣度", "name": "spicy", "choices": ["不辣", "小辣", "中辣"]},
            {"title": "配菜選擇", "name": "veg", "choices": ["附芥藍菜", "附空心菜", "純牛肉"]},
            {"title": "口味", "name": "flavor", "choices": ["標準", "淡", "鹹"]}
        ]
    },
    {
        "id": 23,
        "name": "鐵板豆腐",
        "price": 180,
        "img": "images/Product-image/Sizzling-Tofu.jpg",
        "desc": "焦香誘人，豆腐滑嫩入味。",
        "options": [
            {"title": "豆腐類型", "name": "type", "choices": ["雞蛋豆腐", "板豆腐"]},
            {"title": "辣度", "name": "spicy", "choices": ["不辣", "小辣", "中辣"]},
            {"title": "鐵板配料", "name": "side", "choices": ["有奶油香", "多放洋蔥", "不要黑胡椒"]}
        ]
    },
    
]

# ==========================================
# 3. 前端 UI CSS 樣式
# ==========================================
# 確保統一性
UI_STYLE_GUIDE = {
    "colors": {
        "primary": "#ff5722",         # 品牌橘色 (確認鍵、價格)
        "secondary": "orange",        # 選項標題背景色
        "background": "#f5f5f5",      # 背景淺灰
        "text_main": "#333333",       # 文字顏色
        "text_muted": "rgba(0,0,0,0.5)" # 說明文字顏色 (50% 透明度)
    },
    "font_size": {
        "title": "20px",              # 選項區標題
        "body": "15px",               # 介紹文字
        "price": "22px"               # 顯示金額
    },
    "layout": {
        "mobile_max_width": "450px",  # 手機模擬容器寬度
        "product_grid_gap": "15px"    # 目錄頁商品間距
    }
}

# ==========================================
# 4. 前後端命名對接規範 (ID/Name)
# ==========================================
ID_NAMING_CONVENTION = {
    "temp_group": "temp",             # 溫度單選群組名稱
    "sugar_group": "sugar",           # 甜度單選群組名稱
    "qty_display": "quantity",        # 數量顯示區 ID
    "total_price_display": "total-price" # 總價顯示區 ID
}