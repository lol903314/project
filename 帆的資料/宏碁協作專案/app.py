from flask import Flask, render_template,request,redirect,url_for,session,jsonify
import random
import sqlite3
from flask_mail import Mail,Message
from model import member_db

app = Flask(__name__)
app.secret_key='lol'#session金鑰

app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='trumpet903314@gmail.com',
    MAIL_PASSWORD='ajmn bqvf tfaj sgxt')
mail=Mail(app)
   
db=member_db()
db.create_table()

#首頁
@app.route('/')
def home():
    return render_template('home.html')

#訪客登入
@app.route('/guest')
def guest():
    session['user']='訪客'
    session['is_guest']=True
    return render_template('mora.html',msg='將進入點餐頁面')

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
            return redirect(url_for('mora'))
        else:
            return render_template('login.html',msg='帳密錯誤')
        
    return render_template('login.html')

#忘記密碼頁面
@app.route('/forgot_password',methods=['GET','POST'])
def forgot_password():
    if request.method=='POST':
        user=request.form['user']
        email=request.form['email']
        
        conn=sqlite3.connect('member.db')
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
            conn=sqlite3.connect('member.db')
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
    
    conn=sqlite3.connect('member.db')
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
    
    conn=sqlite3.connect('member.db')
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

#猜拳(後續會替換成商品頁)
@app.route('/mora',methods=['GET','POST'])
def mora():
    #如果沒登入過，就自動跳轉登入頁
    if 'user' not in session:
        return redirect(url_for('login'))
    
    you=computer=result=None
    #預設結果session為0
    win=session.get('win',0)
    lose=session.get('lose',0)
    tie=session.get('tie',0)
    
    if request.method=='POST':
        you=request.form['choice']
        computer=random.choice(['stone','paper','scissors'])
        
        if you==computer:
            result='平手'
            tie+=1
        elif (you=='stone' and computer=='scissors') or (you=='scissors' and computer=='paper') or (you=='paper' and computer=='stone'):
            result='你贏了'
            win+=1
        else:
            result='你輸了'
            lose+=1
        
        #更新結果session
        session['win']=win
        session['lose']=lose
        session['tie']=tie
        
    return render_template('mora.html',you=you,computer=computer,result=result,win=win,lose=lose,tie=tie)

#重置次數(後續會砍掉)   
@app.route('/reset')
def reset():
    session['win']=0
    session['lose']=0
    session['tie']=0
    return redirect(url_for('mora'))

if __name__ == '__main__':
    app.run(debug = True,use_reloader=False)