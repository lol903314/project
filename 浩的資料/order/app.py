import os
print("目前執行路徑:", os.getcwd()) # 這行會印在 Console，看是不是在你的 Order 資料夾
from flask import Flask, render_template
import module  # 匯入你的規範文件

app = Flask(__name__)

@app.route('/')
def test_page():
    # 將單價與規範參數傳入模板
    return render_template('test.html', 
                           unit_price=50, 
                           config=module.FOOD_TEMPLATE_CONFIG)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)