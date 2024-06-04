#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from flask import Flask, render_template_string, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for session management

# Function to connect to the database
def get_db_connection():
    conn = sqlite3.connect('finance.db')
    conn.row_factory = sqlite3.Row
    return conn

# Ensure the database tables exist
def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            description TEXT NOT NULL,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            user_id INTEGER NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

home_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Personal Finance</title>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Roboto', sans-serif;
            padding: 20px;
            background-color: #f8f9fa;
        }
        h1, h2 {
            margin-bottom: 20px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        .table {
            margin-top: 20px;
        }
        .btn-primary {
            background-color: #007bff;
            border-color: #007bff;
        }
        nav a {
            margin-right: 15px;
            text-decoration: none;
            color: #007bff;
        }
        nav a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Personal Finance</h1>
        <nav>
            <a href="{{ url_for('home') }}">Home</a>
            <a href="{{ url_for('about') }}">About</a>
            {% if 'user_id' in session %}
                <a href="{{ url_for('logout') }}">Logout</a>
            {% else %}
                <a href="{{ url_for('login') }}">Login</a>
                <a href="{{ url_for('signup') }}">SignUp</a>
            {% endif %}
            <a href="{{ url_for('contacts') }}">Contacts</a>
        </nav>

        {% if 'user_id' in session %}
        <form action="{{ url_for('add_transaction') }}" method="post" class="form-group">
            <div class="form-group">
                <label for="amount">Amount:</label>
                <input type="number" step="0.01" name="amount" id="amount" class="form-control" required>
            </div>
            <div class="form-group">
                <label for="description">Description:</label>
                <input type="text" name="description" id="description" class="form-control" required>
            </div>
            <div class="form-group">
                <label for="date">Date:</label>
                <input type="date" name="date" id="date" class="form-control" required>
            </div>
            <div class="form-group">
                <label for="category">Category:</label>
                <select name="category" id="category" class="form-control" required>
                    <option value="income">Income</option>
                    <option value="expense">Expense</option>
                    <option value="savings">Savings</option>
                </select>
            </div>
            <button type="submit" class="btn btn-primary">Add Transaction</button>
        </form>
        
        <h2>Transactions</h2>
        <div class="form-group">
            <label for="filter">Filter by Date:</label>
            <input type="date" id="filter" class="form-control" onchange="filterTransactions()">
        </div>
        
        <h2>Totals</h2>
        <p>Total Income: ₹ {{ total_income }}</p>
        <p>Total Expenses: ₹ {{ total_expense }}</p>
        <p>Total Savings: ₹ {{ total_savings }}</p>

        <table class="table table-striped">
            <thead>
                <tr>
                    <th>Amount</th>
                    <th>Description</th>
                    <th>Date</th>
                    <th>Category</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody id="transactionTable">
                {% for transaction in transactions %}
                <tr>
                    <td>₹ {{ transaction.amount }} </td>
                    <td>{{ transaction.description }}</td>
                    <td>{{ transaction.date }}</td>
                    <td>{{ transaction.category }}</td>
                    <td>
                        <form action="{{ url_for('delete_transaction', id=transaction.id) }}" method="post" style="display:inline;">
                            <button type="submit" class="btn btn-danger btn-sm">Delete</button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <p>Please <a href="{{ url_for('login') }}">login</a> to manage your transactions.</p>
        {% endif %}
    </div>

    <script>
        function filterTransactions() {
            const filter = document.getElementById('filter').value;
            const rows = document.getElementById('transactionTable').getElementsByTagName('tr');
            for (let i = 0; i < rows.length; i++) {
                const date = rows[i].getElementsByTagName('td')[2].innerText;
                if (date >= filter) {
                    rows[i].style.display = '';
                } else {
                    rows[i].style.display = 'none';
                }
            }
        }

        document.getElementById('date').max = new Date().toISOString().split("T")[0];
    </script>
</body>
</html>


"""

about_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>About Personal Finance</title>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Roboto', sans-serif;
            background-color: #f8f9fa;
            padding: 20px;
        }
        .content {
            background: #ffffff;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        h1, h2 {
            font-weight: 700;
            margin-bottom: 20px;
        }
        p {
            margin-bottom: 20px;
            line-height: 1.6;
        }
        .steps {
            list-style-type: none;
            padding: 0;
        }
        .steps li {
            background: #e9ecef;
            margin: 10px 0;
            padding: 10px;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="content">
            <h1>About Personal Finance</h1>
            <p>Personal finance is the financial management that an individual or a family unit performs to budget, save, and spend monetary resources in a controlled manner, taking into account various financial risks and future life events.</p>
            <p>When planning personal finances, the individual would take into account the suitability of various banking products (checking accounts, savings accounts, credit cards, and loans), insurance products (health insurance, disability insurance, life insurance, etc.), and investment products (bonds, stocks, real estate, etc.), as well as participation in monitoring and management of credit scores, income taxes, retirement funds and pensions.</p>
            <h2>Financial Planning</h2>
            <p>The key component of personal finance is financial planning which is a dynamic process requiring regular monitoring and re-evaluation. In general, it involves five steps:</p>
            <ol class="steps">
                <li><strong>Assessment:</strong> A person's financial situation is assessed by compiling simplified versions of financial statements, including balance sheets and income statements. A personal balance sheet lists the values of personal assets (e.g., car, house, clothes, stocks, bank account, cryptocurrencies), along with personal liabilities (e.g., credit card debt, bank loan, mortgage). A personal income statement lists personal income and expenses.</li>
                <li><strong>Goal setting:</strong> Multiple goals are expected, including short- and long-term goals. For example, a long-term goal would be to "retire at age 65 with a personal net worth of $1,000,000," while a short-term goal would be to "save up for a new computer in the next month." Setting financial goals helps direct financial planning. Goal setting is done with an objective to meet certain financial requirements.</li>
                <li><strong>Plan creation:</strong> The financial plan details how to accomplish goals. It could include, for example, reducing unnecessary expenses, increasing employment income, or investing in the stock market.</li>
                <li><strong>Execution:</strong> Execution of a financial plan often requires discipline and perseverance. Many people obtain assistance from professionals such as accountants, financial planners, investment advisers, and lawyers.</li>
                <li><strong>Monitoring and reassessment:</strong> The financial plan is monitored in regular intervals to determine if one is on track to reach their goals. This information is evaluated to make potential adjustments as time passes and circumstances change.</li>
            </ol>
            <p>Typical goals that most adults and young adults have are paying off credit card/student loan/housing/car loan debt, investing for retirement, investing for college costs for children, and paying medical expenses.</p>
        </div>
    </div>
</body>
</html>
"""

login_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login</title>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Roboto', sans-serif;
            background-color: #f8f9fa;
            padding: 20px;
        }
        .login-container {
            max-width: 400px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        h2 {
            font-weight: 700;
            margin-bottom: 20px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        .btn-primary {
            background-color: #007bff;
            border-color: #007bff;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h2>Login</h2>
        <form action="{{ url_for('login') }}" method="post">
            <div class="form-group">
                <label for="username">Username:</label>
                <input type="text" name="username" id="username" class="form-control" required>
            </div>
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" name="password" id="password" class="form-control" required>
            </div>
            <button type="submit" class="btn btn-primary">Login</button>
        </form>
        <p class="mt-3">Don't have an account? <a href="{{ url_for('signup') }}">Sign up here</a>.</p>
    </div>
</body>
</html>
"""

signup_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sign Up</title>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Roboto', sans-serif;
            background-color: #f8f9fa;
            padding: 20px;
        }
        .signup-container {
            max-width: 400px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        h2 {
            font-weight: 700;
            margin-bottom: 20px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        .btn-primary {
            background-color: #007bff;
            border-color: #007bff;
        }
    </style>
</head>
<body>
    <div class="signup-container">
        <h2>Sign Up</h2>
        <form action="{{ url_for('signup') }}" method="post">
            <div class="form-group">
                <label for="username">Username:</label>
                <input type="text" name="username" id="username" class="form-control" required>
            </div>
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" name="password" id="password" class="form-control" required>
            </div>
            <button type="submit" class="btn btn-primary">Sign Up</button>
        </form>
    </div>
</body>
</html>
"""

contacts_html="""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Contact Us</title>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Roboto', sans-serif;
            background-color: #f8f9fa;
            padding: 20px;
        }
        .contact-container {
            max-width: 600px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        h2 {
            font-weight: 700;
            margin-bottom: 20px;
        }
        p {
            margin-bottom: 20px;
            line-height: 1.6;
        }
        .contact-info {
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="contact-container">
        <h2>Contact Us</h2>
        <div class="contact-info">
            <p>If you have any questions or feedback, feel free to reach out to us using the following contact information:</p>
            <p><strong>Email:</strong> expenseease@gmail.com</p>
            <p><strong>Phone:</strong> +91 9880210666</p>
        </div>
        <div class="feedback-form">
            <h3>Send Feedback</h3>
            <form action="/submit_feedback" method="post">
                <div class="form-group">
                    <label for="name">Name:</label>
                    <input type="text" name="name" id="name" class="form-control" required>
                </div>
                <div class="form-group">
                    <label for="email">Email:</label>
                    <input type="email" name="email" id="email" class="form-control" required>
                </div>
                <div class="form-group">
                    <label for="message">Message:</label>
                    <textarea name="message" id="message" class="form-control" rows="5" required></textarea>
                </div>
                <button type="submit" class="btn btn-primary">Send</button>
            </form>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    transactions = conn.execute('SELECT * FROM transactions WHERE user_id = ?', (user_id,)).fetchall()
    total_income = conn.execute('SELECT SUM(amount) FROM transactions WHERE user_id = ? AND category = ?', (user_id, 'income')).fetchone()[0] or 0
    total_expense = conn.execute('SELECT SUM(amount) FROM transactions WHERE user_id = ? AND category = ?', (user_id, 'expense')).fetchone()[0] or 0
    total_savings = conn.execute('SELECT SUM(amount) FROM transactions WHERE user_id = ? AND category = ?', (user_id, 'savings')).fetchone()[0] or 0
    conn.close()
    return render_template_string(home_html, transactions=transactions, total_income=total_income, total_expense=total_expense, total_savings=total_savings)

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    amount = request.form['amount']
    description = request.form['description']
    date = request.form['date']
    category = request.form['category']
    user_id = session['user_id']

    conn = get_db_connection()
    conn.execute('INSERT INTO transactions (amount, description, date, category, user_id) VALUES (?, ?, ?, ?, ?)',
                 (amount, description, date, category, user_id))
    conn.commit()
    conn.close()

    return redirect(url_for('home'))

@app.route('/delete_transaction/<int:id>', methods=['POST'])
def delete_transaction(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.execute('DELETE FROM transactions WHERE id = ?', (id,))
    conn.commit()
    conn.close()

    return redirect(url_for('home'))


@app.route('/about')
def about():
    return render_template_string(about_html)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            return redirect(url_for('home'))
        else:
            return 'Invalid username or password'

    return render_template_string(login_html)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        conn.close()

        return redirect(url_for('login'))

    return render_template_string(signup_html)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/contacts')
def contacts():
    return render_template_string(contacts_html)

if __name__ == '__main__':
    app.run(port=9000)


# In[ ]:




