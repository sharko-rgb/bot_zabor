import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('zabory72.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform TEXT,
        user_id INTEGER,
        username TEXT,
        full_name TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        type TEXT,
        data TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()

def save_user(platform, user_id, username, full_name):
    conn = sqlite3.connect('zabory72.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (platform, user_id, username, full_name) VALUES (?, ?, ?, ?)',
                   (platform, user_id, username, full_name))
    conn.commit()
    conn.close()

def save_request(user_id, request_type, data):
    conn = sqlite3.connect('zabory72.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO requests (user_id, type, data) VALUES (?, ?, ?)',
                   (user_id, request_type, data))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect('zabory72.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user
