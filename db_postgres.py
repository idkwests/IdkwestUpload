import os
import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE_URL = os.environ['DATABASE_URL']

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    return conn

def init_db():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                download_url TEXT NOT NULL,
                rating INTEGER DEFAULT 0,
                uploader_id INTEGER REFERENCES users(id)
            )
        ''')

def insert_user(username, password):
    password_hash = generate_password_hash(password)
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            'INSERT INTO users (username, password_hash) VALUES (%s, %s)',
            (username, password_hash)
        )

def get_user_by_username(username):
    with get_db_connection() as conn:
        c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        c.execute('SELECT * FROM users WHERE username = %s', (username,))
        return c.fetchone()

def insert_file(title, description, download_url, uploader_id):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            '''
            INSERT INTO files (title, description, download_url, uploader_id)
            VALUES (%s, %s, %s, %s)
            ''',
            (title, description, download_url, uploader_id)
        )

def get_all_files():
    with get_db_connection() as conn:
        c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
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
        c.execute('UPDATE files SET rating = rating + 1 WHERE id = %s', (file_id,))

def get_user_by_id(user_id):
    with get_db_connection() as conn:
        c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        c.execute('SELECT * FROM users WHERE id = %s', (user_id,))
        return c.fetchone()

def get_user_files(user_id):
    with get_db_connection() as conn:
        c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        c.execute(
            'SELECT * FROM files WHERE uploader_id = %s ORDER BY id DESC',
            (user_id,)
        )
        return c.fetchall()
