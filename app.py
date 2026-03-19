import sqlite3
from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from init_db import init_db

app = Flask(__name__)
app.secret_key = "segredo_super"

init_db()

def get_db():
    return sqlite3.connect("database.db")

# HOME
@app.route("/")
def home():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT username, xp, is_admin FROM users WHERE id = ?", (session["user_id"],))
    user = cursor.fetchone()

    cursor.execute("SELECT * FROM questions ORDER BY RANDOM() LIMIT 1")
    question = cursor.fetchone()

    conn.close()

    return render_template("index.html", user=user, question=question)

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
    user_answer = request.form["answer"]
    question_id = request.form["question_id"]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT answer FROM questions WHERE id = ?", (question_id,))
    correct_answer = cursor.fetchone()[0]

    correct = int(user_answer.lower() == correct_answer.lower())

    if correct:
        cursor.execute("UPDATE users SET xp = xp + 10 WHERE id = ?", (session["user_id"],))

    conn.commit()
    conn.close()

    return redirect("/")

# ADMIN
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT is_admin FROM users WHERE id = ?", (session["user_id"],))
    is_admin = cursor.fetchone()[0]

    if not is_admin:
        conn.close()
        return "Acesso negado"

    # ADICIONAR PERGUNTA
    if request.method == "POST":
        question = request.form.get("question")
        answer = request.form.get("answer")

        if question and answer:
            cursor.execute("INSERT INTO questions (question, answer) VALUES (?, ?)", (question, answer))
            conn.commit()

    # DELETAR
    delete_id = request.args.get("delete")
    if delete_id:
        cursor.execute("DELETE FROM questions WHERE id = ?", (delete_id,))
        conn.commit()

    # LISTAR
    cursor.execute("SELECT * FROM questions")
    questions = cursor.fetchall()

    # USUÁRIOS
    cursor.execute("SELECT id, username, xp, is_admin FROM users")
    users = cursor.fetchall()

    conn.close()

    return render_template("admin.html", questions=questions, users=users)

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)