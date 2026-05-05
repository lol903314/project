import os#heroku
from flask import Flask,render_template,request,redirect,url_for,session,jsonify,abort
import random
from flask_mail import Mail,Message
from model import second_group_order_db
import function

db=second_group_order_db()
db.create_table()

app = Flask(__name__)
app.secret_key='lol'#session金鑰

#信箱驗證
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='trumpet903314@gmail.com',
    MAIL_PASSWORD='ajmn bqvf tfaj sgxt')
mail=Mail(app)

#----------------------------------------------
app.config["JSON_AS_ASCII"] = False
#----------------------------------------------
  
#首頁
@app.route('/')
def home():
    return render_template('home.html')

#訪客登入
@app.route('/guest')
def guest():
    session['user']='訪客'
    session['is_guest']=True
    return redirect(url_for("product_list_page"))

#註冊頁面
@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        user=request.form['user']
        password=request.form['password']
        name=request.form['name']
        email=request.form['email']
        if db.user_exists(user):
            return render_template('register.html',msg='帳號已存在')
        code=str(random.randint(100000,999999))
        
        session['temp_user']=user
        session['temp_password']=password
        session['temp_name']=name
        session['temp_email']=email
        session['verify_code']=code
        
        #寄信
        msg=Message('驗證碼',sender=app.config['MAIL_USERNAME'],recipients=[email])
        msg.body=f'你的驗證碼:{code}'
        mail.send(msg)
        return render_template('verify.html',msg='註冊需進行Email驗證，驗證完成才可繼續操作')    
    return render_template('register.html')

#檢查帳號是否註冊
@app.route('/check_user',methods=['POST'])
def check_user():
    user=request.json.get('user')
    return jsonify({'exists':db.user_exists(user)})

#驗證頁面
@app.route('/verify',methods=['GET','POST'])
def verify():
    if request.method=='POST':
        code=request.form['code']
        if code==session.get('verify_code'):
            db.add_user(session['temp_user'],session['temp_password'],session['temp_name'],session['temp_email'])
            return render_template('login.html',msg='驗證碼正確，請登入')
        else:
            return render_template('verify.html',msg='驗證碼錯誤')
    return render_template('verify.html') 

#登入頁面
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        user=request.form['user']
        password=request.form['password']
        
        if db.check_user(user,password):
            session['user']=user
            session['password']=password
            return redirect(url_for("product_list_page"))
        else:
            return render_template('login.html',msg='帳密錯誤')   
    return render_template('login.html')

#忘記密碼頁面
@app.route('/forgot_password',methods=['GET','POST'])
def forgot_password():
    if request.method=='POST':
        user=request.form['user']
        email=request.form['email']
        
        conn=db.connect()
        cursor=conn.cursor()
        sql='''
        SELECT * FROM MEMBERSHIP 
        WHERE USER=? AND EMAIL=?
        '''
        cursor.execute(sql,(user,email,))
        data=cursor.fetchone()
        conn.close()
        if not data:
            return render_template('forgot_password.html',msg='帳號或email錯誤')
        
        code=str(random.randint(100000,999999))
        session['reset_code']=code
        session['reset_user']=user
        
        msg=Message('重設密碼驗證碼',sender=app.config['MAIL_USERNAME'],recipients=[email])
        msg.body=f'你的驗證碼:{code}'
        mail.send(msg)
        return redirect(url_for('reset_password'))
    return render_template('forgot_password.html')

#驗證及重設密碼頁面
@app.route('/reset_password',methods=['GET','POST'])
def reset_password():    
    if request.method=='POST':
        code=request.form['code']
        new_password=request.form['password']
        
        if code==session['reset_code']:
            conn=db.connect()
            cursor=conn.cursor()
            sql='''
            UPDATE MEMBERSHIP
            SET PASSWORD=? 
            WHERE USER=?
            '''
            cursor.execute(sql,(new_password,session['reset_user']))
            conn.commit()
            conn.close()
            return render_template('login.html',msg='更新完成，請重新登入')
        else:
            return render_template('reset_password.html',msg='驗證碼錯誤')    
    return render_template('reset_password.html')
    
#登出頁面
@app.route('/logout')
def logout():
    #刪除登入狀態
    session.clear()
    return render_template('login.html',msg='已登出')

