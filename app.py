import sqlite3
import unicodedata
from flask import Flask, render_template, request, redirect, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from init_db import init_db

app = Flask(__name__)
app.secret_key = "segredo_super"

init_db()

def get_db():
    return sqlite3.connect("database.db")

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

# HOME
@app.route("/")
def home():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT username, xp FROM users WHERE id = ?", (session["user_id"],))
    user = cursor.fetchone()

    xp = user[1]
    level = get_level(xp)
    difficulty = get_difficulty(level)
    xp_next = (level + 1) * 50

    # PERGUNTA BASEADA NO NÍVEL
    cursor.execute(
        "SELECT * FROM questions WHERE difficulty = ? ORDER BY RANDOM() LIMIT 1",
        (difficulty,)
    )
    question = cursor.fetchone()

    conn.close()

    # proteção caso não tenha pergunta
    if not question:
        return "Sem perguntas cadastradas para esse nível"

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

# REGISTRO
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

# LOGIN
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
            elif not check_password_hash(user[1], password):
                error = "Senha incorreta"
            else:
                session["user_id"] = user[0]
                return redirect("/")

    return render_template("login.html", error=error)

# RESPONDER
@app.route("/answer", methods=["POST"])
def answer():
    data = request.get_json()

    user_answer = data["answer"]
    question_id = data["id"]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT answer FROM questions WHERE id = ?", (question_id,))
    correct_answer = cursor.fetchone()[0]

    correct = normalize(user_answer) == normalize(correct_answer)

    if correct:
        cursor.execute("UPDATE users SET xp = xp + 10 WHERE id = ?", (session["user_id"],))

    conn.commit()
    conn.close()

    return jsonify({"result": "correct" if correct else "wrong"})

# PROFILE
@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT username, xp FROM users WHERE id = ?", (session["user_id"],))
    user = cursor.fetchone()

    conn.close()

    xp = user[1]
    level = get_level(xp)
    xp_next = (level + 1) * 50

    return render_template("profile.html",
        username=user[0],
        xp=xp,
        xp_next=xp_next,
        level=level
    )

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)