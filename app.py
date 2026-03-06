from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

def get_question():

    conn = sqlite3.connect("database.db")

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM questions LIMIT 1")

    question = cursor.fetchone()

    conn.close()

    return question


@app.route("/")
def index():

    question = get_question()

    return render_template("index.html", q=question)


app.run(debug=True)
