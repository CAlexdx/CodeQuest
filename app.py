import sqlite3
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

# HOME
@app.route("/")
def home():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT username, xp FROM users WHERE id = ?", (session["user_id"],))
    user = cursor.fetchone()

    level = get_level(user[1])
    difficulty = get_difficulty(level)

    # PEGA PERGUNTA BASEADA NO NÍVEL
    cursor.execute(
        "SELECT * FROM questions WHERE difficulty = ? ORDER BY RANDOM() LIMIT 1",
        (difficulty,)
    )
    question = cursor.fetchone()

    conn.close()

    return render_template("index.html",
        username=user[0],
        xp=user[1],
        level=level,
        question={
            "id": question[0],
            "question": question[1]
        }
    )

# REGISTRO
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
        except:
            return "Usuário já existe"

        conn.close()
        return redirect("/login")

    return render_template("register.html")

# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        conn.close()

        if user and check_password_hash(user[1], password):
            session["user_id"] = user[0]
            return redirect("/")

        return "Login inválido"

    return render_template("login.html")

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

    correct = user_answer.strip().lower() == correct_answer.strip().lower()

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

    level = get_level(user[1])

    return render_template("profile.html",
        username=user[0],
        xp=user[1],
        level=level
    )

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)