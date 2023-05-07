from datetime import date, datetime
from flask import Flask, flash, jsonify, render_template, request, redirect, url_for, session
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



def get_tickets_by_uid(uid):
    try:
        data_cursor.execute('SELECT visitor_id as v_id, concat(v_fname, " ", v_lname) as v_name, date(visit_date) as visit_date, vt_type, ticket_id, ticket_type FROM visitors natural join tickets WHERE uid = %s' % (uid))
        tickets = data_cursor.fetchall()
        return tickets
    except:
        return redirect(url_for('tickets'))

def get_ticket_by_vid(vid):
    try:
        data_cursor.execute('SELECT * FROM tickets WHERE visitor_id = %s' % (vid))
        ticket = data_cursor.fetchone()
        return ticket
    except:
        return redirect(url_for('tickets'))

def get_date_by_vid(vid):
    try:
        data_cursor.execute('SELECT visit_date FROM visitors WHERE visitor_id = %s' % (vid))
        date = data_cursor.fetchone()
        return date["visit_date"]
    except:
        return redirect(url_for('tickets'))
    
def get_remain_spot_by_date(visit_date):
    data_cursor.execute('SELECT lot, COUNT(*) as used FROM parking WHERE date(time_in) = "%s" GROUP BY lot' % visit_date)
    used_spot_by_lot =  data_cursor.fetchall()
    remain_spot_by_lot ={}
    for i in ["lotA", "lotB", "lotC", "lotD"]:
        remain_spot_by_lot[i] = 400
    for i in used_spot_by_lot:
        remain_spot_by_lot[i['lot']] = 400 - i['used']
    return remain_spot_by_lot

def get_available_shows_by_date(visit_date):
    data_cursor.execute('SELECT show_id, show_name FROM shows WHERE s_time = "%s"' % visit_date)
    shows =  data_cursor.fetchall()
    return shows

def cancel_parking(payment_id):
    delete_parking_sql = 'delete from parking where payment_id=%s'
    data_cursor.execute(delete_parking_sql % (payment_id, ))
    delete_payment_sql = 'delete from payments where payment_id=%s'
    data_cursor.execute(delete_payment_sql % (payment_id, ))
    data_db.commit()

def cancel_show(payment_id):
    delete_show_sql = 'delete from visitor_shows where payment_id=%s'
    data_cursor.execute(delete_show_sql, (payment_id, ))
    delete_payment_sql = 'delete from payments where payment_id=%s'
    data_cursor.execute(delete_payment_sql, (payment_id, ))
    data_db.commit()

# Try delete function [attraction type]
@app.route('/delete/<int:id>')
def delete_type(id):
    try:
        data_cursor.execute('DELETE FROM attraction_type where attr_type_id = %s', (id,))
        data_db.commit()
        return redirect(url_for('attractions'))
    except:
        return redirect(url_for('attractions'))
    
# Try delete function [attraction]
@app.route('/delete1/<int:id>')
def delete_type1(id):
    try:
        data_cursor.execute('DELETE FROM attractions where attraction_id = %s', (id,))
        data_db.commit()
        return redirect(url_for('attractions'))
    except:
        return redirect(url_for('attractions'))
    
# Try delete function [attraction]
@app.route('/delete2/<int:id>')
def delete_type2(id):
    try:
        data_cursor.execute('DELETE FROM shows where show_id = %s', (id,))
        data_db.commit()
        return redirect(url_for('ashows'))
    except:
        return redirect(url_for('ashows'))
    

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
        data_cursor.execute("SELECT * FROM menu_items")
        items = data_cursor.fetchall()
        return render_template('home.html',
                                username=session['username'],
                                attractions = attractions, 
                                shows = shows, 
                                items = items)

    # If not, redirect to the login page
    return redirect(url_for('login'))


