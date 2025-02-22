from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from functools import wraps
from config import Config
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, set_access_cookies, unset_jwt_cookies
from datetime import timedelta
from database.db import Database

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
app.config['JWT_SECRET_KEY'] = Config.SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']
app.config['JWT_COOKIE_CSRF_PROTECT'] = False
app.config['JWT_COOKIE_SECURE'] = False  # Set to True in production
app.config['JWT_COOKIE_SAMESITE'] = 'Lax'
app.config['JWT_SESSION_COOKIE'] = False
jwt = JWTManager(app)

def login_required(f):
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.json.get('username') if request.is_json else request.form.get('username')
        password = request.json.get('password') if request.is_json else request.form.get('password')
        
        if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
            access_token = create_access_token(identity=username)
            
            # Create response object based on request type
            if request.is_json:
                response = jsonify({
                    'access_token': access_token,
                    'token_type': 'Bearer'
                })
            else:
                response = redirect(url_for('dashboard'))
            
            # Set JWT cookies for both API and form responses
            set_access_cookies(response, access_token)
            return response
        
        error_response = jsonify({"msg": "Invalid credentials"}) if request.is_json else render_template('login.html', error="Invalid credentials")
        return error_response, 401 if request.is_json else 200
    
    return render_template('login.html')

@app.route('/')
@login_required
def dashboard():
    current_user = get_jwt_identity()
    return render_template('dashboard.html', username=current_user)

@app.route('/api/verify_token')
@jwt_required()
def verify_token():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

@app.route('/logout')
def logout():
    response = redirect(url_for('login'))
    unset_jwt_cookies(response)
    return response

@app.route('/blocked_links')
@login_required
def blocked_links():
    from database.db import Database
    import sqlite3

    db = Database()
    with sqlite3.connect(db.db_file) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM link_attempts
            ORDER BY timestamp DESC
            LIMIT 100
        """)
        link_attempts = cursor.fetchall()

    return render_template('blocked_links.html', link_attempts=link_attempts)

@app.route('/bad_words')
@login_required
def bad_words():
    db = Database()
    bad_words = db.get_bad_words()
    bad_word_attempts = db.get_bad_word_attempts()
    return render_template('bad_words.html', bad_words=bad_words, bad_word_attempts=bad_word_attempts)

@app.route('/bad_words/add', methods=['POST'])
@login_required
def add_bad_word():
    word = request.form.get('word')
    if not word:
        flash('Please provide a word to add.', 'error')
        return redirect(url_for('bad_words'))
    
    # Get the current user's ID (using 0 as a placeholder since we don't have user management)
    user_id = 0
    
    db = Database()
    db.add_bad_word(word, user_id)
    flash(f'Successfully added "{word}" to bad words list.', 'success')
    return redirect(url_for('bad_words'))

@app.route('/bad_words/remove', methods=['POST'])
@login_required
def remove_bad_word():
    word = request.form.get('word')
    if not word:
        flash('Please specify a word to remove.', 'error')
        return redirect(url_for('bad_words'))
    
    db = Database()
    db.remove_bad_word(word)
    flash(f'Successfully removed "{word}" from bad words list.', 'success')
    return redirect(url_for('bad_words'))

@app.route('/api/dashboard/stats')
@jwt_required()
def get_dashboard_stats():
    from database.db import Database
    from datetime import datetime, timedelta
    import sqlite3

    db = Database()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    # Get link blocks data
    with sqlite3.connect(db.db_file) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date(timestamp) as date, COUNT(*) as count
            FROM link_attempts
            WHERE timestamp >= ?
            GROUP BY date(timestamp)
            ORDER BY date
        """, (start_date,))
        link_blocks_data = cursor.fetchall()

        # Get bad words data
        cursor.execute("""
            SELECT date(timestamp) as date, COUNT(*) as count
            FROM bad_word_attempts
            WHERE timestamp >= ?
            GROUP BY date(timestamp)
            ORDER BY date
        """, (start_date,))
        bad_words_data = cursor.fetchall()

        # Get user activity data
        cursor.execute("""
            SELECT date(timestamp) as date, COUNT(*) as count
            FROM (
                SELECT timestamp FROM link_attempts WHERE timestamp >= ?
                UNION ALL
                SELECT timestamp FROM bad_word_attempts WHERE timestamp >= ?
            )
            GROUP BY date(timestamp)
            ORDER BY date
        """, (start_date, start_date))
        user_activity_data = cursor.fetchall()

    # Process data for charts
    dates = [(start_date + timedelta(days=x)).strftime('%Y-%m-%d') 
            for x in range(8)]

    def process_data(raw_data):
        data_dict = {row[0]: row[1] for row in raw_data}
        return {
            'labels': dates,
            'data': [data_dict.get(date, 0) for date in dates]
        }

    return jsonify({
        'linkBlocks': process_data(link_blocks_data),
        'badWords': process_data(bad_words_data),
        'userActivity': process_data(user_activity_data)
    })

if __name__ == '__main__':
    app.run(debug=True)