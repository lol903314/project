import os

# 檢查當前路徑
print(f"目前執行路徑: {os.getcwd()}")

# 檢查 static 內容
static_path = os.path.join(os.getcwd(), 'static', 'images', 'products')
if os.path.exists(static_path):
    print("✅ 找到 products 資料夾")
    files = os.listdir(static_path)
    print(f"資料夾內的檔案列表: {files}")
else:
    print("❌ 找不到路徑: ", static_path)

# 測試其中一個檔案
target = "Basil-Omelet.jpg"
if target in os.listdir(static_path) if os.path.exists(static_path) else []:
    print(f"✅ 檔案 {target} 確實存在")
else:
    print(f"❌ 找不到檔案 {target}")