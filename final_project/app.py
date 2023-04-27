from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash #hash password & check 
import mysql.connector
import re 
# import hashlib
# import psycopg2.extras
# import MySQLdb.cursors
"""
TODO:
Simon:
用户可以查询消费记录
用户可以更改游园日期
用户买票/退票

Eric:
用户可以查看游乐园基本信息
用户Parking 提前预约 [车辆基本信息]
用户网上购物

Bill:
管理员可以查询所有用户信息
管理员添改db[商品信息, show, 游乐项目]
管理员查看summary
"""

app = Flask(__name__)

# secret key
app.secret_key = 'your secret key'

# Enter your database connection details below
# app.config['MYSQL_HOST'] = 'localhost'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = ''
# app.config['MYSQL_DB'] = 'pythonlogin'

mydb = mysql.connector.connect(
  host = "localhost",       # 数据库主机地址/db address
  user = "root",            # 数据库用户名/db username
  passwd = 'lOVE0614',              # 数据库密码/db password
  database = 'pythonlogin',  # 数据库名称/db name
)

# cursor = mydb.cursor()
# print(mydb)
# Intialize MySQL
# mysql = MySQL(app)


@app.route('/')
def index():
    # redirect to login page
    return redirect(url_for('login'))

# Home page, only available to the login user
@app.route('/login/home', methods=['GET', 'POST'])
def home():
    # Check user login status
    if 'loggedin' in session:
        # If user is login, show the home page
        # if request.method == 'POST':
            #cursor = mydb.cursor(dictionary=True)
            #integer = request.form['integer']
            #cursor.execute('INSERT INTO testdb VALUES (NULL, %s)', (integer,))
            #mydb.commit()

        return render_template('home.html', username=session['username'])
    # If not, redirect to the login page
    return redirect(url_for('login'))


# Test database function page
@app.route('/login/testdb', methods=['GET', 'POST'])
def testdb():
    msg = ''
    data = {}
    if 'loggedin' in session:
        #cursor.close()
        if request.method == 'POST':
            name = request.form['name']
            number = request.form['number']
            cursor = mydb.cursor(dictionary=True)
            cursor.execute("INSERT INTO testdb VALUES ('{}',{})".format(name, int(number)))
            mydb.commit()
            msg = 'Data enter complete'
        
        # display data in DB
        cursor = mydb.cursor(dictionary=True)
        cursor.execute("SELECT * FROM testdb")
        data = cursor.fetchall()

        return render_template('testdb.html', msg = msg, data = data)
    
    # If not, redirect to the login page
    return redirect(url_for('login'))

# Login function
@app.route('/login/', methods=['GET', 'POST'])
def login():

    if 'loggedin' in session:
        return redirect(url_for('home'))

    # Error message
    msg = ''
    # Check username and password exist in placeholder
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']

        # Check the account exist in DB
        cursor = mydb.cursor(dictionary=True)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        
        # Fetch one record
        account = cursor.fetchone()
        # If account exists
        if account:
            hashed_password = account['password']
            print(hashed_password)
            if(check_password_hash(hashed_password, password)):
                # Create session data, this could be use in other routes
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']
                # Redirect to home page
                # return "login IN!"
                return redirect(url_for('home'))
            else:
                # If account doesnt exist or username/password incorrect
                msg = 'Incorrect Username or Password!'
        else:
            # If account doesnt exist or username/password incorrect
            msg = 'Incorrect Username or Password!'

    return render_template('index.html', msg=msg)


# Logout function
@app.route('/login/logout')
def logout():
    # Remove session data
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)

   # Redirect to login page
   return redirect(url_for('login'))


# Register function
@app.route('/login/register', methods=['GET', 'POST'])
def register():
    # Error message
    msg = ''
    # Check username, password and email exist in placeholder
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        account_type = request.form['account_type']
        print(account_type)

        # Hashing password
        hashed_password = generate_password_hash(password)
        
        # Check the account exist in DB
        cursor = mydb.cursor(dictionary=True)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()

        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        # Email format needs to be correct
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s, %s)', (username, hashed_password, account_type, email,))
            mydb.commit()
            msg = 'You have successfully registered!'
        
    elif request.method == 'POST':
        msg = 'Please fill out the form'

    return render_template('register.html', msg=msg)


# user profile
@app.route('/pythonlogin/profile')
def profile():
    # Check if user is loggedin
    if 'loggedin' in session:
        # Get user account info
        cursor = mydb.cursor(dictionary=True)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        # Show the profile page with account info
        return render_template('profile.html', account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))
     
if __name__ == '__main__':
    #app.run()
    app.run(debug=True) # debug mode on