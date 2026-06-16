import os
import sqlite3
import unicodedata
from flask import Flask, render_template, request, redirect, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "segredo_super_codequest")

from init_db import init_db
try:
    init_db()
except Exception as e:
    print(f"[init_db] {e}")

# ==========================
# BANCO DE DADOS
# ==========================

def get_db():
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        import psycopg2
        return psycopg2.connect(db_url)
    return sqlite3.connect("database.db")

def ph():
    """Placeholder: %s para Postgres, ? para SQLite."""
    return "%s" if os.environ.get("DATABASE_URL") else "?"

# ==========================
# HELPERS
# ==========================

def get_level(xp):
    return xp // 50

def get_difficulty(level):
    if level < 2:
        return 1
    elif level < 4:
        return 2
    return 3

def normalize(text):
    """Remove acentos e coloca em minúsculas para comparação flexível."""
    return ''.join(
        c for c in unicodedata.normalize('NFD', text.lower().strip())
        if unicodedata.category(c) != 'Mn'
    )

def get_current_user():
    """Retorna (id, username, xp, is_admin) do usuário logado ou None."""
    if "user_id" not in session:
        return None
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT id, username, xp, is_admin FROM users WHERE id={ph()}",
        (session["user_id"],)
    )
    row = cursor.fetchone()
    conn.close()
    return row

def is_admin():
    user = get_current_user()
    return bool(user and user[3])

def require_login():
    """Retorna redirect se não estiver logado, None se estiver."""
    if "user_id" not in session:
        return redirect("/login")
    return None

def require_admin():
    if not is_admin():
        return redirect("/")
    return None

# ==========================
# ROTA PRINCIPAL (GAMEPLAY)
# ==========================

@app.route("/")
def home():
    redir = require_login()
    if redir:
        return redir

    conn = get_db()
    cursor = conn.cursor()
    p = ph()

    cursor.execute(
        f"SELECT username, xp FROM users WHERE id={p}",
        (session["user_id"],)
    )
    user = cursor.fetchone()

    if not user:
        conn.close()
        return redirect("/logout")

    level = get_level(user[1])
    difficulty = get_difficulty(level)

    # Busca pergunta não respondida adequada ao nível atual
    cursor.execute(f"""
        SELECT * FROM questions
        WHERE difficulty <= {p}
        AND id NOT IN (
            SELECT question_id FROM answered WHERE user_id={p}
        )
        ORDER BY RANDOM() LIMIT 1
    """, (difficulty, session["user_id"]))

    q = cursor.fetchone()

    # Se respondeu tudo, reseta o histórico e reinicia
    if not q:
        cursor.execute(
            f"DELETE FROM answered WHERE user_id={p}",
            (session["user_id"],)
        )
        conn.commit()
        cursor.execute(
            f"SELECT * FROM questions WHERE difficulty <= {p} ORDER BY RANDOM() LIMIT 1",
            (difficulty,)
        )
        q = cursor.fetchone()

    conn.close()

    question_data = None
    if q:
        question_data = {
            "id": q[0],
            "question": q[1],
            "type": q[4],
            "options": [q[5], q[6], q[7], q[8]],
        }

    return render_template(
        "index.html",
        username=user[0],
        xp=user[1],
        xp_next=(level + 1) * 50,
        level=level,
        question=question_data,
    )

# ==========================
# LOGIN / REGISTRO / LOGOUT
# ==========================

@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect("/")

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            error = "Preencha todos os campos."
        elif len(username) > 15:
            error = "Nome de usuário muito longo (máx. 15 caracteres)."
        elif len(password) < 4:
            error = "Senha muito curta (mín. 4 caracteres)."
        else:
            conn = get_db()
            cursor = conn.cursor()
            p = ph()
            try:
                cursor.execute(
                    f"INSERT INTO users (username, password) VALUES ({p}, {p})",
                    (username, generate_password_hash(password))
                )
                conn.commit()
                return redirect("/login")
            except Exception:
                error = "Este usuário já existe!"
            finally:
                conn.close()

    return render_template("register.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect("/")

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            error = "Preencha todos os campos."
        else:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT id, password FROM users WHERE username={ph()}",
                (username,)
            )
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
# RESPOSTA (API)
# ==========================