# see all ticket history and allow edit or refund
# now can handle edit or refund, maybe need to seperate from this route
@app.route('/login/payhistory', methods=['GET', 'POST'])
def ticket_history():
    # Check user login status
    data = {}
    if 'loggedin' in session:
        uid = session['id']
        
        ## get of payment, here only shows up the ticket payment
        if request.method == 'GET':
            query_tickets = """
                    select * 
                    from visitors join
                    tickets on visitors.visitor_id = tickets.visitor_id
                    join ticket_attractions on tickets.ticket_id = ticket_attractions.ticket_id
                    join payments on payments.payment_id = ticket_attractions.payment_id
                    where uid=%s
                """
            data_cursor.execute(query_tickets, (uid,))
            tickets = data_cursor.fetchall()

            query_parking = """
                    select * 
                    from visitors join
                    parking on visitors.visitor_id = parking.visitor_id
                    where uid=%s
                """
            data_cursor.execute(query_parking, (uid,))
            parking = data_cursor.fetchall()

            query_shows = """
                    select *
                    from visitors join
                    visitor_shows on visitors.visitor_id = visitor_shows.visitor_id
                    join shows on shows.show_id = visitor_shows.show_id
                    where uid=%s
                    """
            data_cursor.execute(query_shows, (uid,))
            shows = data_cursor.fetchall()
            return render_template('ticket_history.html',
                                   tickets=tickets,
                                   parking=parking,
                                   shows=shows)
        elif request.method == 'POST':
            print(request.form)
            action = request.form['action']

            # handle change_date
            if action == 'change_date':
                vdate = request.form['Vdate']
                mysql = 'update tickets set visit_date=%s'
                data_cursor.execute(mysql, (vdate,))
                data_db.commit()
            # handle refund
            elif action == 'cancel_parking':
                cancel_parking(request.form['parking_payment_id'])
            elif action == 'cancel_show':
                cancel_show(request.form['show_payment_id'])
            else:
                ticket_id = request.form['row_value']
                #delete step by step
                #ticket_attraction, card, payments, tickets

                #first need to get information in ticket_attractions
                mysql = 'select * from ticket_attractions where ticket_id=%s'
                data_cursor.execute(mysql, (ticket_id,))
                Intersect_value = data_cursor.fetchall()
                paymentID = Intersect_value[0]['payment_id']

                cardsql = 'delete from card where payment_id=%s'
                paymentsql = 'delete from payments where payment_id=%s'
                sql = 'delete from ticket_attractions where payment_id=%s'
                parkingsql = 'delete from parking where payment_id=%s'
                ticketsql = 'delete from tickets where ticket_id=%s'
                showsql = 'delete from visitor_shows where payment_id=%s'
                attractionsql = 'delete from ticket_attractions where ticket_id=%s'
                itemsql = 'delete from item_orders where payment_id=%s'
                data_cursor.execute(cardsql, (paymentID,))
                data_cursor.execute(sql, (paymentID,))
                data_cursor.execute(parkingsql, (paymentID,))
                data_cursor.execute(itemsql, (paymentID,))
                data_cursor.execute(showsql, (paymentID,))
                data_cursor.execute(paymentsql, (paymentID,))
                data_cursor.execute(attractionsql, (ticket_id,))
                data_cursor.execute(ticketsql, (ticket_id,))
                data_db.commit()
            
            mysql = """
                select * 
                from visitors join
                tickets on visitors.visitor_id = tickets.visitor_id
                join ticket_attractions on tickets.ticket_id = ticket_attractions.ticket_id
                join payments on payments.payment_id = ticket_attractions.payment_id
                where uid=%s
            """
            data_cursor.execute(mysql, (uid,))
            data = data_cursor.fetchall()

            return render_template('ticketPayment_history.html', data=data)
        
    return redirect(url_for('login'))


