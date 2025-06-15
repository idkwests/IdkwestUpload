import os
import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE_URL = os.environ['DATABASE_URL']

# Connect to the PostgreSQL database
def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    return conn

# Initialize the database tables
def init_db():
    with get_db_connection() as conn:
        c = conn.cursor()
        # Existing table creation code...
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
        # Run migration for new columns
        c.execute("ALTER TABLE files ADD COLUMN IF NOT EXISTS is_private BOOLEAN DEFAULT FALSE")
        c.execute("ALTER TABLE files ADD COLUMN IF NOT EXISTS password_hash TEXT")

# Insert a new user
def insert_user(username, password):
    password_hash = generate_password_hash(password)
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            'INSERT INTO users (username, password_hash) VALUES (%s, %s)',
            (username, password_hash)
        )

# Get a user by their username
def get_user_by_username(username):
    with get_db_connection() as conn:
        c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        c.execute('SELECT * FROM users WHERE username = %s', (username,))
        return c.fetchone()

# Insert a new file (supports optional private/password fields)
def insert_file(title, description, download_url, uploader_id, is_private=False, password=None):
    password_hash = generate_password_hash(password) if is_private and password else None
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            '''
            INSERT INTO files (title, description, download_url, uploader_id, is_private, password_hash)
            VALUES (%s, %s, %s, %s, %s, %s)
            ''',
            (title, description, download_url, uploader_id, is_private, password_hash)
        )

# Retrieve all files with uploader usernames
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

# Increment rating on a file
def rate_file(file_id):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('UPDATE files SET rating = rating + 1 WHERE id = %s', (file_id,))

# Get user by their ID
def get_user_by_id(user_id):
    with get_db_connection() as conn:
        c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        c.execute('SELECT * FROM users WHERE id = %s', (user_id,))
        return c.fetchone()

# Get all files uploaded by a specific user
def get_user_files(user_id):
    with get_db_connection() as conn:
        c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        c.execute(
            'SELECT * FROM files WHERE uploader_id = %s ORDER BY id DESC',
            (user_id,)
        )
        return c.fetchall()

# Get file by ID
def get_file_by_id(file_id):
    with get_db_connection() as conn:
        c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        c.execute('SELECT * FROM files WHERE id = %s', (file_id,))
        return c.fetchone()

# Validate a password for a private file
def validate_file_password(file_id, password_input):
    file = get_file_by_id(file_id)
    if file and file['is_private']:
        return check_password_hash(file['password_hash'], password_input)
    return False

