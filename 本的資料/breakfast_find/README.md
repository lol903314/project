# 熱炒點餐系統 


這一版已經把商品資料切換成熱炒商品，商品詳情頁也整理成比較適合手機操作的版本。

## 這版完成的功能

- 商品詳情頁改成手機版大圖模板
- 商品圖片改用 `static/images/` 管理
- 商品資料已切換成 23 筆熱炒商品
- 熱炒商品圖片已放到 `static/images/`
- 加入購物車流程保留後端計價
- 前端仍然只送 `product_id`、`quantity`、`option_ids`
- 後端仍然自己查商品價格與選項價格
- 原本購物車、結帳、訂單成功、訂單查詢、後台訂單管理都保留

## 執行方式

```bash
pip install -r requirements.txt
python app.py
```

啟動後開啟：

```text
http://127.0.0.1:5000/product
```

## 主要頁面

```text
/product              商品列表
/product/5            熱炒商品詳情頁範例
/cart                 購物車
/checkout             結帳
/order_list           訂單查詢
/admin/orders         店家後台
/orders               訂單 JSON
/health               後端健康檢查
```


## 圖片位置

商品圖片放在：

```text
static/images/
```

目前已經放了這些檔案：

```text
九層塔炒海瓜子.jpg
牛肉炒飯.jpg
白灼蝦.jpg
糖醋排骨.jpg
鐵板豆腐.jpg
default.jpg
```

之後如果要換圖片，可以把檔名對應好後放進 `static/images/`。
