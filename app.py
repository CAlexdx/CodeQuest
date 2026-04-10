import sqlite3
import unicodedata
import random
from flask import Flask, render_template, request, redirect, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from init_db import init_db

app = Flask(__name__)
app.secret_key = "segredo_super"

# Inicializa banco
init_db()

# CONEXÃO OTIMIZADA
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# NÍVEL
def get_level(xp):
    return xp // 50

# DIFICULDADE
def get_difficulty(level):
    if level < 2:
        return 1
    elif level < 4:
        return 2
    else:
        return 3

# NORMALIZA TEXTO (remove acento e case)
def normalize(text):
    return ''.join(
        c for c in unicodedata.normalize('NFD', text.lower().strip())
        if unicodedata.category(c) != 'Mn'
    )

# =========================
# HOME
# =========================
@app.route("/")
def home():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT username, xp FROM users WHERE id = ?", (session["user_id"],))
    user = cursor.fetchone()

    xp = user["xp"]
    level = get_level(xp)
    difficulty = get_difficulty(level)
    xp_next = (level + 1) * 50

    # CONTAR QUESTÕES
    cursor.execute(
        "SELECT COUNT(*) FROM questions WHERE difficulty = ?",
        (difficulty,)
    )
    count = cursor.fetchone()[0]

    if count == 0:
        conn.close()
        return "Sem perguntas para esse nível"

    # PEGAR QUESTÃO LEVE (SEM RANDOM PESADO)
    offset = random.randint(0, max(count - 1, 0))

    cursor.execute(
        "SELECT * FROM questions WHERE difficulty = ? LIMIT 1 OFFSET ?",
        (difficulty, offset)
    )
    question = cursor.fetchone()

    conn.close()

    return render_template("index.html",
        username=user["username"],
        xp=xp,
        xp_next=xp_next,
        level=level,
        question={
            "id": question["id"],
            "question": question["question"],
            "type": question["type"],
            "options": [
                question["option1"],
                question["option2"],
                question["option3"],
                question["option4"]
            ]
        }
    )

# =========================
# REGISTER
# =========================
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

            try:
                cursor.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    (username, generate_password_hash(password))
                )
                conn.commit()
                conn.close()
                return redirect("/login")
            except:
                error = "Usuário já existe"

    return render_template("register.html", error=error)

# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if not username or not password:
            error = "Preencha todos os campos"
        else:
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute("SELECT id, password FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()

            conn.close()

            if not user:
                error = "Usuário não existe"
            elif not check_password_hash(user["password"], password):
                error = "Senha incorreta"
            else:
                session["user_id"] = user["id"]
                return redirect("/")

    return render_template("login.html", error=error)

# =========================
# ANSWER (API)
# =========================
@app.route("/answer", methods=["POST"])
def answer():
    if "user_id" not in session:
        return jsonify({"result": "error"})

    data = request.get_json()

    user_answer = data["answer"]
    question_id = data["id"]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT answer, explanation FROM questions WHERE id = ?", (question_id,))
    row = cursor.fetchone()

    correct_answer = row["answer"]
    explanation = row["explanation"]

    correct = normalize(user_answer) == normalize(correct_answer)

    if correct:
        cursor.execute(
            "UPDATE users SET xp = xp + 10 WHERE id = ?",
            (session["user_id"],)
        )

    # SALVAR HISTÓRICO
    cursor.execute("""
        INSERT INTO user_answers (user_id, question_id, is_correct)
        VALUES (?, ?, ?)
    """, (session["user_id"], question_id, int(correct)))

    conn.commit()
    conn.close()

    return jsonify({
        "result": "correct" if correct else "wrong",
        "correct_answer": correct_answer,
        "explanation": explanation
    })

# =========================
# PROFILE
# =========================
@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT username, xp FROM users WHERE id = ?", (session["user_id"],))
    user = cursor.fetchone()

    conn.close()

    xp = user["xp"]
    level = get_level(xp)
    xp_next = (level + 1) * 50

    return render_template("profile.html",
        username=user["username"],
        xp=xp,
        xp_next=xp_next,
        level=level
    )

# =========================
# RANKING
# =========================
@app.route("/ranking")
def ranking():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT username, xp 
        FROM users 
        ORDER BY xp DESC 
        LIMIT 10
    """)
    users = cursor.fetchall()

    conn.close()

    return render_template("ranking.html", users=users)

# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run()