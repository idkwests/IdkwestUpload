from flask import Flask, render_template, request, redirect, url_for, session, flash
import os, tempfile, json
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from functools import wraps
import db

db.init_db()

app = Flask(__name__)
app.secret_key = 'whatasecretidkwestkey132'  

# //// Auth Decorator ////
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# //// Google Drive Setup ////
with open('credentials.json') as f:
    creds_json = json.load(f)

creds = service_account.Credentials.from_service_account_info(creds_json)
drive_service = build('drive', 'v3', credentials=creds)

# //// Routes ////
@app.route('/')
def index():
    files = db.get_all_files()
    return render_template('index.html', files=files)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm_password']

        if password != confirm:
            flash('Passwords do not match.')
            return redirect(url_for('register'))

        if db.get_user_by_username(username):
            flash('Username already exists.')
            return redirect(url_for('register'))

        db.insert_user(username, password)
        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = db.get_user_by_username(username)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Logged in successfully.')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('Logged out successfully.')
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        file = request.files['file']

        if not file or file.filename == '':
            flash('No file selected.')
            return redirect(url_for('upload'))

        filename = secure_filename(file.filename)
        temp_path = os.path.join(tempfile.gettempdir(), filename)
        file.save(temp_path)

        try:
            media = MediaFileUpload(temp_path, resumable=False)
            uploaded = drive_service.files().create(
                media_body=media,
                body={"name": filename},
                fields="id"
            ).execute()

            file_id = uploaded['id']

            drive_service.permissions().create(
                fileId=file_id,
                body={'role': 'reader', 'type': 'anyone'}
            ).execute()

            download_url = f"https://drive.google.com/uc?id={file_id}&export=download"

            db.insert_file(title, description, download_url, session['user_id'])

            flash('File uploaded successfully.')

        finally:
            try:
                os.remove(temp_path)
            except Exception:
                pass

        return redirect(url_for('index'))

    return render_template('upload.html')

@app.route('/rate/<int:file_id>', methods=['POST'])
@login_required
def rate(file_id):
    db.rate_file(file_id)
    flash('Thanks for your rating!')
    return redirect(url_for('index'))

@app.context_processor
def inject_user():
    return dict(logged_in=('user_id' in session))

@app.route('/account')
@login_required
def account():
    user_id = session['user_id']
    user = db.get_user_by_id(user_id)
    files = db.get_user_files(user_id)
    return render_template('account.html', user=user, files=files)


