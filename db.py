import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DB_NAME = 'files.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                download_url TEXT NOT NULL,
                rating INTEGER DEFAULT 0,
                uploader_id INTEGER,
                FOREIGN KEY (uploader_id) REFERENCES users(id)
            )
        ''')
        conn.commit()

def insert_user(username, password):
    password_hash = generate_password_hash(password)
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
        conn.commit()

def get_user_by_username(username):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        return c.fetchone()

def insert_file(title, description, download_url, uploader_id):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO files (title, description, download_url, uploader_id)
            VALUES (?, ?, ?, ?)
        ''', (title, description, download_url, uploader_id))
        conn.commit()

def get_all_files():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT files.*, users.username AS uploader
            FROM files
            LEFT JOIN users ON files.uploader_id = users.id
            ORDER BY rating DESC
        ''')
        return c.fetchall()

def rate_file(file_id):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('UPDATE files SET rating = rating + 1 WHERE id = ?', (file_id,))
        conn.commit()
