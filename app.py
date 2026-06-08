import os
import sqlite3
import unicodedata
from flask import Flask, render_template, request, redirect, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
from init_db import init_db

try:
    init_db()
except Exception as e:
    print(e)
app.secret_key = os.environ.get("SECRET_KEY", "segredo_super_codequest")

# ==========================
# CONFIGURAÇÃO DO BANCO (HÍBRIDO)
# ==========================

def get_db():
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        import psycopg2
        return psycopg2.connect(db_url)
    else:
        return sqlite3.connect("database.db")

def get_placeholder():
    """Retorna %s para Postgres (Render) ou ? para SQLite (Local)"""
    return "%s" if os.environ.get("DATABASE_URL") else "?"

# ==========================
# FUNÇÕES DE APOIO E GAMIFICAÇÃO
# ==========================

def get_level(xp):
    return xp // 50

def get_difficulty(level):
    if level < 2: return 1
    elif level < 4: return 2
    else: return 3

def normalize(text):
    """Remove acentos e padroniza para comparação"""
    return ''.join(
        c for c in unicodedata.normalize('NFD', text.lower().strip())
        if unicodedata.category(c) != 'Mn'
    )

def is_admin():
    """Verifica se o usuário logado tem permissão de admin"""
    if "user_id" not in session:
        return False
    conn = get_db()
    cursor = conn.cursor()
    p = get_placeholder()
    cursor.execute(f"SELECT is_admin FROM users WHERE id={p}", (session["user_id"],))
    row = cursor.fetchone()
    conn.close()
    return bool(row and row[0])

# ==========================
# ROTA PRINCIPAL (GAMEPLAY)
# ==========================

@app.route("/")
def home():
    if "user_id" not in session:
        return redirect("/login")
    
    conn = get_db()
    cursor = conn.cursor()
    p = get_placeholder()
    
    cursor.execute(f"SELECT username, xp FROM users WHERE id={p}", (session["user_id"],))
    user = cursor.fetchone()
    
    if not user:
        return redirect("/logout")

    level = get_level(user[1])
    difficulty = get_difficulty(level)

    # Busca pergunta baseada na dificuldade que o usuário ainda não respondeu
    cursor.execute(f"""
        SELECT * FROM questions 
        WHERE difficulty <= {p} 
        AND id NOT IN (SELECT question_id FROM answered WHERE user_id={p})
        ORDER BY RANDOM() LIMIT 1
    """, (difficulty, session["user_id"]))
    
    q = cursor.fetchone()

    # Se zerar as perguntas daquele nível, limpa o histórico para ele poder repetir
    if not q:
        cursor.execute(f"DELETE FROM answered WHERE user_id={p}", (session["user_id"],))
        conn.commit()
        cursor.execute(f"SELECT * FROM questions WHERE difficulty <= {p} ORDER BY RANDOM() LIMIT 1", (difficulty,))
        q = cursor.fetchone()

    conn.close()
    
    return render_template("index.html", 
                           username=user[0], 
                           xp=user[1], 
                           xp_next=(level+1)*50, 
                           level=level, 
                           question={
                               "id": q[0], "question": q[1], "type": q[4],
                               "options": [q[5], q[6], q[7], q[8]]
                           } if q else None)

# ==========================
# SISTEMA DE LOGIN E REGISTRO
# ==========================

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        
        conn = get_db()
        cursor = conn.cursor()
        p = get_placeholder()
        try:
            cursor.execute(f"INSERT INTO users (username, password) VALUES ({p}, {p})",
                           (username, generate_password_hash(password)))
            conn.commit()
            return redirect("/login")
        except:
            error = "Este usuário já existe!"
        finally:
            conn.close()
    return render_template("register.html", error=error)

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        
        conn = get_db()
        cursor = conn.cursor()
        p = get_placeholder()
        cursor.execute(f"SELECT id, password FROM users WHERE username={p}", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):
            session["user_id"] = user[0]
            return redirect("/")
        error = "Usuário ou senha incorretos."
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ==========================
# LÓGICA DE RESPOSTAS (API)
# ==========================

