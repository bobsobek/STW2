from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import sqlite3
import json
import stripe
import search_engine
from flask_bcrypt import Bcrypt
import PyPDF2

# prompt_breakdown
# get_weightage
from pymongo import MongoClient
from pymongo.server_api import ServerApi

# DO ONLY ONCE TO LOAD INFO INTO MONGODB
'''
pdf_open.syllabus_load_into_mongodb()
pdf_open.indiv_load_into_mongodb()
'''

conn = sqlite3.connect('engine.db')
cur = conn.cursor()

cur.execute('''CREATE TABLE IF NOT EXISTS users (
userid INTEGER PRIMARY KEY,
username TEXT NOT NULL,
name TEXT NOT NULL, 
email TEXT NOT NULL UNIQUE,
password_hash BLOB NOT NULL)''')

cur.execute('''CREATE TABLE IF NOT EXISTS members (
memberid INTEGER PRIMARY KEY,
userid INTEGER NOT NULL,
role TEXT,
FOREIGN KEY (userid) REFERENCES users (userid))''')

cur.execute('''CREATE TABLE IF NOT EXISTS prompts (
userid INTEGER NOT NULL,
prompt TEXT NOT NULL,
response TEXT NOT NULL, 
FOREIGN KEY (userid) REFERENCES users (userid))''')

conn.commit()
conn.close()

app = Flask(__name__, static_folder='public', static_url_path='', template_folder='templates')
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
bcrypt = Bcrypt(app)

@app.route('/', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    username = request.form['username']
    password = request.form['password']
    conn = sqlite3.connect('engine.db')
    cur = conn.cursor()
    cur.execute('''SELECT password_hash 
    FROM users 
    WHERE username = ?''', (username,))
    hash_result = cur.fetchone()
    hash = hash_result[0]
    conn.close()    
    validation = bcrypt.check_password_hash(hash, password)
    if validation:
      session['username'] = username
      return redirect(url_for('home'))
    else:
      return render_template('login.html', message='Invalid username or password')
  return render_template('login.html', message='')

@app.route('/home')
def home():
  return render_template('home.html')
    
@app.route('/bio', methods=['GET', 'POST'])
def bio():
  if request.method == 'POST':
    return redirect(url_for('results', query=request.form['query']))

  return render_template('bio.html')

@app.route('/results')
def results():
  prompt = request.args.get('query')  # Retrieving query parameter from URL
  pdf_and_page = search_engine.search_engine(prompt)
  pdfName = list(pdf_and_page.keys())[0]
  pdfPage = pdf_and_page[pdfName]
  pdfPage = int(pdfPage[0])
  with open(f'data/bio/{pdfName}', 'rb') as f:
    reader = PyPDF2.PdfReader(f)
    page = reader.pages[pdfPage-1]
    text = page.extract_text()
  return render_template('results.html', pdf_and_page=pdf_and_page, pdfName=pdfName, page=page, text=text)

@app.route('/logout')
def logout():
  session.pop('username', None)
  return redirect(url_for('index'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
  if request.method == 'POST':
    username = request.form['username']
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    hash = bcrypt.generate_password_hash(password).decode('utf-8')
    conn = sqlite3.connect('engine.db')
    cur = conn.cursor()
    cur.execute('''SELECT email 
    FROM users 
    WHERE email = ?''', (email,))
    recs = cur.fetchall()
    if email in recs:
      return render_template('signup.html', message='Email already in use')
    else:
      cur.execute('''INSERT INTO users (
      username,
      name, 
      email, 
      password_hash
      ) 
      VALUES (?, ?, ?, ?)''', (username, name, email, hash))
      conn.commit()
      conn.close()
      print('Inserted into users')
      return redirect(url_for('login'))
  return render_template('signup.html', message='')


# This is your test secret API key.
stripe.api_key = 'pk_live_51P6BVO09zvePxwpfEYVZy8mJLuZV5GbkJHNHyVvT9520ylxqWKb5e6dPo7H0ASuIga7TSXxkbBiCnIQ9nBxpqiRl006C8ZVoeE'
def calculate_order_amount(items):
  return 1400
  
@app.route('/donate', methods=['POST'])
def donate():
  try:
    data = json.loads(request.data)
    # Create a PaymentIntent with the order amount and currency
    intent = stripe.PaymentIntent.create(
      amount=calculate_order_amount(data['items']),
      currency='sgd',
      automatic_payment_methods={
        'enabled': True,
      },
    )
    return jsonify({'clientSecret': intent['client_secret']})
  except Exception as e:
    return jsonify(error=str(e)), 403

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=80)
