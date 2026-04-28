import sqlite3

class member_db:
    #初始化資料庫
    def __init__(self,db_name='member.db'):
        self.db_name=db_name
        
    #串接sqlite3
    def connect(self):
        return sqlite3.connect(self.db_name)
    
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
                IS_VERIFIED INREGER DEFAULT 0)
        '''
        cursor.execute(sql)
        conn.commit()
        conn.close()
   
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