#會員資料頁面
@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    conn=db.connect()
    cursor=conn.cursor()
    sql='''
    SELECT USER,PASSWORD,NAME,EMAIL
    FROM MEMBERSHIP
    WHERE USER=?
    '''
    cursor.execute(sql,(session['user'],))
    data=cursor.fetchone()
    conn.close()
    if not data:
        return render_template('login.html',msg='找不到資料，請登入')
    
    user,password,name,email=data
    return render_template('profile.html',user=user,password=password,name=name,email=email)

#修改會員資料頁面
@app.route('/edit_profile',methods=['GET','POST'])
def edit_profile():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    conn=db.connect()
    cursor=conn.cursor()
    
    if request.method=='POST':
        password=request.form['password']
        name=request.form['name']
        email=request.form['email']
        sql='''
        UPDATE MEMBERSHIP
        SET PASSWORD=?, NAME=?, EMAIL=?
        WHERE USER=?
        '''
        cursor.execute(sql,(password,name,email,session['user'],))
        conn.commit()
        conn.close()
        return render_template('edit_profile.html',msg="更新成功")
    
    cursor.execute("SELECT PASSWORD,NAME,EMAIL FROM MEMBERSHIP WHERE USER=?",(session['user'],))
    data=cursor.fetchone()
    conn.close()
    return render_template('edit_profile.html',password=data[0],name=data[1],email=data[2])

#--------------------------------------------------------------------------------------------------------
#商品頁
@app.route("/products")
def product_list_page():
    if 'user' not in session:
        return redirect(url_for('login'))
    products = function.get_active_products()
    return render_template("product_list.html", products=products)

#商品內頁
@app.route("/product/<int:product_id>")
def product_detail_page(product_id: int):
    if 'user' not in session:
        return redirect(url_for('login'))
    product = function.get_product_or_404(product_id)
    option_groups = function.get_option_groups(product_id)
    return render_template("product_detail.html", product=product, option_groups=option_groups)

@app.route("/cart")
def cart_page():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template("cart.html")

@app.route("/checkout")
def checkout_page():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template("checkout.html",user=session['user'])

@app.route("/order_success/<int:order_id>")
def order_success_page(order_id: int):
    if 'user' not in session:
        return redirect(url_for('login'))
    order = function.get_order_by_id(order_id)
    if order is None:
        abort(404)
    items = function.get_order_items(order_id)
    return render_template("order_success.html", order=function.enrich_order(order), items=items)

@app.route("/order_list")
def order_list_page():
    if 'user' not in session:
        return redirect(url_for('login'))
    orders = function.get_all_orders()
    return render_template("order_list.html", orders=orders)

@app.route("/admin/orders")
def admin_orders_page():
    if 'user' not in session:
        return redirect(url_for('login'))
    status_filter = request.args.get("status", "").strip()
    if status_filter and status_filter not in function.STATUS_LABELS:
        status_filter = ""
    orders = function.get_all_orders(status_filter or None)
    stats = function.get_today_stats()
    return render_template("admin_orders.html", orders=orders, stats=stats, statuses=function.STATUS_LABELS, current_status=status_filter)

@app.route("/api/products")
def products_json():
    if 'user' not in session:
        return redirect(url_for('login'))
    return function.success({"products": function.get_active_products()})

