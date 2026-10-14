import hashlib
import html
import logging
import os
import random
import re
import sqlite3
import unicodedata
from datetime import date, datetime, timedelta, timezone
from functools import wraps
from urllib.parse import urlencode, urlparse

from flask import Flask, g, jsonify, redirect, render_template, request, session
from itsdangerous import URLSafeTimedSerializer
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash

# ==========================
# CONFIGURAÇÃO
# ==========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_PATH = os.path.join(BASE_DIR, "database.db")

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
IS_PG = bool(DATABASE_URL)
IS_VERCEL = bool(os.environ.get("VERCEL"))

LAB_URL = os.environ.get("LAB_URL", "https://code-quest-lab.vercel.app/").strip()
AUTO_INJECT_ACHIEVEMENTS = os.environ.get("AUTO_INJECT_ACHIEVEMENTS", "1") != "0"
ASSET_VERSION = os.environ.get("ASSET_VERSION") or os.environ.get("VERCEL_GIT_COMMIT_SHA", "")[:7] or "1"

XP_PER_CORRECT = 10
XP_PER_LEVEL = 50
STREAK_BADGE_DAYS = 5
MAX_USERNAME_LEN = 15
MIN_PASSWORD_LEN = 4
MAX_ANSWER_LEN = 500
MAX_PENDING_BADGES = 6
LAB_TOKEN_SALT = "codequest-lab-v1"

# Conquistas conhecidas: se a linha ainda não existir na tabela `badges`
# (init_db.py não foi reexecutado), ela é criada sob demanda.
BADGE_DEFAULTS = {
    "primeiro_login": ("Primeiro Passo", "Realizou o primeiro acesso na plataforma CodeQuest.", "🚀"),
    "trilha_concluida": ("Mestre das Trilhas", "Completou todas as unidades de uma trilha de aprendizado.", "🏆"),
    "ofensiva_5": ("Chama Acesa", "Alcançou uma ofensiva de 5 dias seguidos.", "🔥"),
    "lab_explorador": ("Explorador do LAB", "Visitou o CodeQuest LAB pela primeira vez.", "🧪"),
    "mestre_bugs": ("Mestre dos Bugs", "Corrigiu desafios do Bug Hunt no CodeQuest LAB.", "🐛"),
}

try:  # fuso para o "dia" da ofensiva (Vercel roda em UTC)
    from zoneinfo import ZoneInfo

    APP_TZ = ZoneInfo(os.environ.get("APP_TIMEZONE", "America/Sao_Paulo"))
except Exception:  # sem tzdata (Windows): Brasil não tem horário de verão desde 2019
    APP_TZ = timezone(timedelta(hours=-3))


def _derive_secret(label):
    """Segredo estável (igual em todas as instâncias serverless) quando a env var não foi definida."""
    base = DATABASE_URL or "codequest-local-dev"
    return hashlib.sha256(f"codequest:{label}:{base}".encode("utf-8")).hexdigest()


SECRET_KEY = os.environ.get("SECRET_KEY") or _derive_secret("session")
LAB_SECRET = os.environ.get("LAB_SHARED_SECRET") or _derive_secret("lab")

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config.update(
    SECRET_KEY=SECRET_KEY,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=IS_VERCEL or os.environ.get("SESSION_COOKIE_SECURE") == "1",
    PERMANENT_SESSION_LIFETIME=timedelta(days=30),
    JSON_AS_ASCII=False,
)
# Atrás do proxy da Vercel: respeita X-Forwarded-Proto/Host
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

if not os.environ.get("SECRET_KEY") and (IS_VERCEL or IS_PG):
    app.logger.warning("SECRET_KEY não definida: usando segredo derivado. Defina SECRET_KEY nas variáveis de ambiente.")

# ==========================
# BANCO DE DADOS (SUPABASE / POSTGRES / SQLITE)
# ==========================

if IS_PG:
    import psycopg2

    DB_ERRORS = (psycopg2.Error,)
    INTEGRITY_ERRORS = (psycopg2.IntegrityError,)
else:
    DB_ERRORS = (sqlite3.Error,)
    INTEGRITY_ERRORS = (sqlite3.IntegrityError,)