# make a payment for ticket
@app.route('/login/payment', methods=['GET', 'POST'])
def payment():
    if 'loggedin' in session:
        if request.method == 'POST':
            # Expirdate = request.form['expdate']
            Expyear = request.form['year']
            ExpMon = request.form['month']
            date_string = '20'+Expyear+'-'+ExpMon
            Expdate = datetime.strptime(date_string, '%Y-%m').date()
            cardNum = request.form['card-number']
            cardtype = request.form.get('cardtype')
            cvv = request.form['CVV']
            fname = request.form['first name']
            lname = request.form['last name']

            data_cursor = data_db.cursor(dictionary=True)
            ticket_id = session['ticket_id']
            session.pop('ticket_id', None)

            # payment need to be resolved
            data_cursor.execute('select * from tickets where ticket_id=%s',(ticket_id,))
            ticket = data_cursor.fetchone()
            pay_amount = float(ticket['price']) * float(ticket['discount'])

            # online purchase can only be debit or credit card
            mysql = 'insert into payments (pay_method, pay_date, pay_amount) values (%s, %s, %s)'
            value = ('CD', date.today(), pay_amount)
            data_cursor.execute(mysql, value)
            payment_id = data_cursor.lastrowid

            # then insert a card information
            mysql = 'insert into card (payment_id, fname, lname, card_num, cvv, expir_date, card_type) values (%s, %s, %s, %s, %s, %s, %s)'
            value = (payment_id, fname, lname, cardNum, cvv, Expdate, cardtype)
            data_cursor.execute(mysql, value)

            # finally connect payment to ticket by inserting into ticket_attractions
            mysql = 'insert into ticket_attractions (ticket_id, attraction_id, payment_id) values (%s, %s, %s)'
            value = (ticket_id, 1, payment_id)
            data_cursor.execute(mysql, value)
            data_db.commit()

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
            
            data_cursor.execute("select * from visitors where emails=%s", (email,))
            visitor = data_cursor.fetchone()
            # don't have visitor need to create on first
            if not visitor:
                # create visitor
                # cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s, %s)', (username, hashed_password, account_type, email,))
                mysql = 'insert into visitors (v_fname, v_lname, city, zipcode, street, state, phone_number, dob, vt_type, visit_date, emails, member_id, uid) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
                value = (fname, lname, city, zipcode, street, state, int(phone), dob, visType, Vdate, email, MemberID, uid,)
                data_cursor.execute(mysql, value)

            # purchase ticket
            data_cursor.execute('SELECT * FROM visitors WHERE emails = %s', (email,))
            row = data_cursor.fetchone()
            visitor_id = row['visitor_id']

            # one personal can only have one ticket
            data_cursor.execute('SELECT * FROM tickets WHERE visitor_id = %s', (visitor_id,))
            visitor_ticket = data_cursor.fetchone()
            if visitor_ticket:
                # print("one can only buy one ticket")
                msg = "One person can only own one ticket"
                return render_template('ticket_purchase.html', msg=msg)
            
            # memeber have special discount
            if visType == "Member":
                mysql = 'insert into tickets (ticket_method, p_date, visit_date, ticket_type, price, discount, visitor_id) values (%s, %s, %s, %s, %s, %s, %s)'
                data_cursor.execute(mysql, ('online', date.today(), Vdate, 'Member', 200, 0.85,  visitor_id))
            else:
                mysql = 'insert into tickets (ticket_method, p_date, visit_date, ticket_type, price, discount, visitor_id) values (%s, %s, %s, %s, %s, %s, %s)'
                # need to solve age here for ticket type {adult, child, senior, member} -- sloved
                data_cursor.execute(mysql, ('online', date.today(), Vdate, 'Child', 200, 0.81,  visitor_id))
            data_db.commit()
        
            # store ticket id for later use
            data_cursor.execute('SELECT * FROM tickets WHERE visitor_id = %s', (visitor_id,))
            tickets = data_cursor.fetchone()
            session['ticket_id']=tickets['ticket_id']
        
            return render_template('makepayment.html')
        
        # for GET option
        return render_template('ticket_purchase.html')
    return redirect(url_for('login'))

# employee home page
@app.route('/login/emphome', methods=['GET', 'POST'])
def emphome():
    if 'loggedin' in session:
        return render_template('emphome.html', username=session['username'])
    
    # If not, redirect to the login page
    return redirect(url_for('login'))

