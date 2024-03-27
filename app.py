from flask import Flask, render_template, request, session, redirect, url_for
import numpy as np
import joblib
import requests
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import random  

app = Flask(__name__)

# Loading the trained model from the .pkl file
regressor = joblib.load('model_file.pkl')
# MYSQL configuration
app.secret_key = 'your secret key'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'floods'

mysql = MySQL(app)

# Defining thresholds for flood risk levels
LOW_RISK_THRESHOLD = 1.5
MEDIUM_RISK_THRESHOLD = 2.5
HIGH_RISK_THRESHOLD = 3.0

# Defining the predict function
def predict_flood_probability_from_rainfall_amount(rainfall_amount):
    predicted_riverlevel = regressor.predict(rainfall_amount.reshape(-1, 1))
    return predicted_riverlevel[0]

def provide_mitigation_strategies(predicted_riverlevel):
    if predicted_riverlevel <= LOW_RISK_THRESHOLD:
        return "LOW RISK: No immediate action required."
    elif LOW_RISK_THRESHOLD < predicted_riverlevel <= MEDIUM_RISK_THRESHOLD:
        return "MEDIUM RISK: Implement mitigation strategies such as strengthening riverbanks and clearing drainage systems."
    elif MEDIUM_RISK_THRESHOLD < predicted_riverlevel <= HIGH_RISK_THRESHOLD:
        return "HIGH RISK: Implement mitigation strategies such as evacuation planning and reinforcing flood defenses."
    else:
        return "CRITICAL RISK: Implement emergency response measures and shelter preparation."

@app.route('/index')
def index():
    if not is_user_logged_in():
        return redirect(url_for('login'))  # Redirect to login if not logged in
    else:
        # Replace this with your actual logic to get the logged-in user's username
        username = session.get('username', None)
    return render_template("index.html", user_authenticated=is_user_authenticated(), username=username)

@app.route('/predict', methods=['POST'])
def predict():
    # Getting data from request
    rainfall_amount = float(request.form['rainfall_amount'])

    predicted_riverlevel = predict_flood_probability_from_rainfall_amount(np.array(rainfall_amount))

    # Determining flood probability
    if predicted_riverlevel > 2.5:
        result = "FLOODS."
    else:
        result = "NO FLOODS."

    # Getting mitigation strategy based on predicted river level
    mitigation_strategy = provide_mitigation_strategies(predicted_riverlevel)

    return render_template('index.html', prediction_text={
        "result": result,
        "predicted_riverlevel": predicted_riverlevel.tolist(),
        "mitigation_strategy": mitigation_strategy
    })

@app.route('/', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
        accounts = cursor.fetchone()

        if accounts:
            # Valid username and password
            session['username'] = username  # Store username in session
            return redirect(url_for('index'))  # Redirect to the index route
        else:
            # Incorrect username/password
            msg = 'Incorrect username/password!'

    return render_template('login.html', msg=msg)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s)', (username, password, email,))
            mysql.connection.commit()
            msg = 'You have successfully registered!'

    return render_template('register.html', msg=msg)

def is_user_logged_in():
    return 'username' in session

def is_user_authenticated():
    return 'username' in session

if __name__ == "__main__":
    app.run(debug=True)
