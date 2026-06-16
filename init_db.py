import os
import sqlite3
from werkzeug.security import generate_password_hash

# ==========================
# CONEXÃO
# ==========================

def get_db():
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        import psycopg2
        return psycopg2.connect(db_url)
    return sqlite3.connect("database.db")

def ph():
    return "%s" if os.environ.get("DATABASE_URL") else "?"

# ==========================
# SETUP DO BANCO
# ==========================

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    p = ph()
    is_pg = (p == "%s")

    print("--- Iniciando CodeQuest Database Setup ---")

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS users (
            id {"SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"},
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            xp INTEGER DEFAULT 0,
            is_admin BOOLEAN DEFAULT FALSE
        )
    """)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS questions (
            id {"SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"},
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            difficulty INTEGER NOT NULL,
            type TEXT NOT NULL,
            opt1 TEXT,
            opt2 TEXT,
            opt3 TEXT,
            opt4 TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS answered (
            user_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL
        )
    """)

    # Admin padrão
    cursor.execute(f"SELECT id FROM users WHERE username={p}", ("admin",))
    if not cursor.fetchone():
        print("Criando conta de administrador padrão...")
        cursor.execute(
            f"INSERT INTO users (username, password, is_admin) VALUES ({p}, {p}, {p})",
            ("admin", generate_password_hash("admin123"), True)
        )

    # Perguntas iniciais
    cursor.execute("SELECT COUNT(*) FROM questions")
    total = cursor.fetchone()[0]

    if total > 0:
        print(f"Banco já contém {total} perguntas. Pulando inserção.")
    else:
        print("Inserindo banco de questões iniciais...")
        perguntas = [
            # --- Nível 1: Fácil ---
            ("Qual é a saída de print('Hello')?", "hello", 1, "text", None, None, None, None),
            ("Qual linguagem roda no navegador?", "javascript", 1, "multiple", "Python", "Java", "JavaScript", "C++"),
            ("Qual símbolo inicia um comentário em Python?", "#", 1, "multiple", "//", "#", "/*", "--"),
            ("HTML é uma linguagem de programação?", "falso", 1, "multiple", "verdadeiro", "falso", "talvez", "depende"),
            ("O que significa a sigla 'JS'?", "javascript", 1, "text", None, None, None, None),
            ("Qual tag HTML cria um parágrafo?", "p", 1, "multiple", "div", "p", "span", "h1"),
            ("Qual operador faz divisão em Python?", "/", 1, "multiple", "*", "/", "%", "//"),
            ("Como se imprime algo em Python?", "print", 1, "text", None, None, None, None),
            ("Qual símbolo é usado para strings em Python?", "aspas", 1, "multiple", "colchetes", "aspas", "chaves", "parênteses"),
            ("Qual cor o CSS 'color: red' aplica?", "vermelho", 1, "multiple", "azul", "verde", "vermelho", "amarelo"),

            # --- Nível 2: Médio ---
            ("Qual comando SQL deleta dados?", "delete", 2, "multiple", "REMOVE", "DROP", "DELETE", "CLEAR"),
            ("Qual função Python conta itens de uma lista?", "len", 2, "text", None, None, None, None),
            ("O que 'break' faz em um loop?", "parar", 2, "multiple", "continuar", "parar", "pular", "repetir"),
            ("Qual seletor CSS é usado para IDs?", "#", 2, "multiple", ".", "#", "*", "@"),
            ("Dicionários Python armazenam pares de...?", "chave valor", 2, "text", None, None, None, None),
            ("Qual método adiciona item ao final de uma lista Python?", "append", 2, "text", None, None, None, None),
            ("Qual tag HTML cria um link?", "a", 2, "multiple", "link", "a", "href", "url"),
            ("O que significa 'API'?", "interface de programacao de aplicacoes", 2, "text", None, None, None, None),
            ("Qual comando Git salva alterações?", "commit", 2, "multiple", "push", "save", "commit", "add"),
            ("Em CSS, qual propriedade muda a cor de fundo?", "background-color", 2, "multiple", "color", "background-color", "border-color", "font-color"),

            # --- Nível 3: Difícil ---
            ("Complexidade de tempo de busca binária?", "o(log n)", 3, "multiple", "O(n)", "O(n²)", "O(log n)", "O(1)"),
            ("Como se declara uma classe em Python?", "class", 3, "text", None, None, None, None),
            ("O que é JSON?", "formato de dados", 3, "multiple", "linguagem", "banco de dados", "formato de dados", "protocolo"),
            ("Qual método HTTP atualiza dados?", "put", 3, "multiple", "GET", "POST", "PUT", "DELETE"),
            ("Função que chama a si mesma é chamada de...?", "recursividade", 3, "text", None, None, None, None),
            ("O que é um índice em banco de dados?", "estrutura para busca rapida", 3, "multiple", "tipo de coluna", "estrutura para busca rapida", "chave estrangeira", "constraint"),
            ("Qual princípio OOP esconde detalhes internos?", "encapsulamento", 3, "multiple", "herança", "polimorfismo", "encapsulamento", "abstração"),
            ("O que faz o comando SQL 'JOIN'?", "combinar tabelas", 3, "multiple", "deletar linhas", "combinar tabelas", "criar tabela", "filtrar colunas"),
            ("Qual estrutura de dados opera LIFO?", "pilha", 3, "multiple", "fila", "pilha", "grafo", "arvore"),
            ("O que é um 'deadlock'?", "bloqueio mutuo de processos", 3, "text", None, None, None, None),
        ]

        # 30 perguntas × 4 = 120 perguntas no banco
        perguntas_finais = perguntas * 4

        cursor.executemany(
            f"""INSERT INTO questions
            (question, answer, difficulty, type, opt1, opt2, opt3, opt4)
            VALUES ({p},{p},{p},{p},{p},{p},{p},{p})""",
            perguntas_finais
        )
        print(f"{len(perguntas_finais)} perguntas inseridas com sucesso!")

    conn.commit()
    conn.close()
    print("--- Setup Finalizado ---")


if __name__ == "__main__":
    init_db()