@app.route("/answer", methods=["POST"])
def answer():
    if "user_id" not in session:
        return jsonify({"error": "Acesso negado"}), 403
    
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()
    p = get_placeholder()

    # Validação anti-spam (não pontuar duas vezes a mesma pergunta)
    cursor.execute(f"SELECT 1 FROM answered WHERE user_id={p} AND question_id={p}", 
                   (session["user_id"], data["id"]))
    if cursor.fetchone():
        return jsonify({"result": "already_answered"})

    cursor.execute(f"SELECT answer FROM questions WHERE id={p}", (data["id"],))
    correct = cursor.fetchone()[0]

    if normalize(data["answer"]) == normalize(correct):
        cursor.execute(f"UPDATE users SET xp = xp + 10 WHERE id={p}", (session["user_id"],))
        result = "correct"
    else:
        result = "wrong"

    cursor.execute(f"INSERT INTO answered (user_id, question_id) VALUES ({p}, {p})",
                   (session["user_id"], data["id"]))
    conn.commit()
    conn.close()
    return jsonify({"result": result, "correct_answer": correct})

# ==========================
# PAINEL ADMINISTRATIVO
# ==========================

@app.route("/admin")
def admin():
    if not is_admin():
        return redirect("/") # Bloqueia quem não é admin
    
    conn = get_db()
    cursor = conn.cursor()
    # Pega todos os usuários para a tabela de gestão
    cursor.execute("SELECT id, username, xp, is_admin FROM users ORDER BY id ASC")
    users = cursor.fetchall()
    
    # Pega as questões para conferência
    cursor.execute("SELECT id, question, difficulty FROM questions ORDER BY id DESC")
    questions = cursor.fetchall()
    conn.close()
    return render_template("admin.html", users=users, questions=questions)

@app.route("/admin/set_xp", methods=["POST"])
def set_xp():
    if not is_admin(): return "Acesso negado", 403
    
    user_id = request.form.get("user_id")
    xp = request.form.get("xp")
    
    conn = get_db()
    cursor = conn.cursor()
    p = get_placeholder()
    
    cursor.execute(f"UPDATE users SET xp={p} WHERE id={p}", (xp, user_id))
    conn.commit()
    conn.close()
    return redirect("/admin")

@app.route("/admin/toggle_admin/<int:user_id>")
def toggle_admin(user_id):
    """ Rota para promover ou rebaixar um usuário """
    if not is_admin(): return "Acesso negado", 403
    
    # Segurança: Impede que o admin logado remova seu próprio cargo
    if user_id == session.get("user_id"):
        return "Erro: Você não pode remover seu próprio acesso administrativo.", 400

    conn = get_db()
    cursor = conn.cursor()
    p = get_placeholder()

    # Busca o status atual
    cursor.execute(f"SELECT is_admin FROM users WHERE id={p}", (user_id,))
    user = cursor.fetchone()
    
    if user:
        # Inverte o status: se era True (1) vira False (0) e vice-versa
        novo_status = not bool(user[0])
        cursor.execute(f"UPDATE users SET is_admin={p} WHERE id={p}", (novo_status, user_id))
        conn.commit()
    
    conn.close()
    return redirect("/admin")

@app.route("/admin/delete_user/<int:user_id>")
def delete_user(user_id):
    if not is_admin(): return "Acesso negado", 403
    
    # Segurança: Impede que o admin logado se delete
    if user_id == session.get("user_id"):
        return "Erro: Você não pode deletar sua própria conta enquanto está logado.", 400
        
    conn = get_db()
    cursor = conn.cursor()
    p = get_placeholder()
    
    # Limpa o histórico de respostas do usuário primeiro (integridade do banco)
    cursor.execute(f"DELETE FROM answered WHERE user_id={p}", (user_id,))
    # Deleta o usuário
    cursor.execute(f"DELETE FROM users WHERE id={p}", (user_id,))
    
    conn.commit()
    conn.close()
    return redirect("/admin")
# ==========================
# SOCIAL E PERFIL
# ==========================

@app.route("/ranking")
def ranking():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT username, xp FROM users ORDER BY xp DESC LIMIT 10")
    rows = cursor.fetchall()
    conn.close()
    users = [{"username": r[0], "xp": r[1]} for r in rows]
    return render_template("ranking.html", users=users)

@app.route("/profile")
def profile():
    if "user_id" not in session: return redirect("/login")
    conn = get_db()
    cursor = conn.cursor()
    p = get_placeholder()
    cursor.execute(f"SELECT username, xp FROM users WHERE id={p}", (session["user_id"],))
    user = cursor.fetchone()
    conn.close()
    return render_template("profile.html", username=user[0], xp=user[1], level=get_level(user[1]))

# ==========================
# INICIALIZAÇÃO
# ==========================

if __name__ == "__main__":
    from init_db import init_db
    init_db() # Garante que o banco está pronto
    app.run(debug=True)