class Database:
    """Camada fina: o mesmo SQL (escrito com %s) roda no Postgres e no SQLite."""

    def __init__(self, conn):
        self.conn = conn

    def execute(self, sql, params=()):
        cur = self.conn.cursor()
        cur.execute(sql if IS_PG else sql.replace("%s", "?"), tuple(params))
        return cur

    def fetchone(self, sql, params=()):
        cur = self.execute(sql, params)
        try:
            return cur.fetchone()
        finally:
            cur.close()

    def fetchall(self, sql, params=()):
        cur = self.execute(sql, params)
        try:
            return cur.fetchall()
        finally:
            cur.close()

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()


def _connect():
    if IS_PG:
        kwargs = {"connect_timeout": 10}
        if "sslmode" not in DATABASE_URL:
            kwargs["sslmode"] = os.environ.get("DB_SSLMODE", "require" if "supabase" in DATABASE_URL else "prefer")
        return psycopg2.connect(DATABASE_URL, **kwargs)
    if IS_VERCEL:
        raise RuntimeError(
            "DATABASE_URL não está configurada na Vercel. Defina a string do pooler do Supabase "
            "em Project Settings > Environment Variables."
        )
    return sqlite3.connect(SQLITE_PATH, timeout=10)


def get_db():
    """Uma única conexão por requisição (reaproveitada por todos os helpers)."""
    if "db" not in g:
        g.db = Database(_connect())
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        try:
            db.rollback()  # descarta transação aberta (leituras ou erro)
        except Exception:  # noqa: BLE001
            pass
        try:
            db.close()
        except Exception:  # noqa: BLE001
            pass


# ==========================
# HELPERS
# ==========================

def get_level(xp):
    return (xp or 0) // XP_PER_LEVEL


def get_difficulty(level):
    if level < 2:
        return 1
    elif level < 4:
        return 2
    return 3


def normalize(text):
    """Minúsculas e sem acentos, para comparação flexível."""
    return "".join(
        c for c in unicodedata.normalize("NFD", str(text).lower().strip())
        if unicodedata.category(c) != "Mn"
    )


_QUOTE_CHARS = str.maketrans({c: None for c in "\"'`“”‘’´"})


def simplificar_texto(texto):
    """Forma canônica de uma resposta: sem aspas/crases, sem acentos, minúsculas, espaços únicos."""
    if not texto:
        return ""
    t = normalize(str(texto).translate(_QUOTE_CHARS))
    return re.sub(r"\s+", " ", t).strip()


def answers_match(user_answer, correct_answer):
    return simplificar_texto(user_answer) == simplificar_texto(correct_answer)


def today_local():
    return datetime.now(APP_TZ).date()


