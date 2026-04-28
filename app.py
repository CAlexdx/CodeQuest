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

    # CONTROLE DE RESPOSTAS (ANTI-SPAM + NÃO REPETIR)
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS answered (
        user_id INTEGER,
        question_id INTEGER
    )
    """)

    cursor.execute("SELECT COUNT(*) FROM questions")
    if cursor.fetchone()[0] == 0:

        perguntas = [

            # ===== FÁCIL =====
            ("print('Hello') → saída?", "hello", 1, "text", None, None, None, None),

            ("Qual linguagem roda no navegador?", "javascript", 1, "multiple",
             "Python", "Java", "JavaScript", "C++"),

            ("Complete: print('____') → World", "world", 1, "cloze",
             None, None, None, None),

            # ===== MÉDIO =====
            ("numero = 10\nif numero % 2 == 0:\n print('Par')\nQual saída?", "par", 2, "multiple",
             "Ímpar", "Par", "Erro", "Nada"),

            ("Qual comando SQL seleciona dados?", "select", 2, "multiple",
             "INSERT", "SELECT", "DELETE", "DROP"),

            # ===== DIFÍCIL =====
            ("for i in range(3): print(i)", "0 1 2", 3, "text",
             None, None, None, None),

        ]

        cursor.executemany(
            f"""INSERT INTO questions 
            (question, answer, difficulty, type, opt1, opt2, opt3, opt4)
            VALUES ({p},{p},{p},{p},{p},{p},{p},{p})""",
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
# HOME (CORRIGIDO)
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

    if not user:
        return redirect("/logout")

    level = get_level(user[1])
    difficulty = get_difficulty(level)

    # 🔥 NÃO REPETE PERGUNTA JÁ RESPONDIDA
    cursor.execute(f"""
    SELECT * FROM questions 
    WHERE difficulty={p} 
    AND id NOT IN (
        SELECT question_id FROM answered WHERE user_id={p}
    )
    ORDER BY RANDOM()
    LIMIT 1
    """, (difficulty, session["user_id"]))

    q = cursor.fetchone()

    # se acabou perguntas, libera todas novamente
    if not q:
        cursor.execute(f"DELETE FROM answered WHERE user_id={p}", (session["user_id"],))
        conn.commit()

        cursor.execute(f"""
        SELECT * FROM questions 
        WHERE difficulty={p}
        ORDER BY RANDOM()
        LIMIT 1
        """, (difficulty,))
        q = cursor.fetchone()

    conn.close()

    return render_template("index.html",
        username=user[0],
        xp=user[1],
        xp_next=(level+1)*50,
        level=level,
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

    # BLOQUEIA SPAM
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

    cursor.execute(
        f"INSERT INTO answered (user_id, question_id) VALUES ({p},{p})",
        (session["user_id"], data["id"])
    )

    conn.commit()
    conn.close()

    return jsonify({"result":result,"correct_answer":correct})

# ==========================
# PROFILE
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

    return render_template("profile.html",
        username=user[0],
        xp=user[1],
        level=get_level(user[1])
    )

# ==========================
# RANKING
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

    users = [{"username": r[0], "xp": r[1]} for r in rows]

    return render_template("ranking.html", users=users)

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