# <!DOCTYPE html>
# <html lang="zh-Hant">
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <title>餐點詳情模板</title>
#     <style>
#         /* [UI 配置區] - 這裡存放固定外觀，後續擴充樣式請寫在 style.css */
#         body { font-family: "Microsoft JhengHei", sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; display: flex; justify-content: center; }
#         .mobile-container { width: 100%; max-width: 450px; min-height: 100vh; background-color: white; position: relative; box-shadow: 0 0 20px rgba(0,0,0,0.1); padding-bottom: 80px; }
        
#         /* 圖片容器：後續若為彈窗模式，寬度可改為 90% 並加圓角 */
#         .image-box { width: 100%; height: 300px; background-color: black; display: flex; align-items: center; justify-content: center; overflow: hidden; }
#         .image-box img { width: 100%; height: 100%; object-fit: cover; }

#         .description { padding: 20px; color: rgba(0, 0, 0, 0.5); font-size: 15px; border-bottom: 8px solid #f5f5f5; }
#         .option-title { background-color: orange; color: white; padding: 10px 20px; font-weight: bold; }
#         .option-item { display: flex; align-items: center; padding: 15px 20px; border-bottom: 1px solid #eee; cursor: pointer; }
        
#         /* 底部操作區 */
#         .footer-bar { position: absolute; bottom: 0; width: 100%; height: 75px; background: white; border-top: 1px solid #eee; display: flex; align-items: center; justify-content: space-between; padding: 0 20px; box-sizing: border-box; }
#         .price-section { font-size: 22px; font-weight: bold; color: #ff5722; }
#     </style>
# </head>
# <body>

#     <div class="mobile-container">
#         <button class="back-btn" onclick="history.back()">〈</button>

#         <div class="image-box">
#             <img src="{{ url_for('static', filename='images/default.jpg') }}" alt="餐點圖片">
#         </div>

#         <div class="description">
#             <h2 id="food-name" style="color:#333; margin-top:0;">餐點名稱</h2>
#             <p id="food-desc">這裡顯示餐點的詳細介紹文字 (預設透明度 50%)</p>
#         </div>

#         <div class="option-title">溫度 (單選)</div>
#         <label class="option-item"><input type="radio" name="temp" value="cold" checked> 冰的</label>
#         <label class="option-item"><input type="radio" name="temp" value="hot"> 熱的</label>

#         <div class="option-title">甜度 (單選)</div>
#         <label class="option-item"><input type="radio" name="sugar" value="10" checked> 全糖</label>
#         <label class="option-item"><input type="radio" name="sugar" value="5"> 半糖</label>
#         <label class="option-item"><input type="radio" name="sugar" value="0"> 無糖</label>

#         <div class="footer-bar">
#             <div class="price-section">$<span id="total-price">50</span></div>
            
#             <div class="counter-group">
#                 <button onclick="updateQty(-1)">-</button>
#                 <span id="quantity">1</span>
#                 <button onclick="updateQty(1)">+</button>
#                 <button class="confirm-btn" onclick="submitOrder()">確認添加</button>
#             </div>
#         </div>
#     </div>

#     <script>
#         /**
#          * [開發備忘錄]
#          * 1. 變數 unitPrice 之後應由 Flask 從資料庫傳入：const unitPrice = {{ product.price }};
#          * 2. submitOrder 函數需實作：抓取所有選中的 Radio Value 並存入購物車物件。
#          */
#         let currentQty = 1;
#         const unitPrice = 50; 

#         // 數量增減邏輯
#         function updateQty(change) {
#             currentQty += change;
#             if (currentQty < 1) currentQty = 1; // 最小數量限制
#             document.getElementById('quantity').innerText = currentQty;
#             document.getElementById('total-price').innerText = currentQty * unitPrice;
#         }

#         // 預留：提交訂單邏輯
#         function submitOrder() {
#             const selectedTemp = document.querySelector('input[name="temp"]:checked').value;
#             const selectedSugar = document.querySelector('input[name="sugar"]:checked').value;
            
#             console.log("提交內容：", {
#                 name: "餐點名稱",
#                 qty: currentQty,
#                 temp: selectedTemp,
#                 sugar: selectedSugar,
#                 total: currentQty * unitPrice
#             });
#             alert('已加入購物車！');
#         }
#     </script>
# </body>
# </html>

# -------------------------------------------------------

# module.py - 點餐系統開發規範與模板參數定義

# [資料對接規範]
# 前端 HTML 的 id 或 name 屬性應與此處 Key 值保持一致
FOOD_TEMPLATE_CONFIG = {
    "basic_info": {
        "name_id": "food-name",        # 餐點名稱顯示區 ID
        "desc_id": "food-desc",        # 詳細介紹顯示區 ID
        "price_id": "total-price"      # 總金額顯示區 ID
    },
    "selectors": {
        "temp_group": "temp",          # 溫度單選群組 name
        "sugar_group": "sugar",        # 甜度單選群組 name
        "qty_id": "quantity"           # 數量顯示區 ID
    },
    "styles": {
        "primary_orange": "orange",    # 標題背景色
        "text_opacity": "0.5",         # 介紹文字透明度
        "mobile_max_width": "450px"    # 手機模式最大寬度
    }
}

# [未來擴充建議]
# 若餐點改為彈窗顯示，前端應呼叫：showProductModal(productId)
# 若餐點為獨立頁面，後端路徑應為：/product/<int:product_id>