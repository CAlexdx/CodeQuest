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

    # QUESTIONS (AGORA COM DIFICULDADE)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        answer TEXT,
        difficulty INTEGER
    )
    """)

    # INSERIR PERGUNTAS SE NÃO EXISTIR
    cursor.execute("SELECT COUNT(*) FROM questions")
    count = cursor.fetchone()[0]

    if count == 0:
        perguntas = [
            # FÁCIL (1)
            ("Quanto é 2 + 2?", "4", 1),
            ("Capital do Brasil?", "Brasilia", 1),
            ("Quanto é 10 / 2?", "5", 1),

            # MÉDIO (2)
            ("Quanto é 15 * 3?", "45", 2),
            ("Linguagem usada no navegador?", "JavaScript", 2),

            # DIFÍCIL (3)
            ("Quanto é 12 * 12?", "144", 3),
            ("Quem criou o Python?", "Guido van Rossum", 3)
        ]

        cursor.executemany(
            "INSERT INTO questions (question, answer, difficulty) VALUES (?, ?, ?)",
            perguntas
        )

    conn.commit()
    conn.close()