@app.route("/answer", methods=["POST"])
def answer():
    redir = require_login()
    if redir:
        return jsonify({"error": "Acesso negado"}), 403

    data = request.get_json(silent=True)
    if not data or "id" not in data or "answer" not in data:
        return jsonify({"error": "Dados inválidos"}), 400

    question_id = data["id"]
    user_answer = str(data["answer"]).strip()

    conn = get_db()
    cursor = conn.cursor()
    p = ph()

    # Anti-spam: não pontuar duas vezes a mesma pergunta
    cursor.execute(
        f"SELECT 1 FROM answered WHERE user_id={p} AND question_id={p}",
        (session["user_id"], question_id)
    )
    if cursor.fetchone():
        conn.close()
        return jsonify({"result": "already_answered"})

    cursor.execute(
        f"SELECT answer FROM questions WHERE id={p}",
        (question_id,)
    )
    row = cursor.fetchone()

    if not row:
        conn.close()
        return jsonify({"error": "Pergunta não encontrada"}), 404

    correct = row[0]
    result = "correct" if normalize(user_answer) == normalize(correct) else "wrong"

    if result == "correct":
        cursor.execute(
            f"UPDATE users SET xp = xp + 10 WHERE id={p}",
            (session["user_id"],)
        )

    cursor.execute(
        f"INSERT INTO answered (user_id, question_id) VALUES ({p}, {p})",
        (session["user_id"], question_id)
    )
    conn.commit()
    conn.close()

    return jsonify({"result": result, "correct_answer": correct})

# ==========================
# PAINEL ADMIN
# ==========================

@app.route("/admin")
def admin():
    redir = require_admin()
    if redir:
        return redir

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, xp, is_admin FROM users ORDER BY id ASC")
    users = cursor.fetchall()
    cursor.execute("SELECT id, question, difficulty FROM questions ORDER BY id DESC")
    questions = cursor.fetchall()
    conn.close()

    return render_template("admin.html", users=users, questions=questions)


@app.route("/admin/set_xp", methods=["POST"])
def set_xp():
    redir = require_admin()
    if redir:
        return "Acesso negado", 403

    user_id = request.form.get("user_id")
    xp = request.form.get("xp")

    try:
        xp = int(xp)
        if xp < 0:
            xp = 0
    except (TypeError, ValueError):
        return "XP inválido", 400

    conn = get_db()
    cursor = conn.cursor()
    p = ph()
    cursor.execute(f"UPDATE users SET xp={p} WHERE id={p}", (xp, user_id))
    conn.commit()
    conn.close()
    return redirect("/admin")


@app.route("/admin/toggle_admin/<int:user_id>")
def toggle_admin(user_id):
    redir = require_admin()
    if redir:
        return "Acesso negado", 403

    if user_id == session.get("user_id"):
        return "Erro: você não pode remover seu próprio acesso.", 400

    conn = get_db()
    cursor = conn.cursor()
    p = ph()
    cursor.execute(f"SELECT is_admin FROM users WHERE id={p}", (user_id,))
    row = cursor.fetchone()

    if row:
        cursor.execute(
            f"UPDATE users SET is_admin={p} WHERE id={p}",
            (not bool(row[0]), user_id)
        )
        conn.commit()

    conn.close()
    return redirect("/admin")


@app.route("/admin/delete_user/<int:user_id>")
def delete_user(user_id):
    redir = require_admin()
    if redir:
        return "Acesso negado", 403

    if user_id == session.get("user_id"):
        return "Erro: você não pode deletar sua própria conta.", 400

    conn = get_db()
    cursor = conn.cursor()
    p = ph()
    cursor.execute(f"DELETE FROM answered WHERE user_id={p}", (user_id,))
    cursor.execute(f"DELETE FROM users WHERE id={p}", (user_id,))
    conn.commit()
    conn.close()
    return redirect("/admin")

# ==========================
# RANKING E PERFIL
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
    redir = require_login()
    if redir:
        return redir

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT username, xp FROM users WHERE id={ph()}",
        (session["user_id"],)
    )
    user = cursor.fetchone()
    conn.close()

    if not user:
        return redirect("/logout")

    return render_template(
        "profile.html",
        username=user[0],
        xp=user[1],
        level=get_level(user[1])
    )

# ==========================
# INICIALIZAÇÃO
# ==========================

if __name__ == "__main__":
    app.run(debug=True)