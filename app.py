import os
import sqlite3
import unicodedata
from flask import Flask, render_template, request, redirect, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "segredo_super")

# ==========================
# DATABASE (AUTO SQLITE / POSTGRES)
# ==========================

def get_db():
    db_url = os.environ.get("DATABASE_URL")

    if db_url:
        import psycopg2
        conn = psycopg2.connect(db_url)
    else:
        conn = sqlite3.connect("database.db")

    return conn


def get_placeholder():
    if os.environ.get("DATABASE_URL"):
        return "%s"
    return "?"


# ==========================
# INIT DB (FUNCIONA NOS DOIS)
# ==========================

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    is_postgres = os.environ.get("DATABASE_URL")

    # USERS
    if is_postgres:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            xp INTEGER DEFAULT 0
        )
        """)
    else:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            xp INTEGER DEFAULT 0
        )
        """)

    # QUESTIONS
    if is_postgres:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id SERIAL PRIMARY KEY,
            question TEXT,
            answer TEXT,
            difficulty INTEGER,
            type TEXT,
            opt1 TEXT,
            opt2 TEXT,
            opt3 TEXT,
            opt4 TEXT
        )
        """)
    else:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            answer TEXT,
            difficulty INTEGER,
            type TEXT,
            opt1 TEXT,
            opt2 TEXT,
            opt3 TEXT,
            opt4 TEXT
        )
        """)

    # INSERIR PERGUNTAS SE VAZIO
    cursor.execute("SELECT COUNT(*) FROM questions")
    count = cursor.fetchone()[0]

    if count == 0:
        perguntas = [
            ("print('Hello World') → saída?", "hello world", 1, "text", None, None, None, None),
            ("Qual comando cria uma tabela no SQL?", "create table", 1, "multiple",
             "CREATE TABLE", "INSERT", "SELECT", "DROP"),
            ("Complete: print('_____') → World", "world", 1, "cloze", None, None, None, None),
            ("Monte: print('Hello World')", "print hello world", 1, "wordbank",
             "print", "hello", "world", None),
        ]

        placeholder = get_placeholder()

        cursor.executemany(
            f"INSERT INTO questions (question, answer, difficulty, type, opt1, opt2, opt3, opt4) VALUES ({placeholder},{placeholder},{placeholder},{placeholder},{placeholder},{placeholder},{placeholder},{placeholder})",
            perguntas
        )

    conn.commit()
    conn.close()


init_db()

# ==========================
# FUNÇÕES AUX
# ==========================

def get_level(xp):
    return xp // 50

def get_difficulty(level):
    if level < 2:
        return 1
    elif level < 4:
        return 2
    else:
        return 3

def normalize(text):
    return ''.join(
        c for c in unicodedata.normalize('NFD', text.lower().strip())
        if unicodedata.category(c) != 'Mn'
    )

# ==========================
# ROTAS
# ==========================

@app.route("/")
def home():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    placeholder = get_placeholder()

    cursor.execute(f"SELECT username, xp FROM users WHERE id = {placeholder}", (session["user_id"],))
    user = cursor.fetchone()

    if not user:
        session.clear()
        return redirect("/login")

    xp = user[1]
    level = get_level(xp)
    difficulty = get_difficulty(level)
    xp_next = (level + 1) * 50

    cursor.execute(
        f"SELECT * FROM questions WHERE difficulty = {placeholder} ORDER BY RANDOM() LIMIT 1",
        (difficulty,)
    )
    question = cursor.fetchone()

    conn.close()

    return render_template("index.html",
        username=user[0],
        xp=xp,
        xp_next=xp_next,
        level=level,
        question={
            "id": question[0],
            "question": question[1],
            "type": question[4],
            "options": [question[5], question[6], question[7], question[8]]
        }
    )

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if not username or not password:
            error = "Preencha todos os campos"
        else:
            conn = get_db()
            cursor = conn.cursor()
            placeholder = get_placeholder()

            try:
                cursor.execute(
                    f"INSERT INTO users (username, password) VALUES ({placeholder}, {placeholder})",
                    (username, generate_password_hash(password))
                )
                conn.commit()
                conn.close()
                return redirect("/login")
            except:
                error = "Usuário já existe"

    return render_template("register.html", error=error)

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()
        placeholder = get_placeholder()

        cursor.execute(
            f"SELECT id, password FROM users WHERE username = {placeholder}",
            (username,)
        )
        user = cursor.fetchone()
        conn.close()

        if not user:
            error = "Usuário não existe"
        elif not check_password_hash(user[1], password):
            error = "Senha incorreta"
        else:
            session["user_id"] = user[0]
            return redirect("/")

    return render_template("login.html", error=error)

@app.route("/answer", methods=["POST"])
def answer():
    data = request.get_json()

    conn = get_db()
    cursor = conn.cursor()
    placeholder = get_placeholder()

    cursor.execute(
        f"SELECT answer FROM questions WHERE id = {placeholder}",
        (data["id"],)
    )
    correct_answer = cursor.fetchone()[0]

    correct = normalize(data["answer"]) == normalize(correct_answer)

    if correct:
        cursor.execute(
            f"UPDATE users SET xp = xp + 10 WHERE id = {placeholder}",
            (session["user_id"],)
        )

    conn.commit()
    conn.close()

    return jsonify({
        "result": "correct" if correct else "wrong",
        "correct_answer": correct_answer
    })

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)