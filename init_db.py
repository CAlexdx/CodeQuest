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
        xp INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # QUESTIONS
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

    # HISTÓRICO
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_answers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        question_id INTEGER,
        is_correct INTEGER,
        answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("SELECT COUNT(*) FROM questions")
    if cursor.fetchone()[0] == 0:

        perguntas = [

        # ==========================
        # 🟢 FÁCIL
        # ==========================

        ("Qual será a saída?\nprint('Hello World')",
         "hello world", 1, "text",
         None, None, None, None,
         "print exibe texto na tela"),

        ("Complete o código:\nprint('____') → Hello",
         "hello", 1, "cloze",
         None, None, None, None,
         "Você precisa completar com Hello"),

        ("Qual linguagem roda no navegador?",
         "JavaScript", 1, "multiple",
         "Python", "Java", "JavaScript", "C++",
         "JavaScript roda no navegador"),

        ("Qual símbolo representa comentário em Python?",
         "#", 1, "multiple",
         "//", "#", "<!-- -->", "--",
         "# é usado para comentários"),

        ("Complete:\nif 10 % 2 == ____:",
         "0", 1, "cloze",
         None, None, None, None,
         "Número par tem resto 0"),

        # ==========================
        # 🟡 MÉDIO
        # ==========================

        ("Qual será a saída?\nnumero = 10\nif numero % 2 == 0:\n print('Par')",
         "par", 2, "text",
         None, None, None, None,
         "10 é número par"),

        ("Qual palavra cria função em Python?",
         "def", 2, "multiple",
         "function", "def", "lambda", "create",
         "def define funções"),

        ("O que SELECT * faz no SQL?",
         "Seleciona tudo", 2, "multiple",
         "Seleciona tudo", "*", "Busca linha", "Erro",
         "Seleciona todas as colunas"),

        ("Complete o código:\nfor i in range(__):",
         "5", 2, "cloze",
         None, None, None, None,
         "range define quantas vezes o loop roda"),

        ("Qual é o resultado?\nprint(2 + 3 * 2)",
         "8", 2, "text",
         None, None, None, None,
         "Multiplicação vem antes da soma"),

        # ==========================
        # 🔴 DIFÍCIL
        # ==========================

        ("Qual será a saída?\nfor i in range(3): print(i)",
         "0 1 2", 3, "text",
         None, None, None, None,
         "range(3) vai de 0 até 2"),

        ("Qual comando remove tabela no SQL?",
         "DROP TABLE", 3, "multiple",
         "DELETE", "DROP TABLE", "REMOVE", "CLEAR",
         "DROP TABLE remove a tabela inteira"),

        ("Complete:\ndef soma(a,b): return ____",
         "a+b", 3, "cloze",
         None, None, None, None,
         "Retorna a soma"),

        ("Qual é a saída?\nprint(bool(0))",
         "false", 3, "text",
         None, None, None, None,
         "0 é considerado False"),

        ("Qual estrutura repete enquanto condição for verdadeira?",
         "while", 3, "multiple",
         "for", "loop", "while", "repeat",
         "while executa enquanto for verdadeiro"),

        ]

        cursor.executemany("""
        INSERT INTO questions 
        (question, answer, difficulty, type, option1, option2, option3, option4, explanation)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, perguntas)

    conn.commit()
    conn.close()