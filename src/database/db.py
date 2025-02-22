import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_file='bot.db'):
        self.db_file = db_file
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_admin BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Create link_attempts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS link_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    chat_id INTEGER,
                    link_text TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    action_taken TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')

            # Create bad_words table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bad_words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT UNIQUE NOT NULL,
                    added_by INTEGER,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (added_by) REFERENCES users(user_id)
                )
            ''')

            # Create bad_word_attempts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bad_word_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    chat_id INTEGER,
                    message_text TEXT,
                    matched_word TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    action_taken TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            conn.commit()

    def add_or_update_user(self, user_id: int, username: str = None, is_admin: bool = False):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, username, is_admin)
                VALUES (?, ?, ?)
            ''', (user_id, username, is_admin))
            conn.commit()

    def log_link_attempt(self, user_id: int, chat_id: int, link_text: str, action_taken: str):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO link_attempts (user_id, chat_id, link_text, action_taken, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, chat_id, link_text, action_taken, datetime.now()))
            conn.commit()

    def get_user_attempts(self, user_id: int, chat_id: int = None, hours: int = 24) -> int:
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            if chat_id:
                cursor.execute('''
                    SELECT COUNT(*) FROM (
                        SELECT timestamp FROM link_attempts
                        WHERE user_id = ? AND chat_id = ? AND
                        timestamp > datetime('now', '-' || ? || ' hours')
                        UNION ALL
                        SELECT timestamp FROM bad_word_attempts
                        WHERE user_id = ? AND chat_id = ? AND
                        timestamp > datetime('now', '-' || ? || ' hours')
                    )
                ''', (user_id, chat_id, hours, user_id, chat_id, hours))
            else:
                cursor.execute('''
                    SELECT COUNT(*) FROM (
                        SELECT timestamp FROM link_attempts
                        WHERE user_id = ? AND
                        timestamp > datetime('now', '-' || ? || ' hours')
                        UNION ALL
                        SELECT timestamp FROM bad_word_attempts
                        WHERE user_id = ? AND
                        timestamp > datetime('now', '-' || ? || ' hours')
                    )
                ''', (user_id, hours, user_id, hours))
            return cursor.fetchone()[0]

    def add_bad_word(self, word: str, added_by: int):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO bad_words (word, added_by)
                VALUES (?, ?)
            ''', (word.lower(), added_by))
            conn.commit()

    def remove_bad_word(self, word: str):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM bad_words WHERE word = ?', (word.lower(),))
            conn.commit()

    def get_bad_words(self) -> list:
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT word, added_by, datetime(added_at, 'localtime') as added_at
                FROM bad_words
                ORDER BY added_at DESC
            ''')
            return [{
                'word': row[0],
                'added_by': row[1],
                'added_at': row[2]
            } for row in cursor.fetchall()]

    def log_bad_word_attempt(self, user_id: int, chat_id: int, message_text: str, matched_word: str, action_taken: str):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO bad_word_attempts (user_id, chat_id, message_text, matched_word, action_taken, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, chat_id, message_text, matched_word, action_taken, datetime.now()))
            conn.commit()
    def get_bad_word_attempts(self) -> list:
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_id, chat_id, message_text, matched_word, action_taken,
                       datetime(timestamp, 'localtime') as timestamp
                FROM bad_word_attempts
                ORDER BY timestamp DESC
                LIMIT 100
            ''')
            return [{
                'user_id': row[0],
                'chat_id': row[1],
                'message_text': row[2],
                'matched_word': row[3],
                'action_taken': row[4],
                'timestamp': row[5]
            } for row in cursor.fetchall()]