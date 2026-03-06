from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

def criar_banco():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pergunta TEXT,
        opcao1 TEXT,
        opcao2 TEXT,
        opcao3 TEXT,
        resposta TEXT
    )
    """)

    cursor.execute("SELECT COUNT(*) FROM questions")
    total = cursor.fetchone()[0]

    if total == 0:

        cursor.execute("""
        INSERT INTO questions
        (pergunta, opcao1, opcao2, opcao3, resposta)

        VALUES
        (
        'O que imprime texto em Python?',
        'print()',
        'input()',
        'var()',
        'print()'
        )
        """)

    conn.commit()
    conn.close()


def pegar_pergunta():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM questions LIMIT 1")

    pergunta = cursor.fetchone()

    conn.close()

    return pergunta


@app.route("/")
def index():

    criar_banco()

    pergunta = pegar_pergunta()

    return render_template("index.html", q=pergunta)


app.run(debug=True)