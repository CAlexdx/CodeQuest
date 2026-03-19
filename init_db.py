import sqlite3
from werkzeug.security import generate_password_hash

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # USERS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        xp INTEGER DEFAULT 0,
        is_admin INTEGER DEFAULT 0
    )
    """)

    # QUESTIONS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        answer TEXT
    )
    """)

    # USER ANSWERS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_answers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        question_id INTEGER,
        user_answer TEXT,
        correct INTEGER
    )
    """)

    # CRIAR ADMIN PADRÃO
    admin_username = "admin"
    admin_password = generate_password_hash("123456")

    cursor.execute("SELECT * FROM users WHERE username = ?", (admin_username,))
    user = cursor.fetchone()

    if not user:
        cursor.execute("""
        INSERT INTO users (username, password, is_admin)
        VALUES (?, ?, 1)
        """, (admin_username, admin_password))
        print("Admin criado: admin / 123456")

    conn.commit()
    conn.close()