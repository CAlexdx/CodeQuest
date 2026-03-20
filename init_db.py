import sqlite3

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # USERS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        xp INTEGER DEFAULT 0
    )
    """)

    # QUESTIONS COM TIPO
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT,
    answer TEXT,
    difficulty INTEGER,
    type TEXT,
    option1 TEXT,
    option2 TEXT,
    option3 TEXT,
    option4 TEXT
)
""")

    cursor.execute("SELECT COUNT(*) FROM questions")
    count = cursor.fetchone()[0]

    if count == 0:
        perguntas = [
                # TEXTO
                ('print("Hello World") -> saída?', "Hello World", 1, "text", None, None, None, None),

                ('numero = 10\nif numero % 2 == 0:\n print("Par")\nelse:\n print("Ímpar")\nSaída?', "Par", 1, "text", None, None, None, None),

                # MÚLTIPLA ESCOLHA
                ('Qual será a saída?\nprint(2 + 2)', "4", 1, "multiple", "2", "4", "22", "0"),

                ('Qual linguagem roda no navegador?', "JavaScript", 1, "multiple", "Python", "Java", "JavaScript", "C++"),

                ('Qual comando SQL pega tudo?', "*", 2, "multiple", "ALL", "*", "SELECT", "FROM"),

                ('Qual palavra define função em Python?', "def", 2, "multiple", "function", "def", "func", "lambda"),

                # DIFÍCIL
                ('for i in range(3): print(i)\nSaída?', "0 1 2", 3, "text", None, None, None, None)

]

        cursor.executemany(
            """INSERT INTO questions 
            (question, answer, difficulty, type, option1, option2, option3, option4) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            perguntas
            )
        

    conn.commit()
    conn.close()