import os
import unicodedata
import sqlite3
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


def normalize(text):
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    ).lower().strip()


def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def get_question():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM questions ORDER BY RANDOM() LIMIT 1")
    question = cursor.fetchone()

    conn.close()
    return question


def get_user():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE id = 1")
    user = cursor.fetchone()

    conn.close()
    return user


def get_level(xp):
    return xp // 100 + 1


@app.route("/")
def index():
    question = get_question()
    user = get_user()
    level = get_level(user["xp"])

    return render_template(
        "index.html",
        question=question,
        xp=user["xp"],
        level=level
    )


@app.route("/answer", methods=["POST"])
def answer():

    data = request.json
    question_id = data["id"]
    user_answer = normalize(data["answer"])

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT answer FROM questions WHERE id=?",
        (question_id,)
    )

    correct_answer = normalize(cursor.fetchone()["answer"])

    result = "wrong"

    if user_answer == correct_answer:
        result = "correct"

        cursor.execute(
            "UPDATE users SET xp = xp + 10 WHERE id = 1"
        )

    conn.commit()
    conn.close()

    return jsonify({"result": result})


@app.route("/ranking")
def ranking():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT username, xp FROM users ORDER BY xp DESC"
    )

    users = cursor.fetchall()

    conn.close()

    return render_template("ranking.html", users=users)


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )