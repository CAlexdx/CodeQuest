import os
import sqlite3
import unicodedata
from flask import Flask, render_template, request, redirect, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "segredo_super")

# ==========================
# DATABASE
# ==========================

def get_db():
    db_url = os.environ.get("DATABASE_URL")

    if db_url:
        import psycopg2
        return psycopg2.connect(db_url)
    else:
        return sqlite3.connect("database.db")

def get_placeholder():
    return "%s" if os.environ.get("DATABASE_URL") else "?"

# ==========================
# INIT DB
# ==========================

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    p = get_placeholder()

    # USERS
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS users (
        id {"SERIAL PRIMARY KEY" if p=="%s" else "INTEGER PRIMARY KEY AUTOINCREMENT"},
        username TEXT UNIQUE,
        password TEXT,
        xp INTEGER DEFAULT 0,
        is_admin BOOLEAN DEFAULT FALSE
    )
    """)

    # QUESTIONS
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS questions (
        id {"SERIAL PRIMARY KEY" if p=="%s" else "INTEGER PRIMARY KEY AUTOINCREMENT"},
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

    # PREVENIR SPAM DE XP
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS answered (
        user_id INTEGER,
        question_id INTEGER
    )
    """)

    cursor.execute("SELECT COUNT(*) FROM questions")
    if cursor.fetchone()[0] == 0:
        perguntas = [
            ("print('Hello World') → saída?", "hello world", 1, "text", None, None, None, None),
            ("Qual comando cria uma tabela no SQL?", "create table", 1, "multiple",
             "CREATE TABLE", "INSERT", "SELECT", "DROP"),
        ]

        cursor.executemany(
            f"INSERT INTO questions (question, answer, difficulty, type, opt1, opt2, opt3, opt4) VALUES ({p},{p},{p},{p},{p},{p},{p},{p})",
            perguntas
        )

    conn.commit()
    conn.close()

init_db()

# ==========================
# FUNÇÕES
# ==========================

def get_level(xp):
    return xp // 50

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
    p = get_placeholder()

    cursor.execute(f"SELECT username, xp FROM users WHERE id={p}", (session["user_id"],))
    user = cursor.fetchone()

    cursor.execute("SELECT * FROM questions ORDER BY RANDOM() LIMIT 1")
    q = cursor.fetchone()

    conn.close()

    return render_template("index.html",
        username=user[0],
        xp=user[1],
        xp_next=(get_level(user[1])+1)*50,
        level=get_level(user[1]),
        question={
            "id": q[0],
            "question": q[1],
            "type": q[4],
            "options": [q[5], q[6], q[7], q[8]]
        }
    )

# ==========================
# REGISTER
# ==========================

@app.route("/register", methods=["GET","POST"])
def register():
    error=None

    if request.method=="POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        if not username or not password:
            error = "Preencha todos os campos"
            return render_template("register.html", error=error)

        conn=get_db()
        cursor=conn.cursor()
        p=get_placeholder()

        try:
            cursor.execute(
                f"INSERT INTO users (username,password) VALUES ({p},{p})",
                (username, generate_password_hash(password))
            )
            conn.commit()
            return redirect("/login")
        except:
            error="Usuário já existe"

        conn.close()

    return render_template("register.html", error=error)

# ==========================
# LOGIN
# ==========================

@app.route("/login", methods=["GET","POST"])
def login():
    error=None

    if request.method=="POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        if not username or not password:
            error="Preencha todos os campos"
            return render_template("login.html", error=error)

        conn=get_db()
        cursor=conn.cursor()
        p=get_placeholder()

        cursor.execute(
            f"SELECT id,password FROM users WHERE username={p}",
            (username,)
        )
        user=cursor.fetchone()
        conn.close()

        if not user:
            error="Usuário não existe"
        elif not check_password_hash(user[1], password):
            error="Senha incorreta"
        else:
            session["user_id"]=user[0]
            return redirect("/")

    return render_template("login.html", error=error)

# ==========================
# ANSWER (ANTI-SPAM)
# ==========================

@app.route("/answer", methods=["POST"])
def answer():
    if "user_id" not in session:
        return jsonify({"error":"não autorizado"}), 403

    data=request.get_json()

    conn=get_db()
    cursor=conn.cursor()
    p=get_placeholder()

    # Verificar se já respondeu
    cursor.execute(
        f"SELECT * FROM answered WHERE user_id={p} AND question_id={p}",
        (session["user_id"], data["id"])
    )

    if cursor.fetchone():
        return jsonify({"result":"already_answered"})

    cursor.execute(f"SELECT answer FROM questions WHERE id={p}", (data["id"],))
    correct=cursor.fetchone()[0]

    if normalize(data["answer"])==normalize(correct):
        cursor.execute(f"UPDATE users SET xp=xp+10 WHERE id={p}", (session["user_id"],))
        result="correct"
    else:
        result="wrong"

    # Registrar resposta
    cursor.execute(
        f"INSERT INTO answered (user_id, question_id) VALUES ({p},{p})",
        (session["user_id"], data["id"])
    )

    conn.commit()
    conn.close()

    return jsonify({"result":result,"correct_answer":correct})

# ==========================
# PROFILE (CORRIGIDO)
# ==========================

@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()
    p = get_placeholder()

    cursor.execute(f"SELECT username, xp FROM users WHERE id={p}", (session["user_id"],))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return redirect("/logout")

    return render_template("profile.html",
        username=user[0],
        xp=user[1],
        level=get_level(user[1])
    )

# ==========================
# RANKING (CORRIGIDO)
# ==========================

@app.route("/ranking")
def ranking():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT username, xp FROM users ORDER BY xp DESC LIMIT 10")
    rows = cursor.fetchall()

    conn.close()

    # 🔥 transforma em dict (resolve bug de index)
    users = []
    for r in rows:
        users.append({
            "username": r[0],
            "xp": r[1]
        })

    return render_template("ranking.html", users=users)
# ==========================
# ADMIN
# ==========================

@app.route("/admin")
def admin():
    if "user_id" not in session:
        return redirect("/login")

    conn=get_db()
    cursor=conn.cursor()
    p=get_placeholder()

    cursor.execute(f"SELECT is_admin FROM users WHERE id={p}", (session["user_id"],))
    if not cursor.fetchone()[0]:
        return "Acesso negado"

    cursor.execute("SELECT id,username,xp FROM users ORDER BY xp DESC")
    users=cursor.fetchall()

    conn.close()
    return render_template("admin.html", users=users)

@app.route("/delete_user/<int:id>")
def delete_user(id):
    conn=get_db()
    cursor=conn.cursor()
    p=get_placeholder()

    cursor.execute(f"DELETE FROM users WHERE id={p}", (id,))
    conn.commit()
    conn.close()

    return redirect("/admin")

# ==========================
# LOGOUT
# ==========================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ==========================

if __name__=="__main__":
    app.run(debug=True)