import sqlite3
from werkzeug.security import generate_password_hash

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # USERS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        xp INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # QUESTIONS (AGORA MELHOR)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        difficulty INTEGER NOT NULL,
        type TEXT NOT NULL,
        option1 TEXT,
        option2 TEXT,
        option3 TEXT,
        option4 TEXT,
        explanation TEXT
    )
    """)

    # HISTÓRICO (IMPORTANTE PRA FUTURO)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_answers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        question_id INTEGER,
        is_correct INTEGER,
        answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # PERFORMANCE (MUITO IMPORTANTE)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_xp ON users(xp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions(difficulty)")

    # INSERIR PERGUNTAS SE VAZIO
    cursor.execute("SELECT COUNT(*) FROM questions")
    if cursor.fetchone()[0] == 0:

        perguntas = [

            # FÁCIL
            ('print("Hello")', "Hello", 1, "text", None, None, None, None, "print exibe texto na tela"),

            ('Qual linguagem roda no navegador?', "JavaScript", 1, "multiple",
             "Python", "Java", "JavaScript", "C++",
             "JavaScript roda no navegador"),

            # MÉDIO
            ('O que SELECT * faz no SQL?', "*", 2, "multiple",
             "Seleciona tudo", "*", "Busca linha", "Erro",
             "Seleciona todas as colunas"),

            ('Qual palavra cria função em Python?', "def", 2, "multiple",
             "function", "def", "lambda", "create",
             "def define funções"),

            # DIFÍCIL
            ('for i in range(3): print(i)', "0 1 2", 3, "text",
             None, None, None, None,
             "range(3) vai de 0 até 2")

        ]

        cursor.executemany("""
        INSERT INTO questions 
        (question, answer, difficulty, type, option1, option2, option3, option4, explanation)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, perguntas)

    conn.commit()
    conn.close()