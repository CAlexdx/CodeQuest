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


@app.route("/")
def index():
    question = get_question()
    return render_template("index.html", question=question)


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

    conn.close()

    if user_answer == correct_answer:
        return jsonify({"result": "correct"})
    else:
        return jsonify({"result": "wrong"})


if __name__ == "__main__":
    app.run(debug=True)