# add & delete attraction
@app.route('/login/attractions', methods=['GET', 'POST'])
def attractions():
    msg = ''
    data = {}
    attraction_data = {}

    if 'loggedin' in session:
        # enter attraction type
        if request.method == 'POST':
            if request.form['submit_button'] == "type":
                attraction_type = request.form['attraction_type']
                cursor = data_db.cursor(dictionary=True)
                cursor.execute("INSERT INTO attraction_type VALUES (NULL,%s)", (attraction_type,))
                data_db.commit()
                msg = 'Type enter complete'

            elif request.form['submit_button'] == "attraction":
                attraction_name = request.form['att_name']
                description = request.form['description']
                attraction_type1 = request.form['attraction_type1']
                status = request.form['status']
                capacity = request.form['capacity']
                height = request.form['height']
                duration = request.form['duration']
                location = request.form['location']
                cursor = data_db.cursor(dictionary=True)
                cursor.execute("INSERT INTO attractions VALUES (NULL,%s,%s,%s,%s,%s,%s,%s,%s)", 
                               (attraction_name,description,attraction_type1,status,capacity,height,duration,location,))
                data_db.commit()
                msg = 'Attraction enter complete'

        cursor = data_db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM attraction_type")
        data = cursor.fetchall()
        #print(data)
        cursor.close()

        cursor = data_db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM attractions")
        attraction_data = cursor.fetchall()
        #print(attraction_data)


        return render_template('attractions.html', msg = msg, data = data, attraction_data = attraction_data)

    # If not, redirect to the login page
    return redirect(url_for('login'))


@app.route('/login/show', methods=['GET', 'POST'])
def ashows():
    msg = ''
    data = {}
    if 'loggedin' in session:
        if request.method == 'POST':
            show_name = request.form['show_name']
            show_type = request.form['show_type']
            show_start = request.form['show_start']
            show_end = request.form['show_end']
            show_wheelchair = request.form['show_wheelchair']
            show_price = request.form['show_price']
            show_description = request.form['show_description']
            cursor = data_db.cursor(dictionary=True)
            cursor.execute("INSERT INTO shows VALUES (NULL,%s,%s,%s,%s,%s,%s,%s)", 
                               (show_name,show_type,show_start,show_end,show_wheelchair,show_price,show_description,))
            data_db.commit()
            msg = 'Show enter complete'
        
        cursor = data_db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM shows")
        data = cursor.fetchall()

        return render_template('shows.html', msg = msg, data = data)
    
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

# User datapage viewd by employees
@app.route('/login/userdata', methods=['GET', 'POST'])
def userdata():
    if'loggedin' in session:
        cursor = login_db.cursor(dictionary=True)
        # account_type = 'employees'
        cursor.execute('SELECT * FROM accounts')
        data = cursor.fetchall()

        return render_template('userdata.html', data = data)
    
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
                    session['account_type'] = account['account_type']
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
@app.route('/login/profile')
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


@app.route('/parking', methods=['GET', 'POST'])
def parking_spot():
    if 'loggedin' in session:
        #TODO: How to let customer book a parking lot? 
        #Step1: check if the cumstomer has a ticket:
        #if no, redirect to the ticket page; if yes, redirect to the checkout page
        #But filter the tickets with parking lot. 
        #redirect to the checkout page with tickets that has parking lot. How to do that?
        tickets = get_tickets_by_uid(session['id'])
        if tickets:
            query_visitor_without_parking = """
            SELECT 
                visitors.visitor_id as v_id, 
                concat(v_fname, " ", v_lname) as v_name, 
                date(visit_date) as visit_date, 
                vt_type, 
                uid
            FROM visitors 
            LEFT JOIN parking ON visitors.visitor_id = parking.visitor_id 
            WHERE parking_id IS NULL and uid = %s;
            """
            data_cursor.execute(query_visitor_without_parking, (session['id'], ))
            visitor_without_parking = data_cursor.fetchall()
            # All visitor has a parking lot
            if len(visitor_without_parking) == 0:
                #TODO: pop up a message to tell customer that all visitors has a parking lot
                #flash('All visitors has a parking lot')
                return render_template('home.html')
            else:
                return render_template('checkout.html', 
                                       tickets=visitor_without_parking, 
                                       type='parking', 
                                       price=19.99)
        # No ticket
        return redirect(url_for('purchase'))


@app.route('/get_remain_spots')
def get_remain_spots():
    v_id = request.args.get('v_id','')
    visit_date = get_date_by_vid(v_id)
    remain_spots = get_remain_spot_by_date(visit_date)
    return jsonify(remain_spots)