@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    data = request.get_json(silent=True) or {}
    try:
        cart_code = function.clean_required(data.get("cart_code"), "cart_code", 80)
        product_id = function.parse_int(data.get("product_id"), "product_id", 1)
        quantity = function.parse_int(data.get("quantity"), "quantity", 1, 99)
        option_ids = function.parse_option_ids(data.get("option_ids", []))
        priced_item = function.build_priced_item(product_id, option_ids)
    except ValueError as exc:
        return function.fail(str(exc))
    conn=db.connect()
    cursor=conn.cursor()
    current_time = function.now_text()
    option_ids_text = ",".join(str(option_id) for option_id in priced_item["option_ids"])
    existing = cursor.execute(
        """
        SELECT id, quantity
        FROM cart_items
        WHERE cart_code = ? AND product_id = ? AND option_ids = ?
        """,
        (cart_code, product_id, option_ids_text),
    ).fetchone()
    if existing:  # 相同商品加上相同選項就直接合併，避免購物車重複很多列
        new_quantity = existing["quantity"] + quantity
        cursor.execute(
            """
            UPDATE cart_items
            SET quantity = ?, product_name = ?, base_price = ?, option_total = ?, price = ?, options_text = ?, updated_at = ?
            WHERE id = ?
            """,
            (new_quantity, priced_item["product_name"], priced_item["base_price"], priced_item["option_total"], priced_item["price"], priced_item["options_text"], current_time, existing["id"]),
        )
        item_id = existing["id"]
    else:
        c = cursor.execute(
            """
            INSERT INTO cart_items (cart_code, product_id, product_name, base_price, option_total, price, quantity, options_text, option_ids, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (cart_code, product_id, priced_item["product_name"], priced_item["base_price"], priced_item["option_total"], priced_item["price"], quantity, priced_item["options_text"], option_ids_text, current_time, current_time),
        )
        item_id = c.lastrowid
    conn.commit()
    conn.close()
    return function.success({"message": "已加入購物車", "item_id": item_id})

@app.route("/get_cart_items")
def get_cart_items():
    if 'user' not in session:
        return redirect(url_for('login'))
    cart_code = request.args.get("cart_code", "").strip()
    if not cart_code:
        return function.fail("缺少 cart_code")
    items = function.load_cart_items(cart_code)
    total_amount = sum(item["subtotal"] for item in items)
    total_quantity = sum(item["quantity"] for item in items)
    return function.success({"items": items, "count": len(items), "total_quantity": total_quantity, "total_amount": total_amount})

@app.route("/update_cart_item", methods=["POST"])
def update_cart_item():
    data = request.get_json(silent=True) or {}
    try:
        item_id = function.parse_int(data.get("item_id"), "item_id", 1)
        new_quantity = function.parse_int(data.get("new_quantity"), "new_quantity")
    except ValueError as exc:
        return function.fail(str(exc))
    conn=db.connect()
    cursor=conn.cursor()
    existing = cursor.execute("SELECT id FROM cart_items WHERE id = ?", (item_id,)).fetchone()
    if existing is None:
        return function.fail("找不到這筆購物車商品", 404)
    if new_quantity <= 0:
        cursor.execute("DELETE FROM cart_items WHERE id = ?", (item_id,))
    else:
        cursor.execute("UPDATE cart_items SET quantity = ?, updated_at = ? WHERE id = ?", (new_quantity, function.now_text(), item_id))
    conn.commit()
    conn.close()
    return function.success({"message": "購物車已更新"})

@app.route("/delete_cart_item", methods=["POST"])
def delete_cart_item():
    data = request.get_json(silent=True) or {}
    try:
        item_id = function.parse_int(data.get("item_id"), "item_id", 1)
    except ValueError as exc:
        return function.fail(str(exc))
    conn=db.connect()
    cursor=conn.cursor()
    c = cursor.execute("DELETE FROM cart_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    if c.rowcount == 0:
        return function.fail("找不到這筆購物車商品", 404)
    return function.success({"message": "商品已刪除"})

@app.route("/submit_order", methods=["POST"])
def submit_order():
    return function.create_order_from_payload(request.get_json(silent=True) or {})

@app.route("/api/orders", methods=["POST"])
def create_order_api():
    return function.create_order_from_payload(request.get_json(silent=True) or {})

@app.route("/orders")
def orders_json():
    if 'user' not in session:
        return redirect(url_for('login'))
    return function.success({"orders": function.get_all_orders()})

@app.route("/api/admin/orders/<int:order_id>/status", methods=["POST"])
def update_order_status(order_id: int):
    data = request.get_json(silent=True) or {}
    new_status = str(data.get("status", "")).strip()
    if new_status not in function.STATUS_LABELS:
        return function.fail("不合法的訂單狀態")
    conn=db.connect()
    cursor=conn.cursor()
    row = cursor.execute("SELECT id, status FROM orders WHERE id = ?", (order_id,)).fetchone()
    if row is None:
        return function.fail("找不到這張訂單", 404)
    current_status = row["status"]
    allowed = function.ALLOWED_TRANSITIONS.get(current_status, [])
    if new_status not in allowed:
        return function.fail(f"狀態不能從 {function.status_text(current_status)} 改成 {function.status_text(new_status)}")
    cursor.execute("UPDATE orders SET status = ?, updated_at = ? WHERE id = ?", (new_status, function.now_text(), order_id))
    conn.commit()
    conn.close()
    return function.success({"message": "訂單狀態已更新", "status": new_status, "status_text": function.status_text(new_status)})

@app.route("/api/admin/stats/today")
def today_stats_json():
    if 'user' not in session:
        return redirect(url_for('login'))
    return function.success({"stats": function.get_today_stats()})

@app.route("/health")
def health():
    if 'user' not in session:
        return redirect(url_for('login'))
    return function.success({"message": "ok"})
#------------------------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    port=int(os.environ.get("PORT",5000))#heroku
    app.run(host="0.0.0.0",port=port)#heroku