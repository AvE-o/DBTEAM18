from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash #hash password & check 
import mysql.connector
import re 
from utils import convert_date_to_day, convert_exp_date_to_sql_date
# import hashlib
# import psycopg2.extras
# import MySQLdb.cursors

app = Flask(__name__)

# secret key
app.secret_key = 'your secret key'

# Enter your database connection details below
# app.config['MYSQL_HOST'] = 'localhost'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = ''
# app.config['MYSQL_DB'] = 'pythonlogin'

login_db = mysql.connector.connect(
  host = "localhost",       # 数据库主机地址/db address
  user = "root",            # 数据库用户名/db username
  passwd = '',              # 数据库密码/db password
  database = 'pythonlogin', # 数据库名称/db name
)

data_db = mysql.connector.connect(
  host = "localhost",       # 数据库主机地址/db address
  user = "root",            # 数据库用户名/db username
  passwd = '',              # 数据库密码/db password
  database = 'test',     # 数据库名称/db name
)
data_cursor = data_db.cursor(dictionary=True)

# cursor = mydb.cursor()
# print(mydb)
# Intialize MySQL
# mysql = MySQL(app)


def get_tickets_by_uid(uid):
    try:
        data_cursor.execute('SELECT visitor_id as v_id, concat(v_fname, " ", v_lname) as v_name, visit_date, vt_type, ticket_id, ticket_type FROM visitors natural join tickets WHERE uid = %s' % (uid))
        tickets = data_cursor.fetchall()
        return tickets
    except:
        return redirect(url_for('tickets'))

def get_ticket_by_vid(vid):
    try:
        data_cursor.execute('SELECt * FROM tickets WHERE visitor_id = %s' % (vid))
        ticket = data_cursor.fetchone()
        return ticket
    except:
        return redirect(url_for('tickets'))
    
def get_remain_spot_by_date(visit_date):
    data_cursor.execute('SELECT lot, COUNT(*) as used FROM parking WHERE date(time_in) = %s GROUP BY lot' % convert_date_to_day(visit_date))
    used_spot_by_lot =  data_cursor.fetchall()
    remain_spot_by_lot ={}
    for i in ["lotA", "lotB", "lotC", "lotD"]:
        remain_spot_by_lot[i] = 400
    for i in used_spot_by_lot:
        remain_spot_by_lot[i['lot']] = 400 - i['used']
    return remain_spot_by_lot

@app.route('/')
def index():
    # redirect to login page
    return redirect(url_for('login'))

# Home page, only available to the login customer user
@app.route('/login/home', methods=['GET', 'POST'])
def home():
    # Check user login status
    if 'loggedin' in session:
        data_cursor.execute("SELECT * FROM attractions")
        attractions = data_cursor.fetchall()
        data_cursor.execute("SELECT * FROM shows")
        shows = data_cursor.fetchall()
        data_cursor.execute("SELECT * FROM store")
        stores = data_cursor.fetchall()
        return render_template('home.html',
                                username=session['username'],
                                attractions = attractions, 
                                shows = shows, 
                                stores = stores)

    # If not, redirect to the login page
    return redirect(url_for('login'))


