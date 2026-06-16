from flask import Flask, send_from_directory, request, jsonify, session
import sqlite3, hashlib, os

app = Flask(__name__)
app.secret_key = 'product-store-demo-secret-xk92ms'

BASE = os.path.dirname(os.path.realpath(__file__))
DB   = os.path.join(BASE, 'store.db')

# ── Database ─────────────────────────────────────────────────────────────────

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as c:
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    UNIQUE NOT NULL,
            password TEXT    NOT NULL,
            balance  REAL    NOT NULL DEFAULT 0.0
        )''')
        c.commit()

def sha(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# ── Static file serving ───────────────────────────────────────────────────────

@app.route('/')
def root():
    return send_from_directory(BASE, 'login.html')

@app.route('/<path:fname>')
def static_file(fname):
    return send_from_directory(BASE, fname)

# ── Auth API ──────────────────────────────────────────────────────────────────

@app.route('/api/register', methods=['POST'])
def register():
    d = request.get_json()
    u = (d.get('username') or '').strip()
    p = (d.get('password') or '').strip()
    if not u or not p:
        return jsonify(error='Username and password are required'), 400
    if len(p) < 3:
        return jsonify(error='Password must be at least 3 characters'), 400
    try:
        with db() as c:
            c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (u, sha(p)))
            c.commit()
            row = c.execute('SELECT * FROM users WHERE username=?', (u,)).fetchone()
        session['uid']      = row['id']
        session['username'] = row['username']
        return jsonify(success=True, username=u, balance=0.0)
    except sqlite3.IntegrityError:
        return jsonify(error='Username already taken'), 400

@app.route('/api/login', methods=['POST'])
def login():
    d = request.get_json()
    u = (d.get('username') or '').strip()
    p = (d.get('password') or '').strip()
    with db() as c:
        row = c.execute(
            'SELECT * FROM users WHERE username=? AND password=?', (u, sha(p))
        ).fetchone()
    if not row:
        return jsonify(error='Invalid username or password'), 401
    session['uid']      = row['id']
    session['username'] = row['username']
    return jsonify(success=True, username=row['username'], balance=row['balance'])

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify(success=True)

@app.route('/api/user')
def get_user():
    if 'uid' not in session:
        return jsonify(error='Not logged in'), 401
    with db() as c:
        row = c.execute('SELECT username, balance FROM users WHERE id=?', (session['uid'],)).fetchone()
    if not row:
        session.clear()
        return jsonify(error='User not found'), 401
    return jsonify(username=row['username'], balance=row['balance'])

# ── Balance API ───────────────────────────────────────────────────────────────

@app.route('/api/balance/add', methods=['POST'])
def add_balance():
    if 'uid' not in session:
        return jsonify(error='Not logged in'), 401
    try:
        amount = float(request.get_json().get('amount', 0))
    except (TypeError, ValueError):
        return jsonify(error='Invalid amount'), 400
    if amount <= 0 or amount > 1_000_000:
        return jsonify(error='Enter a valid amount (1 – 1,000,000)'), 400
    with db() as c:
        c.execute('UPDATE users SET balance=balance+? WHERE id=?', (amount, session['uid']))
        c.commit()
        row = c.execute('SELECT balance FROM users WHERE id=?', (session['uid'],)).fetchone()
    return jsonify(success=True, balance=row['balance'])

@app.route('/api/purchase', methods=['POST'])
def purchase():
    if 'uid' not in session:
        return jsonify(error='Not logged in'), 401
    try:
        total = float(request.get_json().get('total', 0))
    except (TypeError, ValueError):
        return jsonify(error='Invalid total'), 400
    if total <= 0:
        return jsonify(error='Cart is empty'), 400
    with db() as c:
        row = c.execute('SELECT balance FROM users WHERE id=?', (session['uid'],)).fetchone()
        if row['balance'] < total:
            return jsonify(
                error=f'Insufficient balance. You have {row["balance"]:.2f}$ but need {total:.2f}$'
            ), 400
        c.execute('UPDATE users SET balance=balance-? WHERE id=?', (total, session['uid']))
        c.commit()
        row = c.execute('SELECT balance FROM users WHERE id=?', (session['uid'],)).fetchone()
    return jsonify(success=True, balance=row['balance'])

# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    print('\n  Product Store running at: http://localhost:5000\n')
    app.run(debug=True, port=5000)
