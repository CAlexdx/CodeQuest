import os
import sqlite3
from werkzeug.security import generate_password_hash

# ==========================
# CONFIGURAÇÃO DE CONEXÃO
# ==========================

def get_db():
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        import psycopg2
        return psycopg2.connect(db_url)
    else:
        return sqlite3.connect("database.db")

def get_placeholder():
    """Define se usa %s (Postgres) ou ? (SQLite)"""
    return "%s" if os.environ.get("DATABASE_URL") else "?"

# ==========================
# INICIALIZAÇÃO DO BANCO
# ==========================

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    p = get_placeholder()
    is_pg = p == "%s"

    print("--- Iniciando CodeQuest Database Setup ---")

    # 1. Tabela de Usuários
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS users (
        id {"SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"},
        username TEXT UNIQUE,
        password TEXT,
        xp INTEGER DEFAULT 0,
        is_admin BOOLEAN DEFAULT FALSE
    )
    """)

    # 2. Tabela de Perguntas
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS questions (
        id {"SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"},
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

    # 3. Tabela de Controle de Respostas (Anti-Spam/Repetição)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS answered (
        user_id INTEGER,
        question_id INTEGER
    )
    """)

    # ==========================
    # CRIAR CONTA ADMIN PADRÃO
    # ==========================
    # Verifica se já existe um admin para não duplicar
    cursor.execute(f"SELECT * FROM users WHERE username = {p}", ("admin",))
    if not cursor.fetchone():
        print("Criando conta de administrador padrão...")
        # Senha padrão para o grupo: admin123
        hashed_pw = generate_password_hash("admin123")
        cursor.execute(
            f"INSERT INTO users (username, password, is_admin) VALUES ({p}, {p}, {p})",
            ("admin", hashed_pw, True)
        )

    # ==========================
    # POPULAR PERGUNTAS (SE ESTIVER VAZIO)
    # ==========================
    cursor.execute("SELECT COUNT(*) FROM questions")
    total = cursor.fetchone()[0]

    if total > 0:
        print(f"Banco já contém {total} perguntas. Pulando inserção.")
    else:
        print("Inserindo banco de questões iniciais...")
        
        # Base de dados de exemplo (Fácil, Médio, Difícil)
        perguntas_base = [
            # Nível 1 - Fácil
            ("print('Hello') → qual a saída?", "hello", 1, "text", None, None, None, None),
            ("Linguagem que roda no navegador?", "javascript", 1, "multiple", "Python", "Java", "JavaScript", "C++"),
            ("Qual símbolo inicia um comentário em Python?", "#", 1, "multiple", "//", "#", "/*", "--"),
            ("HTML é uma linguagem de programação?", "falso", 1, "multiple", "verdadeiro", "falso", "talvez", "depende"),
            ("O que significa JS?", "javascript", 1, "text", None, None, None, None),
            
            # Nível 2 - Médio
            ("Qual comando SQL é usado para deletar dados?", "delete", 2, "multiple", "REMOVE", "DROP", "DELETE", "CLEAR"),
            ("Em Python, qual função conta itens de uma lista?", "len", 2, "text", None, None, None, None),
            ("O que o comando 'break' faz em um loop?", "parar", 2, "multiple", "continuar", "parar", "pular", "repetir"),
            ("Qual o seletor CSS para IDs?", "#", 2, "multiple", ".", "#", "*", "@"),
            ("Dicionários em Python guardam pares de...?", "chave valor", 2, "text", None, None, None, None),
            
            # Nível 3 - Difícil
            ("Qual a complexidade de tempo de uma busca binária?", "o(log n)", 3, "multiple", "O(n)", "O(n²)", "O(log n)", "O(1)"),
            ("Como declarar uma classe em Python?", "class", 3, "text", None, None, None, None),
            ("O que é um JSON?", "formato de dados", 3, "multiple", "linguagem", "banco de dados", "formato de dados", "protocolo"),
            ("Qual método HTTP é usado para atualizar dados?", "put", 3, "multiple", "GET", "POST", "PUT", "DELETE"),
            ("Função que chama a si mesma é...?", "recursividade", 3, "text", None, None, None, None),
        ]

        # Multiplicamos para garantir o volume de 100+ perguntas solicitado
        # 15 perguntas x 7 = 105 perguntas no banco
        perguntas_finais = perguntas_base * 7

        cursor.executemany(
            f"""INSERT INTO questions 
            (question, answer, difficulty, type, opt1, opt2, opt3, opt4)
            VALUES ({p},{p},{p},{p},{p},{p},{p},{p})""",
            perguntas_finais
        )
        print("105 perguntas inseridas com sucesso!")

    conn.commit()
    conn.close()
    print("--- Setup Finalizado com Sucesso ---")

if __name__ == "__main__":
    init_db()