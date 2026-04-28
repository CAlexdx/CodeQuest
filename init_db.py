import os
import sqlite3

def get_db():
    db_url = os.environ.get("DATABASE_URL")

    if db_url:
        import psycopg2
        return psycopg2.connect(db_url)
    else:
        return sqlite3.connect("database.db")

def get_placeholder():
    return "%s" if os.environ.get("DATABASE_URL") else "?"

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    p = get_placeholder()

    # ==========================
    # USERS
    # ==========================
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS users (
        id {"SERIAL PRIMARY KEY" if p=="%s" else "INTEGER PRIMARY KEY AUTOINCREMENT"},
        username TEXT UNIQUE,
        password TEXT,
        xp INTEGER DEFAULT 0,
        is_admin BOOLEAN DEFAULT FALSE
    )
    """)

    # ==========================
    # QUESTIONS
    # ==========================
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS questions (
        id {"SERIAL PRIMARY KEY" if p=="%s" else "INTEGER PRIMARY KEY AUTOINCREMENT"},
        question TEXT,
        answer TEXT,
        difficulty INTEGER,
        type TEXT,
        opt1 TEXT,
        opt2 TEXT,
        opt3 TEXT,
        opt4 TEXT
    )
    """)

    # ==========================
    # ANSWERED (ANTI-SPAM)
    # ==========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS answered (
        user_id INTEGER,
        question_id INTEGER
    )
    """)

    # ==========================
    # LIMPAR PERGUNTAS (IMPORTANTE)
    # ==========================
    cursor.execute("DELETE FROM questions")

    # ==========================
    # PERGUNTAS (100+)
    # ==========================

    perguntas = [

    # ===== FÁCIL =====
    ("print('Hello') → saída?", "hello", 1, "text", None, None, None, None),
    ("Qual linguagem roda no navegador?", "javascript", 1, "multiple", "Python", "Java", "JavaScript", "C++"),
    ("Complete: print('____') → World", "world", 1, "cloze", None, None, None, None),
    ("Qual símbolo comenta em Python?", "#", 1, "multiple", "//", "#", "<!--", "--"),
    ("2 + 2 = ?", "4", 1, "text", None, None, None, None),
    ("Qual é variável válida?", "x", 1, "multiple", "1x", "@x", "x", "#x"),
    ("HTML é usado para?", "estrutura", 1, "multiple", "lógica", "estrutura", "banco", "rede"),
    ("Qual comando imprime?", "print", 1, "multiple", "echo", "print", "show", "write"),
    ("True é?", "boolean", 1, "multiple", "string", "boolean", "int", "float"),
    ("10 > 5 ?", "true", 1, "text", None, None, None, None),

    # ===== MÉDIO =====
    ("for i in range(3): print(i)", "0 1 2", 2, "text", None, None, None, None),
    ("Qual comando SQL seleciona?", "select", 2, "multiple", "INSERT", "SELECT", "DROP", "DELETE"),
    ("def serve para?", "funcao", 2, "multiple", "loop", "funcao", "classe", "condicao"),
    ("if x > 0: é?", "condicional", 2, "multiple", "loop", "condicional", "classe", "erro"),
    ("Lista em Python?", "list", 2, "multiple", "array", "list", "dict", "set"),
    ("len([1,2,3])?", "3", 2, "text", None, None, None, None),
    ("x = 5; x += 1?", "6", 2, "text", None, None, None, None),
    ("while faz?", "loop", 2, "multiple", "condicao", "loop", "variavel", "erro"),
    ("dict guarda?", "chave valor", 2, "multiple", "lista", "numero", "chave valor", "loop"),
    ("break faz?", "parar", 2, "multiple", "continuar", "parar", "loop", "erro"),

    # ===== DIFÍCIL =====
    ("lambda x: x*2 retorna?", "funcao", 3, "multiple", "valor", "funcao", "erro", "classe"),
    ("O(1) significa?", "constante", 3, "multiple", "lento", "rapido", "constante", "loop"),
    ("JOIN SQL faz?", "juntar tabelas", 3, "multiple", "apagar", "juntar tabelas", "criar", "erro"),
    ("API é?", "interface", 3, "multiple", "linguagem", "interface", "banco", "servidor"),
    ("JSON é?", "formato", 3, "multiple", "linguagem", "formato", "compilador", "cpu"),
    ("try/except serve?", "erro", 3, "multiple", "loop", "erro", "variavel", "classe"),
    ("class em Python?", "objeto", 3, "multiple", "função", "objeto", "loop", "erro"),
    ("recursão é?", "função chamando si", 3, "multiple", "loop", "função chamando si", "erro", "classe"),
    ("index começa em?", "0", 3, "text", None, None, None, None),
    ("None é?", "nulo", 3, "multiple", "string", "nulo", "numero", "lista"),

    ]

    # DUPLICAR PARA TER +100
    perguntas = perguntas * 5

    cursor.executemany(
        f"""INSERT INTO questions 
        (question, answer, difficulty, type, opt1, opt2, opt3, opt4)
        VALUES ({p},{p},{p},{p},{p},{p},{p},{p})""",
        perguntas
    )

    conn.commit()
    conn.close()

    print("Banco populado com sucesso!")

if __name__ == "__main__":
    init_db()