from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from flask_pymongo import PyMongo
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from datetime import datetime
import io
import csv
import math

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config["MONGO_URI"] = "mongodb://localhost:27017/expense_tracker"
mongo = PyMongo(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

ITEMS_PER_PAGE = 5
BUDGET_GOAL = 5000  # Monthly budget

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']

@login_manager.user_loader
def load_user(user_id):
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    return User(user) if user else None

@app.route('/')
def index():
    return redirect(url_for('dashboard')) if current_user.is_authenticated else redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        if mongo.db.users.find_one({'email': email}):
            return 'Email already exists'
        mongo.db.users.insert_one({'username': username, 'email': email, 'password_hash': password})
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = mongo.db.users.find_one({'email': request.form['email']})
        if user and check_password_hash(user['password_hash'], request.form['password']):
            login_user(User(user))
            return redirect(url_for('dashboard'))
        flash('Wrong credentials')
        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    page = int(request.args.get('page', 1))
    category_filter = request.args.get('category', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    user_id = ObjectId(current_user.id)

    query = {'user_id': user_id}
    if category_filter:
        query['category'] = category_filter
    if start_date:
        query['date'] = {'$gte': datetime.strptime(start_date, '%Y-%m-%d')}
    if end_date:
        if 'date' not in query:
            query['date'] = {}
        query['date']['$lte'] = datetime.strptime(end_date, '%Y-%m-%d')

    all_expenses = list(mongo.db.expenses.find(query).sort('date', -1))
    expenses = all_expenses[(page - 1) * ITEMS_PER_PAGE: page * ITEMS_PER_PAGE]

    total = sum(e['amount'] for e in all_expenses)
    monthly_total = sum(e['amount'] for e in all_expenses if e['date'].month == datetime.now().month and e['date'].year == datetime.now().year)
    total_pages = math.ceil(len(all_expenses) / ITEMS_PER_PAGE)

    all_user_expenses = mongo.db.expenses.find({'user_id': user_id})
    categories = sorted(set(e['category'] for e in all_user_expenses))

    return render_template('dashboard.html', 
                           expenses=expenses,
                           total=total,
                           page=page,
                           total_pages=total_pages,
                           monthly_total=monthly_total,
                           budget_goal=BUDGET_GOAL,
                           category_filter=category_filter,
                           categories=categories,
                           start_date=start_date,
                           end_date=end_date)

@app.route('/add_expense', methods=['POST'])
@login_required
def add_expense():
    try:
        data = {
            'user_id': ObjectId(current_user.id),
            'category': request.form['category'],
            'amount': float(request.form['amount']),
            'date': datetime.strptime(request.form['date'], '%Y-%m-%d'),
            'note': request.form['note']
        }
        mongo.db.expenses.insert_one(data)
        flash('Expense added successfully!')
    except Exception as e:
        flash(f'Error adding expense: {str(e)}')
    return redirect(url_for('dashboard'))

@app.route('/delete_expense/<expense_id>')
@login_required
def delete_expense(expense_id):
    mongo.db.expenses.delete_one({'_id': ObjectId(expense_id)})
    flash('Expense deleted.')
    return redirect(url_for('dashboard'))

@app.route('/export_csv')
@login_required
def export_csv():
    user_id = ObjectId(current_user.id)
    expenses = mongo.db.expenses.find({'user_id': user_id})
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Category', 'Amount', 'Date', 'Note'])

    for e in expenses:
        writer.writerow([e['category'], e['amount'], e['date'].strftime('%Y-%m-%d'), e['note']])

    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv', as_attachment=True, download_name='expenses.csv')

if __name__ == '__main__':
    app.run(debug=True)
