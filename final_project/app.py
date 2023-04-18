from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
# import psycopg2.extras
# import MySQLdb.cursors
# import re

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
  passwd = '',              # 数据库密码/db password
  database = 'pythonlogin'  # 数据库名称/db name

)

# cursor = mydb.cursor()
# print(mydb)
# Intialize MySQL
# mysql = MySQL(app)

@app.route('/login/', methods=['GET', 'POST'])
def login():
    # Error message
    msg = ''
    # Check username and password in placeholder
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        
        # Check the account exist in DB
        cursor = mydb.cursor(dictionary=True)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
        
        # Fetch one record
        account = cursor.fetchone()
        # If account exists
        if account:
            # Create session data, this could be use in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            # Redirect to home page
            return "login success"
        else:
            # If account doesnt exist or username/password incorrect
            msg = 'Incorrect Username or Password!'

    return render_template('index.html', msg=msg)

if __name__ == '__main__':
    #app.run()
    app.run(debug=True) # debug mode on