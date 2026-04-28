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

    # QUESTIONS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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

    # CONTROLE DE RESPOSTAS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS answered(
        user_id INTEGER,
        question_id INTEGER
    )
    """)

    cursor.execute("SELECT COUNT(*) FROM questions")
    if cursor.fetchone()[0] == 0:

        perguntas = [

# ==========================
# 🟢 FÁCIL (1)
# ==========================

("print('Hello') → saída?", "hello", 1, "text", None, None, None, None),
("Qual linguagem roda no navegador?", "javascript", 1, "multiple",
 "Python", "Java", "JavaScript", "C++"),
("Complete: print('____') → World", "world", 1, "cloze", None, None, None, None),
("Qual símbolo inicia comentário em Python?", "#", 1, "multiple",
 "//", "#", "/*", "<!--"),
("Qual comando exibe algo na tela em Python?", "print", 1, "text", None, None, None, None),
("HTML é usado para?", "estrutura", 1, "multiple",
 "Estilo", "Banco", "Estrutura", "Servidor"),
("CSS serve para?", "estilo", 1, "multiple",
 "Banco", "Estilo", "Lógica", "Servidor"),
("JS significa?", "javascript", 1, "text", None, None, None, None),
("Qual comando cria variável?", "=", 1, "text", None, None, None, None),
("Qual tipo armazena texto?", "string", 1, "multiple",
 "int", "float", "string", "bool"),

# ==========================
# 🟡 MÉDIO (2)
# ==========================

("numero = 10\nif numero % 2 == 0:\n print('Par')\nSaída?", "par", 2, "multiple",
 "Par", "Ímpar", "Erro", "Nada"),
("Qual comando SQL seleciona dados?", "select", 2, "multiple",
 "INSERT", "SELECT", "DELETE", "DROP"),
("Complete: def ____():", "funcao", 2, "cloze", None, None, None, None),
("Qual palavra cria função?", "def", 2, "multiple",
 "function", "def", "create", "lambda"),
("Qual estrutura repete código?", "for", 2, "multiple",
 "if", "for", "def", "class"),
("Qual banco usamos?", "sqlite", 2, "text", None, None, None, None),
("SELECT * significa?", "*", 2, "text", None, None, None, None),
("Qual comando adiciona dados?", "insert", 2, "multiple",
 "SELECT", "INSERT", "DELETE", "DROP"),
("Qual retorna verdadeiro/falso?", "bool", 2, "multiple",
 "int", "string", "bool", "float"),
("Qual operador compara?", "==", 2, "text", None, None, None, None),

("Complete código: if x > 10: print('____')", "maior", 2, "cloze", None, None, None, None),
("Qual método pega input?", "input", 2, "text", None, None, None, None),
("Qual converte para inteiro?", "int", 2, "text", None, None, None, None),
("Qual estrutura decisão?", "if", 2, "multiple",
 "for", "if", "while", "def"),
("Qual laço infinito?", "while", 2, "multiple",
 "for", "while", "if", "def"),

# ==========================
# 🔴 DIFÍCIL (3)
# ==========================

("for i in range(3): print(i)", "0 1 2", 3, "text", None, None, None, None),
("range(5) vai até?", "4", 3, "multiple",
 "5", "4", "3", "6"),
("Qual chave primária no SQL?", "id", 3, "text", None, None, None, None),
("Qual comando apaga tabela?", "drop", 3, "multiple",
 "DELETE", "DROP", "REMOVE", "CLEAR"),
("Qual atualiza dados?", "update", 3, "multiple",
 "INSERT", "UPDATE", "SELECT", "DROP"),

("Complete: SELECT ____ FROM users", "*", 3, "cloze", None, None, None, None),
("Qual framework Python web?", "flask", 3, "text", None, None, None, None),
("Qual comando conecta DB?", "connect", 3, "text", None, None, None, None),
("Qual método HTTP envia dados?", "post", 3, "multiple",
 "GET", "POST", "PUT", "DELETE"),
("Qual rota principal Flask?", "/", 3, "text", None, None, None, None),

("Complete: app.route('____')", "/", 3, "cloze", None, None, None, None),
("Qual biblioteca senha?", "werkzeug", 3, "text", None, None, None, None),
("Qual banco online usamos?", "postgresql", 3, "text", None, None, None, None),
("Qual comando cria tabela?", "create table", 3, "text", None, None, None, None),
("Qual função random SQL?", "random", 3, "text", None, None, None, None),

("Qual linguagem backend?", "python", 3, "multiple",
 "HTML", "CSS", "Python", "XML"),
("Qual retorna JSON?", "jsonify", 3, "text", None, None, None, None),
("Qual guarda sessão?", "session", 3, "text", None, None, None, None),
("Qual verifica senha?", "check_password_hash", 3, "text", None, None, None, None),
("Qual criptografa senha?", "generate_password_hash", 3, "text", None, None, None, None),

        ]

        cursor.executemany("""
        INSERT INTO questions 
        (question, answer, difficulty, type, opt1, opt2, opt3, opt4)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, perguntas)

    conn.commit()
    conn.close()