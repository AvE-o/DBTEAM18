# Author by : ME!
# Date : 2023-02-27

from flask import Flask, render_template, url_for, request
from flask_mysqldb import MySQL

app = Flask(__name__)

# here use localhost as example
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
# here my database name is 'users'
app.config['MYSQL_DB'] = 'users'
 
mysql = MySQL(app)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test')
def hello_test():
    return 'Test'

if __name__ == '__main__':
    # app.run()
    app.run(debug=True) # debug mode on


