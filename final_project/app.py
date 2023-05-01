from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash #hash password & check 
import mysql.connector
from flask_sqlalchemy import SQLAlchemy
import re 
from datetime import date
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

mydb = mysql.connector.connect(
  host = "localhost",       # 数据库主机地址/db address
  user = "root",            # 数据库用户名/db username
  passwd = '',              # 数据库密码/db password
  database = 'pythonlogin'  # 数据库名称/db name

)

#tmp db name for test
parkdb = mysql.connector.connect(
    host = "localhost",
    user = "root",
    passwd = '',
    database = 'test'
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


# see all payment history and allow edit or refund
# now can handle edit or refund, maybe need to seperate from this route
@app.route('/login/payhistory', methods=['GET', 'POST'])
def payhistory():
    # Check user login status
    data = {}
    if 'loggedin' in session:
        uid = session['id']
        cursor = parkdb.cursor(dictionary=True)
        
        ## get of payment, here only shows up the ticket payment
        if request.method == 'GET':
            mysql = """
                    select * 
                    from visitors join
                    tickets on visitors.visitor_id = tickets.visitor_id
                    join ticket_attractions on tickets.ticket_id = ticket_attractions.ticket_id
                    join payments on payments.payment_id = ticket_attractions.payment_id
                    where uid=%s
                """
            cursor.execute(mysql, (uid,))
            data = cursor.fetchall()
            return render_template('ticketPayment_history.html', data=data)
        elif request.method == 'POST':
            action = request.form['action']

            # handle change_date
            if action == 'change_date':
                print("this is vdate")
                vdate = request.form['Vdate']
                mysql = 'update tickets set visit_date=%s'
                cursor.execute(mysql, (vdate,))
                parkdb.commit()
            # handle refund
            else:
                print("this is refund")
                ticket_id = request.form['row_value']
                #delete step by step
                #ticket_attraction, card, payments, tickets

                #first need to get information in ticket_attractions
                mysql = 'select * from ticket_attractions where ticket_id=%s'
                cursor.execute(mysql, (ticket_id,))
                Intersect_value = cursor.fetchone()
                paymentID = Intersect_value['payment_id']

                cardsql = 'delete from card where payment_id=%s'
                paymentsql = 'delete from payments where payment_id=%s'
                sql = 'delete from ticket_attractions where payment_id=%s'
                ticketsql = 'delete from tickets where ticket_id=%s'
                cursor.execute(cardsql, (paymentID,))
                cursor.execute(sql, (paymentID,))
                cursor.execute(paymentsql, (paymentID,))
                cursor.execute(ticketsql, (ticket_id,))
                parkdb.commit()
            
            mysql = """
                select * 
                from visitors join
                tickets on visitors.visitor_id = tickets.visitor_id
                join ticket_attractions on tickets.ticket_id = ticket_attractions.ticket_id
                join payments on payments.payment_id = ticket_attractions.payment_id
                where uid=%s
            """
            cursor.execute(mysql, (uid,))
            data = cursor.fetchall()

            return render_template('ticketPayment_history.html', data=data)
        
    return redirect(url_for('login'))


# make a payment for ticket
@app.route('/login/payment', methods=['GET', 'POST'])
def payment():
    cursor = parkdb.cursor(dictionary=True)
    if 'loggedin' in session:
        if request.method == 'POST':
            Expirdate = request.form['expdate']
            cardNum = request.form['card-number']
            cardtype = request.form.get('cardtype')
            cvv = request.form['CVV']
            fname = request.form['first name']
            lname = request.form['last name']

            cursor = parkdb.cursor(dictionary=True)
            ticket_id = session['ticket_id']
            session.pop('ticket_id', None)

            # payment need to be resolved
            cursor.execute('select * from tickets where ticket_id=%s',(ticket_id,))
            ticket = cursor.fetchone()
            pay_amount = float(ticket['price']) * float(ticket['discount'])

            # online purchase can only be debit or credit card
            mysql = 'insert into payments (pay_method, pay_date, pay_amount) values (%s, %s, %s)'
            value = ('CD', date.today(), pay_amount)
            cursor.execute(mysql, value)
            payment_id = cursor.lastrowid

            # then insert a card information
            mysql = 'insert into card (payment_id, fname, lname, card_num, cvv, expir_date, card_type) values (%s, %s, %s, %s, %s, %s, %s)'
            value = (payment_id, fname, lname, cardNum, cvv, Expirdate, cardtype)
            cursor.execute(mysql, value)

            # finally connect payment to ticket by inserting into ticket_attractions
            mysql = 'insert into ticket_attractions (ticket_id, attraction_id, payment_id) values (%s, %s, %s)'
            value = (ticket_id, 1, payment_id)
            cursor.execute(mysql, value)
            parkdb.commit()

            return render_template('payment_popup.html')
        # should delete this after finish website
        return render_template('makepayment.html')
    return redirect(url_for('login'))

# Ticket purchase page
@app.route('/login/ticket', methods=['GET', 'POST'])
def purchase():
    msg = ''
    data = {}

    if 'loggedin' in session:
        # if order create then 
        if request.method == 'POST':
            #first create visitor, then create a ticket, and then payment
            Vdate = request.form['Vdate']       # plan visited date
            fname = request.form['first name']
            lname = request.form['last name']
            dob = request.form['dob']       # date of birth
            city = request.form['city']
            zipcode = request.form['zipcode']
            street = request.form['street']
            state = request.form['state']
            phone = request.form['phone number']
            email = request.form['Visitor_email']
            visType = request.form.get('VisitorNum')    # individual or group
            TypeNum = request.form['Visitornumber']     # if group, number of p
            MemberID = request.form['MemberID']         # only member require ID

            uid = session['id']     # new add user id for payment searching for user
            
            cursor = parkdb.cursor(dictionary=True)
            cursor.execute("select * from visitors where emails=%s", (email,))
            visitor = cursor.fetchone()
            # don't have visitor need to create on first
            if not visitor:
                # create visitor
                # cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s, %s)', (username, hashed_password, account_type, email,))
                mysql = 'insert into visitors (v_fname, v_lname, city, zipcode, street, state, phone_number, dob, vt_type, visit_date, emails, member_id, uid) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
                value = (fname, lname, city, zipcode, street, state, int(phone), dob, visType, Vdate, email, MemberID, uid,)
                cursor.execute(mysql, value)

            # purchase ticket
            cursor.execute('SELECT * FROM visitors WHERE emails = %s', (email,))
            row = cursor.fetchone()
            visitor_id = row['visitor_id']

            # one personal can only have one ticket
            cursor.execute('SELECT * FROM tickets WHERE visitor_id = %s', (visitor_id,))
            visitor_ticket = cursor.fetchone()
            if visitor_ticket:
                # print("one can only buy one ticket")
                msg = "One person can only own one ticket"
                return render_template('ticket_purchase.html', msg=msg)
            
            # memeber have special discount
            if visType == "Member":
                mysql = 'insert into tickets (ticket_method, p_date, visit_date, ticket_type, price, discount, visitor_id) values (%s, %s, %s, %s, %s, %s, %s)'
                cursor.execute(mysql, ('online', date.today(), Vdate, 'Member', 200, 0.85,  visitor_id))
            else:
                mysql = 'insert into tickets (ticket_method, p_date, visit_date, ticket_type, price, discount, visitor_id) values (%s, %s, %s, %s, %s, %s, %s)'
                # need to solve age here for ticket type {adult, child, senior, member} -- sloved
                cursor.execute(mysql, ('online', date.today(), Vdate, 'Child', 200, 0.81,  visitor_id))
            parkdb.commit()
        
            # store ticket id for later use
            cursor.execute('SELECT * FROM tickets WHERE visitor_id = %s', (visitor_id,))
            tickets = cursor.fetchone()
            session['ticket_id']=tickets['ticket_id']
        
            return render_template('makepayment.html')
        
        # for GET option
        return render_template('ticket_purchase.html')
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