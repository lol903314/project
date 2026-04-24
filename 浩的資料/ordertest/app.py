import os
from flask import Flask, render_template, url_for
import module

# 取得目前檔案所在的路徑
base_dir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__, 
            template_folder=os.path.join(base_dir, 'templates'),
            static_folder=os.path.join(base_dir, 'static'))

@app.route('/catalog')
def catalog():
    return render_template('catalog.html', 
                           store=module.STORE_CONFIG, 
                           products=module.PRODUCT_LIST)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = next((p for p in module.PRODUCT_LIST if p['id'] == product_id), None)
    
    if product:
        # 將資料命名為 'product' 傳給 HTML
        return render_template('test.html', product=product)
    return "找不到這道菜喔！", 404
    

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)