@app.route('/shows', methods=['GET', 'POST'])
def shows():
    if 'loggedin' in session:
        #TODO: silimlar to reserve spot: get tickets by uid -> when ticket selected change change the available show
        tickets = get_tickets_by_uid(session['id'])
        if tickets:
            return render_template('checkout.html', 
                                    tickets=tickets, 
                                    type='shows')
        # No ticket
        # TODO: modify this to ticket page from Simon
        return redirect(url_for('purchase'))


@app.route('/get_available_shows')
def get_available_shows():
    v_id = request.args.get('v_id','')
    visit_date = get_date_by_vid(v_id)
    available_shows = get_available_shows_by_date(visit_date)
    return jsonify(available_shows)


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
            return render_template('checkout.html', tickets=tickets, type=type, price=price, item=item)
        else:
            return redirect(url_for('tickets'))
    return redirect(url_for('login'))

@app.route('/complete_payment', methods=['POST'])
def complete_payment():
    if 'loggedin' in session:
        v_id = request.form.get('ticket')
        checkout_type = request.form.get('checkout_type')
        lot = request.form.get('lot')
        show_id = request.form.get('show')
        item = request.form.get('item')
        price = request.form.get('price')
        cardholder_name = request.form.get('cardholder_name')
        card_number = request.form.get('card_number')
        card_type = request.form.get('card_type')
        exp_date = request.form.get('exp_date')
        card_cvv = request.form.get('card_cvv')
        if v_id:
            payment_id = add_payment(price, cardholder_name, card_number, card_type, exp_date, card_cvv)
            if checkout_type == "parking":
                add_parking(v_id, lot, price, payment_id)
            elif checkout_type == "shows":
                add_visitor_shows(v_id, show_id, price)
            # elif checkout_type == "store":
            #     add_item(v_id, item, price)
            #redirect to the user payment history page
            return render_template('payment_popup.html')
    # If not, redirect to the login page
    return redirect(url_for('login'))



def add_payment(price, cardholder_name, card_number, card_type, exp_date, card_cvv):
    #First: add payment information to the payment table
    #Second: add card information to the card table
    #Third: return the payment id
    add_payment_sql = 'INSERT INTO `payments` (`pay_method`, `pay_date`, `pay_amount`) VALUES ("CD", now(), %s);'
    data_cursor.execute(add_payment_sql, (price,))
    data_db.commit()
    data_cursor.execute('SELECT LAST_INSERT_ID()')
    payment_id = data_cursor.fetchone()['LAST_INSERT_ID()']
    f_name, l_name = cardholder_name.split(' ')
    add_card_sql = 'INSERT INTO `card` (`payment_id`, `fname`, `lname`, `card_num`, `cvv`, `expir_date`, `card_type`) VALUES (%s, %s, %s, %s, %s, %s, %s);'
    data_cursor.execute(add_card_sql, (payment_id, f_name, l_name, card_number, card_cvv, convert_exp_date_to_sql_date(exp_date), card_type,))
    return payment_id


def add_parking(v_id, lot, price, payment_id):
    visit_date = get_ticket_by_vid(v_id)['visit_date']
    available_spots = [0] * 400
    data_cursor.execute('SELECT * FROM parking WHERE date(time_in) = %s and lot = "%s"' % (visit_date, "lot"+lot))
    used_spots = data_cursor.fetchall()
    for spot in used_spots:
        available_spots[spot['spot_number']] = 1
    spot = 0
    for i in range(400):
        if available_spots[i] == 0:
            spot = i
            break
    add_parking_sql = 'INSERT INTO `parking` (`visitor_id`, `lot`, `spot_number`, `time_in`, `time_out`, `fee`, `payment_id`) VALUES (%s, %s, %s, %s, DATE_ADD(%s, INTERVAL 1 DAY), %s, %s);'
    data_cursor.execute(add_parking_sql, (v_id, lot, spot,visit_date, visit_date, price, payment_id,))
    data_db.commit()

def add_visitor_shows(v_id, show_id, payment_id):
    add_show_sql = 'INSERT INTO `visitor_shows` (`visitor_id`, `show_id`, `payment_id`) VALUES (%s, %s, %s);'
    data_cursor.execute(add_show_sql, (v_id, show_id, payment_id,))
    data_db.commit()


if __name__ == '__main__':
    #app.run()
    app.run(debug=True) # debug mode on