def _parse_date(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def current_user():
    """Usuário logado (dict) ou None. Consulta o banco 1x por requisição."""
    if "current_user" in g:
        return g.current_user

    user = None
    try:
        uid = int(session.get("user_id"))
    except (TypeError, ValueError):
        uid = None

    if uid:
        row = get_db().fetchone(
            "SELECT id, username, xp, is_admin, streak FROM users WHERE id=%s", (uid,)
        )
        if row:
            user = {
                "id": row[0],
                "username": row[1],
                "xp": row[2] or 0,
                "is_admin": bool(row[3]),
                "streak": row[4] or 0,
            }
            # mantém session.is_admin atualizado (templates antigos usam session.is_admin)
            if session.get("is_admin") != user["is_admin"]:
                session["is_admin"] = user["is_admin"]

    g.current_user = user
    return user


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            session.clear()  # sessão antiga/usuário removido
            return redirect("/login")
        return view(*args, **kwargs)

    return wrapped


def admin_required(redirect_non_admin=False):
    """Painel (GET /admin) redireciona; ações administrativas respondem 403."""

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = current_user()
            if not user or not user["is_admin"]:
                if not user:
                    session.clear()
                return redirect("/") if redirect_non_admin else ("Acesso negado", 403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


def same_origin_request():
    """Bloqueia ações disparadas por outro site (CSRF) nas rotas administrativas."""
    site = request.headers.get("Sec-Fetch-Site")
    if site:
        return site in ("same-origin", "none")
    for header in ("Origin", "Referer"):
        value = request.headers.get(header)
        if value:
            try:
                return urlparse(value).netloc == request.host
            except ValueError:
                return False
    return True


# ---------- Conquistas (badges) ----------

def _award(db, user_id, badge_code):
    """Concede a conquista se ainda não existir. Retorna dict se foi NOVA, senão None. Não faz commit."""
    row = db.fetchone("SELECT id, name, description, icon FROM badges WHERE code=%s", (badge_code,))
    if not row and badge_code in BADGE_DEFAULTS:
        name, desc, icon = BADGE_DEFAULTS[badge_code]
        db.execute(
            "INSERT INTO badges (code, name, description, icon) VALUES (%s, %s, %s, %s) "
            "ON CONFLICT (code) DO NOTHING",
            (badge_code, name, desc, icon),
        ).close()
        row = db.fetchone("SELECT id, name, description, icon FROM badges WHERE code=%s", (badge_code,))
    if not row:
        return None

    cur = db.execute(
        "INSERT INTO user_badges (user_id, badge_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
        (user_id, row[0]),
    )
    is_new = cur.rowcount == 1
    cur.close()
    if not is_new:
        return None
    return {"code": badge_code, "name": row[1], "description": row[2], "icon": row[3]}


def _queue_badge(badge):
    pending = list(session.get("pending_badges", []))
    if all(b.get("code") != badge["code"] for b in pending):
        pending.append(badge)
    session["pending_badges"] = pending[-MAX_PENDING_BADGES:]


def pop_pending_badges():
    return session.pop("pending_badges", [])


def check_and_award_badge(user_id, badge_code):
    """Concede uma conquista (badge) ao usuário se ele ainda não possuir.

    A conquista nova fica na fila da sessão e é exibida pelo toast no próximo
    carregamento de página (ou devolvida direto no JSON de /answer).
    """
    db = get_db()
    try:
        badge = _award(db, user_id, badge_code)
        if badge:
            db.commit()
            _queue_badge(badge)
        return badge
    except DB_ERRORS:
        db.rollback()
        app.logger.exception("Falha ao conceder badge %s", badge_code)
        return None


def update_streak(user_id):
    """Atualiza a ofensiva (streak) com base no dia local da última atividade. Retorna a ofensiva atual."""
    db = get_db()
    row = db.fetchone("SELECT streak, last_active FROM users WHERE id=%s", (user_id,))
    if not row:
        return 0

    streak = row[0] or 0
    last_date = _parse_date(row[1])
    today = today_local()

    if last_date and last_date >= today:  # já contou hoje
        return streak

    streak = streak + 1 if last_date == today - timedelta(days=1) else 1
    db.execute(
        "UPDATE users SET streak=%s, last_active=%s WHERE id=%s",
        (streak, today.isoformat(), user_id),
    ).close()
    db.commit()

    if streak >= STREAK_BADGE_DAYS:
        check_and_award_badge(user_id, "ofensiva_5")
    return streak


# ---------- Ponte com o CodeQuest LAB ----------

def make_lab_token(user_id):
    """Token assinado e com validade (o LAB confere a assinatura; id puro na URL seria falsificável)."""
    return URLSafeTimedSerializer(LAB_SECRET, salt=LAB_TOKEN_SALT).dumps({"uid": int(user_id)})


# ==========================
# ROTAS PRINCIPAIS
# ==========================

QUESTION_COLS = "id, question, answer, difficulty, type, opt1, opt2, opt3, opt4"


def _pick_adaptive_question(db, user_id, difficulty):
    row = db.fetchone(
        f"""SELECT {QUESTION_COLS} FROM questions q
            WHERE q.difficulty <= %s
              AND NOT EXISTS (SELECT 1 FROM answered a WHERE a.user_id=%s AND a.question_id=q.id)
            ORDER BY RANDOM() LIMIT 1""",
        (difficulty, user_id),
    )
    if row:
        return row

    # Esgotou o "pool" desta dificuldade: recicla apenas as respostas dele
    db.execute(
        "DELETE FROM answered WHERE user_id=%s AND question_id IN "
        "(SELECT id FROM questions WHERE difficulty <= %s)",
        (user_id, difficulty),
    ).close()
    db.commit()
    return db.fetchone(
        f"SELECT {QUESTION_COLS} FROM questions WHERE difficulty <= %s ORDER BY RANDOM() LIMIT 1",
        (difficulty,),
    )


@app.route("/")
@login_required
def home():
    user = current_user()
    db = get_db()

    level = get_level(user["xp"])
    q = _pick_adaptive_question(db, user["id"], get_difficulty(level))

    question_data = None
    if q:
        question_data = {
            "id": q[0],
            "question": q[1],
            "type": q[4],
            "options": [q[5], q[6], q[7], q[8]] if q[4] == "multiple" else [],
        }

    return render_template(
        "index.html",
        username=user["username"],
        xp=user["xp"],
        xp_next=(level + 1) * XP_PER_LEVEL,
        level=level,
        streak=user["streak"],
        question=question_data,
        is_admin=user["is_admin"],
    )


@app.route("/trilhas")
@login_required
def trilhas():
    user = current_user()
    rows = get_db().fetchall(
        """SELECT t.id, t.name, t.icon, t.description,
                  (SELECT COUNT(*) FROM units u WHERE u.trail_id = t.id),
                  (SELECT COUNT(*) FROM unit_progress up JOIN units u2 ON up.unit_id = u2.id
                    WHERE u2.trail_id = t.id AND up.user_id = %s AND up.completed = %s)
           FROM trails t ORDER BY t.trail_order ASC""",
        (user["id"], True),
    )
    trails_data = [
        {
            "id": r[0],
            "name": r[1],
            "icon": r[2],
            "description": r[3],
            "total_units": r[4],
            "completed_units": r[5],
        }
        for r in rows
    ]
    return render_template("trilhas.html", trails=trails_data)


@app.route("/trilhas/<int:trail_id>")
@login_required
def trilha_detail(trail_id):
    user = current_user()
    db = get_db()

    trail = db.fetchone("SELECT id, name, icon, description FROM trails WHERE id=%s", (trail_id,))
    if not trail:
        return redirect("/trilhas")

    units = db.fetchall(
        "SELECT id, unit_order, title, intro_text FROM units WHERE trail_id=%s ORDER BY unit_order ASC",
        (trail_id,),
    )
    progress_rows = db.fetchall("SELECT unit_id, completed FROM unit_progress WHERE user_id=%s", (user["id"],))
    progress_map = {r[0]: bool(r[1]) for r in progress_rows}

    units_data = []
    unlocked = True
    for u in units:
        completed = progress_map.get(u[0], False)
        status = "completed" if completed else ("available" if unlocked else "locked")
        units_data.append({"id": u[0], "order": u[1], "title": u[2], "intro": u[3], "status": status})
        unlocked = completed

    return render_template(
        "trilha_detail.html",
        trail={"id": trail[0], "name": trail[1], "icon": trail[2], "description": trail[3]},
        units=units_data,
    )


@app.route("/unidade/<int:unit_id>")
@login_required
def unidade(unit_id):
    user = current_user()
    uid = user["id"]
    db = get_db()

    unit = db.fetchone(
        "SELECT id, trail_id, unit_order, title, intro_text FROM units WHERE id=%s", (unit_id,)
    )
    if not unit:
        return redirect("/trilhas")

    # Progressão: todas as unidades anteriores da trilha precisam estar concluídas
    pending_previous = db.fetchone(
        """SELECT COUNT(*) FROM units u
           WHERE u.trail_id=%s AND u.unit_order < %s
             AND NOT EXISTS (SELECT 1 FROM unit_progress up
                             WHERE up.unit_id=u.id AND up.user_id=%s AND up.completed=%s)""",
        (unit[1], unit[2], uid, True),
    )[0]
    if pending_previous:
        return redirect(f"/trilhas/{unit[1]}")

    q = db.fetchone(
        f"""SELECT {QUESTION_COLS} FROM questions q
            WHERE q.unit_id=%s
              AND NOT EXISTS (SELECT 1 FROM answered a WHERE a.user_id=%s AND a.question_id=q.id)
            ORDER BY RANDOM() LIMIT 1""",
        (unit_id, uid),
    )

    unit_finished = False
    if not q:
        unit_finished = True
        cur = db.execute(
            "INSERT INTO unit_progress (user_id, unit_id, completed) VALUES (%s, %s, %s) "
            "ON CONFLICT (user_id, unit_id) DO NOTHING",
            (uid, unit_id, True),
        )
        first_completion = cur.rowcount == 1
        cur.close()
        db.commit()

        if first_completion:
            trail_id = unit[1]
            total = db.fetchone("SELECT COUNT(*) FROM units WHERE trail_id=%s", (trail_id,))[0]
            done = db.fetchone(
                """SELECT COUNT(*) FROM unit_progress up JOIN units u ON up.unit_id = u.id
                   WHERE u.trail_id=%s AND up.user_id=%s AND up.completed=%s""",
                (trail_id, uid, True),
            )[0]
            if total > 0 and done >= total:
                check_and_award_badge(uid, "trilha_concluida")

    question_data = None
    if q:
        options_list = [opt for opt in (q[5], q[6], q[7], q[8]) if opt]
        if q[4] == "wordbank":
            random.shuffle(options_list)
        question_data = {"id": q[0], "question": q[1], "type": q[4], "options": options_list}

    return render_template(
        "unidade.html",
        unit={"id": unit[0], "title": unit[3], "intro": unit[4], "trail_id": unit[1]},
        question=question_data,
        unit_finished=unit_finished,
    )


# ==========================
# AUTENTICAÇÃO
# ==========================

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user():
        return redirect("/")

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            error = "Preencha todos os campos."
        elif len(username) > MAX_USERNAME_LEN:
            error = f"Nome de usuário muito longo (máx. {MAX_USERNAME_LEN} caracteres)."
        elif len(password) < MIN_PASSWORD_LEN:
            error = f"Senha muito curta (mín. {MIN_PASSWORD_LEN} caracteres)."
        else:
            db = get_db()
            try:
                # evita "Admin" / "admin" como contas diferentes
                if db.fetchone("SELECT 1 FROM users WHERE LOWER(username)=LOWER(%s)", (username,)):
                    error = "Este usuário já existe!"
                else:
                    db.execute(
                        "INSERT INTO users (username, password) VALUES (%s, %s)",
                        (username, generate_password_hash(password)),
                    ).close()
                    db.commit()
                    return redirect("/login")
            except INTEGRITY_ERRORS:
                db.rollback()
                error = "Este usuário já existe!"
            except DB_ERRORS:
                db.rollback()
                app.logger.exception("Erro de banco no cadastro")
                error = "Não foi possível acessar o banco de dados agora. Tente novamente em instantes."

    return render_template("register.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user():
        return redirect("/")

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            error = "Preencha todos os campos."
        else:
            try:
                user = get_db().fetchone(
                    "SELECT id, password, is_admin FROM users WHERE username=%s", (username,)
                )
            except DB_ERRORS:
                app.logger.exception("Erro de banco no login")
                user = False

            if user is False:
                error = "Não foi possível acessar o banco de dados agora. Tente novamente em instantes."
            elif user and check_password_hash(user[1], password):
                session.clear()
                session["user_id"] = user[0]
                session["is_admin"] = bool(user[2])
                session.permanent = True
                update_streak(user[0])
                check_and_award_badge(user[0], "primeiro_login")
                return redirect("/")
            else:
                error = "Usuário ou senha incorretos."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ==========================
# API DE RESPOSTA E CONQUISTAS
# ==========================

@app.route("/answer", methods=["POST"])
def answer():
    user = current_user()
    if not user:
        return jsonify({"error": "Acesso negado", "login_url": "/login"}), 403

    data = request.get_json(silent=True)
    if not isinstance(data, dict) or "id" not in data or "answer" not in data:
        return jsonify({"error": "Dados inválidos"}), 400
    try:
        question_id = int(data["id"])
    except (TypeError, ValueError):
        return jsonify({"error": "Dados inválidos"}), 400

    user_answer = str(data["answer"]).strip()
    if len(user_answer) > MAX_ANSWER_LEN:
        return jsonify({"error": "Resposta muito longa"}), 400

    db = get_db()
    uid = user["id"]

    row = db.fetchone("SELECT answer, unit_id FROM questions WHERE id=%s", (question_id,))
    if not row:
        return jsonify({"error": "Pergunta não encontrada"}), 404
    correct, unit_id = row

    if db.fetchone("SELECT 1 FROM answered WHERE user_id=%s AND question_id=%s", (uid, question_id)):
        return jsonify({"result": "already_answered"})

    is_correct = answers_match(user_answer, correct)

    # Registrar PRIMEIRO e só dar XP se a linha realmente entrou (clique duplo não duplica XP)
    cur = db.execute(
        "INSERT INTO answered (user_id, question_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
        (uid, question_id),
    )
    inserted = cur.rowcount == 1
    cur.close()
    if not inserted:
        db.rollback()
        return jsonify({"result": "already_answered"})

    xp_gained = 0
    if is_correct:
        db.execute("UPDATE users SET xp = COALESCE(xp, 0) + %s WHERE id=%s", (XP_PER_CORRECT, uid)).close()
        xp_gained = XP_PER_CORRECT
    db.commit()

    streak = update_streak(uid)

    xp_row = db.fetchone("SELECT xp FROM users WHERE id=%s", (uid,))
    xp_now = (xp_row[0] if xp_row else user["xp"] + xp_gained) or 0

    return jsonify({
        "result": "correct" if is_correct else "wrong",
        "correct_answer": correct,
        "unit_id": unit_id,
        "xp_gained": xp_gained,
        "xp": xp_now,
        "level": get_level(xp_now),
        "leveled_up": get_level(xp_now) > get_level(user["xp"]),
        "streak": streak,
        "new_badges": pop_pending_badges(),
    })


@app.route("/api/badges/pending")
def badges_pending():
    """Devolve (e limpa) as conquistas novas para o toast estilo Minecraft."""
    resp = jsonify({"badges": pop_pending_badges() if "user_id" in session else []})
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.route("/lab")
@login_required
def lab_redirect():
    """Abre o CodeQuest LAB já identificado (token assinado) e com o tema atual."""
    params = {"user_id": make_lab_token(current_user()["id"])}  # chave "user_id" mantida p/ compatibilidade
    theme = request.args.get("theme", "")
    if theme in ("dark", "light"):
        params["theme"] = theme
    sep = "&" if "?" in LAB_URL else "?"
    return redirect(f"{LAB_URL}{sep}{urlencode(params)}")


# ==========================
# PAINEL ADMIN / RANKING / PERFIL
# ==========================

@app.route("/admin")
@login_required
@admin_required(redirect_non_admin=True)
def admin():
    db = get_db()
    users = db.fetchall("SELECT id, username, xp, is_admin FROM users ORDER BY id ASC")
    questions = db.fetchall("SELECT id, question, difficulty FROM questions ORDER BY id DESC")
    return render_template("admin.html", users=users, questions=questions)


@app.route("/admin/set_xp", methods=["POST"])
@admin_required()
def set_xp():
    if not same_origin_request():
        return "Requisição bloqueada (origem inválida).", 403
    try:
        user_id = int(request.form.get("user_id"))
        xp = max(0, int(request.form.get("xp")))
    except (TypeError, ValueError):
        return "XP inválido", 400

    db = get_db()
    db.execute("UPDATE users SET xp=%s WHERE id=%s", (xp, user_id)).close()
    db.commit()
    return redirect("/admin")


@app.route("/admin/toggle_admin/<int:user_id>", methods=["GET", "POST"])
@admin_required()
def toggle_admin(user_id):
    if not same_origin_request():
        return "Requisição bloqueada (origem inválida).", 403
    if user_id == session.get("user_id"):
        return "Erro: você não pode remover seu próprio acesso.", 400

    db = get_db()
    row = db.fetchone("SELECT is_admin FROM users WHERE id=%s", (user_id,))
    if row:
        db.execute("UPDATE users SET is_admin=%s WHERE id=%s", (not bool(row[0]), user_id)).close()
        db.commit()
    return redirect("/admin")


@app.route("/admin/delete_user/<int:user_id>", methods=["GET", "POST"])
@admin_required()
def delete_user(user_id):
    if not same_origin_request():
        return "Requisição bloqueada (origem inválida).", 403
    if user_id == session.get("user_id"):
        return "Erro: você não pode deletar sua própria conta.", 400

    db = get_db()
    # lab_submissions primeiro: pode não existir em bancos antigos / ter user_id como texto.
    # Se falhar, desfaz só isso (ainda não há nada pendente) e segue.
    try:
        db.execute("DELETE FROM lab_submissions WHERE CAST(user_id AS TEXT)=%s", (str(user_id),)).close()
    except DB_ERRORS:
        db.rollback()
        app.logger.warning("Não foi possível limpar lab_submissions do usuário %s", user_id)

    for table in ("answered", "unit_progress", "user_badges"):
        db.execute(f"DELETE FROM {table} WHERE user_id=%s", (user_id,)).close()
    db.execute("DELETE FROM users WHERE id=%s", (user_id,)).close()
    db.commit()
    return redirect("/admin")


@app.route("/ranking")
def ranking():
    rows = get_db().fetchall("SELECT username, xp FROM users ORDER BY xp DESC, id ASC LIMIT 10")
    users = [{"username": r[0], "xp": r[1]} for r in rows]
    return render_template("ranking.html", users=users)


@app.route("/profile")
@login_required
def profile():
    user = current_user()
    db = get_db()

    rows = db.fetchall(
        """SELECT b.name, b.description, b.icon, ub.earned_at, b.code
           FROM user_badges ub JOIN badges b ON ub.badge_id = b.id
           WHERE ub.user_id=%s ORDER BY ub.earned_at ASC""",
        (user["id"],),
    )
    user_badges = [
        {"name": r[0], "description": r[1], "icon": r[2], "earned_at": r[3], "code": r[4]} for r in rows
    ]
    earned_codes = {b["code"] for b in user_badges}

    # catálogo completo (conquistadas + bloqueadas), útil p/ tela estilo Duolingo
    all_rows = db.fetchall("SELECT code, name, description, icon FROM badges ORDER BY id ASC")
    all_badges = [
        {"code": r[0], "name": r[1], "description": r[2], "icon": r[3], "earned": r[0] in earned_codes}
        for r in all_rows
    ]

    return render_template(
        "profile.html",
        username=user["username"],
        xp=user["xp"],
        level=get_level(user["xp"]),
        streak=user["streak"],
        badges=user_badges,
        all_badges=all_badges,
    )


@app.route("/health")
def health():
    try:
        get_db().fetchone("SELECT 1")
    except Exception:  # noqa: BLE001
        app.logger.exception("Health check falhou")
        return jsonify({"status": "error", "database": False}), 503
    return jsonify({"status": "ok", "database": "postgres" if IS_PG else "sqlite"})


# ==========================
# ERROS, CABEÇALHOS E INTEGRAÇÃO DO TOAST
# ==========================

def _wants_json():
    return request.path.startswith(("/answer", "/api/")) or request.accept_mimetypes.best == "application/json"


def _error_page(code, title, message):
    title, message = html.escape(title), html.escape(message)
    return (
        '<!DOCTYPE html><html lang="pt-br" data-theme="dark"><head><meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        f"<title>{title} - CodeQuest</title>"
        f'<link rel="stylesheet" href="/static/style.css?v={ASSET_VERSION}">'
        "<script>(function(){try{var t=localStorage.getItem('codequest_theme');"
        "if(t==='light'||t==='dark')document.documentElement.setAttribute('data-theme',t);}catch(e){}})();</script>"
        f'</head><body><div class="quiz"><h1>{code}</h1><h2>{title}</h2><p>{message}</p>'
        '<div class="btn-container"><a class="btn-jogar" href="/">Voltar ao início</a></div></div></body></html>'
    )


@app.errorhandler(Exception)
def handle_exception(exc):
    if isinstance(exc, HTTPException):
        if _wants_json():
            return jsonify({"error": exc.description}), exc.code
        if exc.code == 404:
            return _error_page(404, "Página não encontrada", "O endereço que você tentou abrir não existe."), 404
        return exc

    app.logger.exception("Erro não tratado em %s", request.path)
    if isinstance(exc, DB_ERRORS):
        code, msg = 503, "O banco de dados está indisponível no momento. Tente novamente em instantes."
    else:
        code, msg = 500, "Algo deu errado do nosso lado. Tente novamente em instantes."
    if _wants_json():
        return jsonify({"error": msg}), code
    return _error_page(code, "Ops!", msg), code


@app.context_processor
def inject_globals():
    return {"asset_v": ASSET_VERSION, "lab_url": LAB_URL}


@app.after_request
def after_request(resp):
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")

    if resp.mimetype == "text/html":
        resp.headers.setdefault("Cache-Control", "no-cache, private")
    elif request.path.startswith(("/api/", "/answer", "/health")):
        resp.headers["Cache-Control"] = "no-store"

    # Garante o toast de conquistas em TODAS as páginas HTML de usuário logado,
    # mesmo nas que não carregam achievements.js explicitamente.
    if (
        AUTO_INJECT_ACHIEVEMENTS
        and resp.status_code == 200
        and resp.mimetype == "text/html"
        and not resp.direct_passthrough
        and "user_id" in session
    ):
        body = resp.get_data(as_text=True)
        idx = body.rfind("</body>")
        if idx != -1 and "achievements.js" not in body:
            tag = (
                f'<script src="/static/achievements.js?v={ASSET_VERSION}" '
                'data-pending-url="/api/badges/pending" defer></script>'
            )
            resp.set_data(body[:idx] + tag + body[idx:])
    return resp


if __name__ == "__main__":
    app.run(
        debug=os.environ.get("FLASK_DEBUG", "1") == "1",
        port=int(os.environ.get("PORT", 5000)),
    )