@app.route('/login/emphome', methods=['GET', 'POST'])
def emphome():
    if 'loggedin' in session:
        return render_template('emphome.html', username=session['username'])
    
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
            cursor = login_db.cursor(dictionary=True)
            cursor.execute("INSERT INTO testdb VALUES ('{}',{})".format(name, int(number)))
            login_db.commit()
            msg = 'Data enter complete'
        
        # display data in DB
        cursor = login_db.cursor(dictionary=True)
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
        cursor = login_db.cursor(dictionary=True)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        
        # Fetch one record
        account = cursor.fetchone()
        # If account exists
        if account:
            hashed_password = account['password']
            account_type = account['account_type']
            print(hashed_password)
            if(check_password_hash(hashed_password, password)):
                if(account_type == 'customers'):
                    # Create session data, this could be use in other routes
                    session['loggedin'] = True
                    session['id'] = account['id']
                    session['username'] = account['username']
                    # Redirect to home page
                    # return "login IN!"
                    return redirect(url_for('home'))
                else:
                    # Create session data, this could be use in other routes
                    session['loggedin'] = True
                    session['id'] = account['id']
                    session['username'] = account['username']
                    return redirect(url_for('emphome'))
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
        cursor = login_db.cursor(dictionary=True)
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
            login_db.commit()
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
        cursor = login_db.cursor(dictionary=True)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        # Show the profile page with account info
        return render_template('profile.html', account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

# for get request, show all available parking slots by location, which including LotA, LotB, LotC, LotD and by time.  
# for post request, pass the parking slot information and user information to the checkout page.
@app.route('/parking', methods=['GET', 'POST'])
def parking_spot():
    if 'loggedin' in session:
        #TODO: How to let customer book a parking lot? 
        #Step1: check if the cumstomer has a ticket:
        #if no, redirect to the ticket page; if yes, check if the customer has a parking lot:
        #if no, redirect to the parking page; if yes, show the parking lot information
        tickets = get_tickets_by_uid(session['id'])
        if tickets:
            data_cursor.execute('SELECT visitor_id as v_id, concat(v_fname, " ", v_lname) as v_name, DATE_FORMAT(visit_date, "%%Y-%%m-%%d") as visit_date, lot, spot_number FROM visitors natural join parking WHERE uid = %s' % (session['id']))
            parking_order = data_cursor.fetchall()
            remain_spot_by_lot = {} # key: lot, value: remain spot. Example: {"lotA": 100, "lotB": 200, "lotC": 300, "lotD": 400} 
            # Already has a parking lot
            # popup a window to show the parking lot information
            if not parking_order:
                #TODO: show the parking order information
                return render_template('parking_order.html', 
                                       parking_order=parking_order, 
                                       remain_spot_by_lot=remain_spot_by_lot, 
                                       username=session['username'])
            # No parking lot
            else:
                #TODO: temperarily use the first ticket's visit date to get the remain spot by lot
                remain_spot_by_lot = get_remain_spot_by_date(tickets[0]['visit_date'])
                return render_template('parking_reserve.html', remain_spot_by_lot=remain_spot_by_lot)
        # No ticket
        # TODO: modify this to ticket page from Simon
        return redirect(url_for('ticket'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'loggedin' in session:
        #TODO: Checkout page for customer
        #select visitor by name
        type = request.args.get('type','')
        item = request.args.get('item','')
        price = 0
        tickets = get_tickets_by_uid(session['id'])
        
        if tickets:
            if type == 'parking':
                price = 19.99
            elif type == 'show':
                price = 29.99
            elif type == 'store':
                price = 9.99
            else:
                return redirect(url_for('home'))
            return render_template('checkout.html', tickets=tickets, type=type, price=price)
        else:
            return redirect(url_for('tickets'))
    return redirect(url_for('login'))

@app.route('/complete_payment', methods=['POST'])
def complete_payment():
    if 'loggedin' in session:
        v_id = request.form.get('ticket')
        checkout_type = request.form.get('checkout_type')
        lot = request.form.get('lot')
        show = request.form.get('show')
        item = request.form.get('item')
        price = request.form.get('price')
        cardholder_name = request.form.get('cardholder_name')
        card_number = request.form.get('card_number')
        card_type = request.form.get('card_type')
        exp_date = request.form.get('exp_date')
        card_cvv = request.form.get('card_cvv')
        print(card_type)
        if v_id:
            payment_id = add_payment(price, cardholder_name, card_number, card_type, exp_date, card_cvv)
            if checkout_type == "parking":
                add_parking(v_id, lot, price, payment_id)
            # elif checkout_type == "show":
            #     add_show(v_id, show, price)
            # elif checkout_type == "store":
            #     add_item(v_id, item, price)
            #redirect to the user payment history page
            return redirect(url_for('profile'))
    # If not, redirect to the login page
    return redirect(url_for('login'))

def add_payment(price, cardholder_name, card_number, card_type, exp_date, card_cvv):
    #First: add payment information to the payment table
    #Second: add card information to the card table
    #Third: return the payment id
    data_cursor.execute('INSERT INTO `payments` (`pay_method`, `pay_date`, `pay_amount`) VALUES ("CD", now(), %s);' % price)
    data_db.commit()
    data_cursor.execute('SELECT LAST_INSERT_ID()')
    payment_id = data_cursor.fetchone()['LAST_INSERT_ID()']
    f_name, l_name = cardholder_name.split(' ')
    data_cursor.execute("INSERT INTO `card` (`payment_id`, `fname`, `lname`, `card_num`, `cvv`, `expir_date`, `card_type`) VALUES (%s, '%s', '%s', '%s', '%s', '%s', '%s');" % (payment_id, f_name, l_name, card_number, card_cvv, convert_exp_date_to_sql_date(exp_date), card_type))
    return payment_id


def add_parking(v_id, lot, price, payment_id):
    visit_date = get_ticket_by_vid(v_id)['visit_date']
    available_spots = [0] * 400
    data_cursor.execute('SELECT * FROM parking WHERE date(time_in) = %s and lot = "%s"' % (convert_date_to_day(visit_date), "lot"+lot))
    used_spots = data_cursor.fetchall()
    for spot in used_spots:
        available_spots[spot['spot_number']] = 1
    spot = 0
    for i in range(400):
        if available_spots[i] == 0:
            spot = i
            break
    data_cursor.execute('INSERT INTO parking (visitor_id, lot, spot_number, time_in, time_out, fee, payment_id) VALUES (%s, "%s", %s, %s, DATE_ADD(%s, INTERVAL 1 DAY), %s, %s)' % (v_id, lot, spot,visit_date, visit_date, price, payment_id))
    data_db.commit()


if __name__ == '__main__':
    #app.run()
    app.run(debug=True) # debug mode on