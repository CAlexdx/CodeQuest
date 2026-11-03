import csv
import hashlib
import html
import io
import logging
import os
import random
import re
import sqlite3
import unicodedata
from datetime import date, datetime, timedelta, timezone
from functools import wraps
from urllib.parse import urlencode, urlparse

from flask import Flask, Response, g, jsonify, redirect, render_template, request, session
from itsdangerous import URLSafeTimedSerializer
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash

from unit_cards import DISCIPLINAS, get_unit_content

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
VERCEL_ANALYTICS = os.environ.get("VERCEL_ANALYTICS", "0") == "1"  # ligue também no painel da Vercel
ASSET_VERSION = os.environ.get("ASSET_VERSION") or os.environ.get("VERCEL_GIT_COMMIT_SHA", "")[:7] or "1"

XP_PER_CORRECT = 10
XP_PER_LEVEL = 50
STREAK_BADGE_DAYS = 5
MAX_USERNAME_LEN = 15
MIN_PASSWORD_LEN = 4
MAX_ANSWER_LEN = 500
MAX_PENDING_BADGES = 6
LAB_TOKEN_SALT = "codequest-lab-v1"

HEARTS_MAX = 3            # corações por unidade
COMBO_FOR_HEART = 3       # 3 acertos seguidos devolvem 1 coração
REVIEW_XP_MULTIPLIER = 2  # Revisão de Falhas: XP em dobro
REVISOR_GOAL = 5          # erros corrigidos para a conquista "Aprendiz Persistente"
LAST_SEEN_THROTTLE_S = 60
ONLINE_WINDOW_MIN = 5
BUGHUNT_TOTAL = 8         # desafios existentes no LAB (só para mostrar "x/8")

# Atalhos "Praticar no LAB": ?to=<chave> -> caminho dentro do LAB
LAB_TARGETS = {
    "lab": "/",
    "python": "/sandbox?lang=python",
    "sql": "/sandbox?lang=sql",
    "js": "/sandbox?lang=javascript",
    "css": "/studio-css",
    "bughunt": "/bug-hunt",
}

# Conquistas conhecidas: se a linha ainda não existir na tabela `badges`
# (init_db.py não foi reexecutado), ela é criada sob demanda.
# (nome, descrição, ícone, secreta)
BADGE_DEFAULTS = {
    "primeiro_login": ("Primeiro Passo", "Realizou o primeiro acesso na plataforma CodeQuest.", "🚀", False),
    "trilha_concluida": ("Mestre das Trilhas", "Completou todas as unidades de uma trilha de aprendizado.", "🏆", False),
    "ofensiva_5": ("Chama Acesa", "Alcançou uma ofensiva de 5 dias seguidos.", "🔥", False),
    "lab_explorador": ("Explorador do LAB", "Visitou o CodeQuest LAB pela primeira vez.", "🧪", False),
    "mestre_bugs": ("Mestre dos Bugs", "Corrigiu vários desafios do Bug Hunt no CodeQuest LAB.", "🐛", False),
    "revisor": ("Aprendiz Persistente", "Corrigiu 5 erros na Revisão de Falhas.", "🔄", False),
    "notivago": ("Notívago", "Estudou de madrugada, entre 00h e 05h.", "🦉", True),
    "madrugador": ("Madrugador", "Estudou logo cedo, entre 05h e 07h.", "🌅", True),
    "perfeccionista": ("Perfeccionista", "Terminou uma unidade sem errar nenhuma pergunta.", "💎", True),
    "estilista_extremo": ("Estilista Extremo", "Levou todos os controles do Studio CSS ao máximo.", "🎨", True),
    "bug_hunter_pro": ("Bug Hunter Pro", "Resolveu um desafio do Bug Hunt de primeira, sem dicas e sem erros.", "🎯", True),
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


def safe_scalar(sql, params=(), default=0):
    """Consulta opcional (ex.: lab_submissions pode ter sido criada à mão): erro vira valor padrão."""
    db = get_db()
    try:
        row = db.fetchone(sql, params)
        return row[0] if row and row[0] is not None else default
    except DB_ERRORS:
        db.rollback()
        app.logger.warning("Consulta opcional falhou: %s", sql[:80])
        return default


# ==========================
# HELPERS
# ==========================

def get_level(xp):
    return (xp or 0) // XP_PER_LEVEL


def get_difficulty(level):
    """Dificuldade 'confortável' do jogador: as perguntas dentro dela são servidas primeiro."""
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


def _loose_key(texto):
    """Só letras e números (ignora espaços, hífens, pontos e '()'): 'createApp()' == 'createapp'."""
    return re.sub(r"[^a-z0-9]+", "", simplificar_texto(texto).replace("()", ""))


# Respostas alternativas aceitas (chave = resposta oficial já simplificada).
ALT_ANSWERS = {
    "2nf": ["2fn", "segunda forma normal", "segunda forma normal (2nf)"],
    "sql": ["structured query language"],
    "teste de turing": ["turing", "teste turing", "turing test"],
    "llm": ["large language model", "large language models", "llms"],
    "gan": ["gans", "generative adversarial network", "rede adversaria generativa"],
    "ai act": ["eu ai act", "lei de ia da uniao europeia"],
    "virtual dom": ["vdom", "dom virtual"],
    "linus torvalds": ["linus", "torvalds"],
    "desnormalizacao": ["desnormalizar", "denormalizacao"],
    "identacao": ["indentacao", "indentation"],
    "scrollview": ["scroll view"],
    "justifycontent": ["justify content", "justify-content"],
    "react navigation": ["react-navigation", "@react-navigation"],
    "neuronios": ["neuronio"],
    "historicos": ["historico", "historicas"],
}


def answers_match(user_answer, correct_answer):
    u = simplificar_texto(user_answer)
    c = simplificar_texto(correct_answer)
    if not u:
        return False
    if u == c:
        return True
    alts = ALT_ANSWERS.get(c, [])
    if u in alts:
        return True
    lu, lc = _loose_key(u), _loose_key(c)
    if lu and lc and lu == lc:
        return True
    return bool(lu) and any(_loose_key(a) == lu for a in alts)


def today_local():
    return datetime.now(APP_TZ).date()


def now_utc_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


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


def _parse_utc(value):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value)[:19])
    except ValueError:
        return None
    return dt.replace(tzinfo=timezone.utc)


def fmt_ago(value):
    """'agora', 'há 5 min', 'há 3 h', 'há 2 dias' a partir de um timestamp UTC."""
    dt = _parse_utc(value)
    if not dt:
        return "nunca"
    secs = max(0, int((datetime.now(timezone.utc) - dt).total_seconds()))
    if secs < 90:
        return "agora"
    if secs < 3600:
        return f"há {secs // 60} min"
    if secs < 86400:
        return f"há {secs // 3600} h"
    return f"há {secs // 86400} dia(s)"


def safe_next(value):
    """Só aceita caminhos internos (evita open redirect)."""
    if not value or not isinstance(value, str):
        return ""
    if not value.startswith("/") or value.startswith("//") or "\\" in value or "\n" in value or "\r" in value:
        return ""
    return value[:300]


def current_user():
    """Usuário logado (dict) ou None. Consulta o banco 1x por requisição e marca 'visto por último'."""
    if "current_user" in g:
        return g.current_user

    user = None
    try:
        uid = int(session.get("user_id"))
    except (TypeError, ValueError):
        uid = None

    if uid:
        db = get_db()
        row = db.fetchone(
            "SELECT id, username, xp, is_admin, streak, last_seen FROM users WHERE id=%s", (uid,)
        )
        if row:
            user = {
                "id": row[0],
                "username": row[1],
                "xp": row[2] or 0,
                "is_admin": bool(row[3]),
                "streak": row[4] or 0,
                "last_seen": row[5],
            }
            # mantém session.is_admin atualizado (templates antigos usam session.is_admin)
            if session.get("is_admin") != user["is_admin"]:
                session["is_admin"] = user["is_admin"]
            _touch_last_seen(db, user)

    g.current_user = user
    return user


def _touch_last_seen(db, user):
    """Grava 'visto por último' no máx. 1x por minuto por aluno (barato e sem contador no código)."""
    seen = _parse_utc(user.get("last_seen"))
    if seen and (datetime.now(timezone.utc) - seen).total_seconds() < LAST_SEEN_THROTTLE_S:
        return
    try:
        stamp = now_utc_iso()
        db.execute("UPDATE users SET last_seen=%s WHERE id=%s", (stamp, user["id"])).close()
        db.commit()
        user["last_seen"] = stamp
    except DB_ERRORS:
        db.rollback()  # coluna ainda não existe (init_db.py não rodou) ou erro transitório: segue sem


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            session.clear()  # sessão antiga/usuário removido
            if request.method == "GET":
                nxt = request.full_path.rstrip("?")
                return redirect("/login?" + urlencode({"next": nxt}) if safe_next(nxt) and nxt != "/" else "/login")
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
    row = db.fetchone("SELECT id, name, description, icon, secret FROM badges WHERE code=%s", (badge_code,))
    if not row and badge_code in BADGE_DEFAULTS:
        name, desc, icon, secret = BADGE_DEFAULTS[badge_code]
        db.execute(
            "INSERT INTO badges (code, name, description, icon, secret) VALUES (%s, %s, %s, %s, %s) "
            "ON CONFLICT (code) DO NOTHING",
            (badge_code, name, desc, icon, secret),
        ).close()
        row = db.fetchone("SELECT id, name, description, icon, secret FROM badges WHERE code=%s", (badge_code,))
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
    return {"code": badge_code, "name": row[1], "description": row[2], "icon": row[3], "secret": bool(row[4])}


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


def award_time_badges(user_id):
    """Conquistas secretas por horário de estudo (fuso do app)."""
    hour = datetime.now(APP_TZ).hour
    if 0 <= hour < 5:
        check_and_award_badge(user_id, "notivago")
    elif 5 <= hour < 7:
        check_and_award_badge(user_id, "madrugador")


# ---------- Ponte com o CodeQuest LAB ----------

def make_lab_token(user_id):
    """Token assinado e com validade (o LAB confere a assinatura; id puro na URL seria falsificável)."""
    return URLSafeTimedSerializer(LAB_SECRET, salt=LAB_TOKEN_SALT).dumps({"uid": int(user_id)})


def build_lab_url(to="", theme=""):
    """URL do LAB: tema na query e token no FRAGMENTO (#), que não vai para logs nem para o Referer."""
    path = LAB_TARGETS.get(to, "/")
    base = LAB_URL.rstrip("/")
    params = {}
    if theme in ("dark", "light"):
        params["theme"] = theme
    sep = "&" if "?" in path else "?"
    query = f"{sep}{urlencode(params)}" if params else ""
    token = make_lab_token(current_user()["id"])
    return f"{base}{path}{query}#{urlencode({'cq': token})}"


# ---------- Estado da unidade (teoria + corações) ----------

def get_unit_state(db, user_id, unit_id):
    row = db.fetchone(
        "SELECT theory_read, hearts, combo FROM unit_state WHERE user_id=%s AND unit_id=%s", (user_id, unit_id)
    )
    if not row:
        return {"theory_read": False, "hearts": HEARTS_MAX, "combo": 0}
    return {
        "theory_read": bool(row[0]),
        "hearts": HEARTS_MAX if row[1] is None else max(0, min(HEARTS_MAX, row[1])),
        "combo": row[2] or 0,
    }


def save_unit_state(db, user_id, unit_id, state):
    db.execute(
        "INSERT INTO unit_state (user_id, unit_id, theory_read, hearts, combo) VALUES (%s, %s, %s, %s, %s) "
        "ON CONFLICT (user_id, unit_id) DO UPDATE SET "
        "theory_read=excluded.theory_read, hearts=excluded.hearts, combo=excluded.combo",
        (user_id, unit_id, bool(state["theory_read"]), int(state["hearts"]), int(state["combo"])),
    ).close()


def unit_is_unlocked(db, user_id, trail_id, unit_order):
    """Progressão: todas as unidades anteriores da trilha precisam estar concluídas."""
    pending = db.fetchone(
        """SELECT COUNT(*) FROM units u
           WHERE u.trail_id=%s AND u.unit_order < %s
             AND NOT EXISTS (SELECT 1 FROM unit_progress up
                             WHERE up.unit_id=u.id AND up.user_id=%s AND up.completed=%s)""",
        (trail_id, unit_order, user_id, True),
    )[0]
    return pending == 0


def count_errors(db, user_id):
    """Questões erradas que ainda não foram corrigidas na Revisão de Falhas."""
    return db.fetchone(
        "SELECT COUNT(*) FROM answered WHERE user_id=%s AND correct=%s AND fixed=%s", (user_id, False, False)
    )[0]


def next_unit(db, user_id):
    """Primeira unidade ainda não concluída (para o botão 'Continuar')."""
    rows = db.fetchall(
        """SELECT u.id, u.title, t.name, t.icon, u.unit_order
           FROM units u JOIN trails t ON t.id = u.trail_id
           ORDER BY t.trail_order ASC, u.unit_order ASC"""
    )
    done = {r[0] for r in db.fetchall("SELECT unit_id FROM unit_progress WHERE user_id=%s AND completed=%s", (user_id, True))}
    for r in rows:
        if r[0] not in done:
            return {"id": r[0], "title": r[1], "trail": r[2], "icon": r[3], "order": r[4]}
    return None


# ==========================
# ROTAS PRINCIPAIS
# ==========================

QUESTION_COLS = "id, question, answer, difficulty, type, opt1, opt2, opt3, opt4"


@app.route("/")
@login_required
def home():
    user = current_user()
    db = get_db()
    uid = user["id"]

    level = get_level(user["xp"])
    errors_count = count_errors(db, uid)
    lab_solved = safe_scalar(
        "SELECT COUNT(DISTINCT CAST(challenge_id AS TEXT)) FROM lab_submissions "
        "WHERE CAST(user_id AS TEXT)=%s AND passed=%s",
        (str(uid), True),
    )

    return render_template(
        "index.html",
        username=user["username"],
        xp=user["xp"],
        xp_next=(level + 1) * XP_PER_LEVEL,
        level=level,
        streak=user["streak"],
        is_admin=user["is_admin"],
        errors_count=errors_count,
        next_unit=next_unit(db, uid),
        lab_solved=lab_solved,
        bughunt_total=BUGHUNT_TOTAL,
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
            "discipline": DISCIPLINAS.get(r[0], ""),
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


def _unit_counts(db, user_id, unit_id):
    total = db.fetchone("SELECT COUNT(*) FROM questions WHERE unit_id=%s", (unit_id,))[0]
    done = db.fetchone(
        "SELECT COUNT(*) FROM answered a JOIN questions q ON q.id = a.question_id "
        "WHERE a.user_id=%s AND q.unit_id=%s",
        (user_id, unit_id),
    )[0]
    return done, total


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

    if not unit_is_unlocked(db, uid, unit[1], unit[2]):
        return redirect(f"/trilhas/{unit[1]}")

    level = get_level(user["xp"])
    q = db.fetchone(
        f"""SELECT {QUESTION_COLS} FROM questions q
            WHERE q.unit_id=%s
              AND NOT EXISTS (SELECT 1 FROM answered a WHERE a.user_id=%s AND a.question_id=q.id)
            ORDER BY CASE WHEN q.difficulty <= %s THEN 0 ELSE 1 END, q.difficulty, RANDOM() LIMIT 1""",
        (unit_id, uid, get_difficulty(level)),
    )

    unit_finished = False
    perfect = False
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

        wrong = db.fetchone(
            "SELECT COUNT(*) FROM answered a JOIN questions q ON q.id=a.question_id "
            "WHERE a.user_id=%s AND q.unit_id=%s AND a.correct=%s",
            (uid, unit_id, False),
        )[0]
        perfect = wrong == 0

    content = get_unit_content(unit[1], unit[2])
    cards = content["cards"] or [
        {"titulo": "Resumo da unidade", "texto": unit[4], "topicos": [], "codigo": "", "dica": ""}
    ]
    state = get_unit_state(db, uid, unit_id)
    must_read = (not state["theory_read"]) or state["hearts"] <= 0
    force_theory = request.args.get("teoria") == "1"

    if unit_finished:
        view = "teoria" if force_theory else "finished"
        must_read = False
    else:
        view = "teoria" if (must_read or force_theory) else "quiz"

    question_data = None
    if q:
        options_list = [opt for opt in (q[5], q[6], q[7], q[8]) if opt]
        if q[4] in ("multiple", "wordbank"):
            random.shuffle(options_list)  # a posição da resposta certa muda a cada vez (sem decorar o "chute")
        question_data = {"id": q[0], "question": q[1], "type": q[4], "options": options_list}

    done_count, total_count = _unit_counts(db, uid, unit_id)
    lab_key = content.get("lab")

    return render_template(
        "unidade.html",
        unit={"id": unit[0], "title": unit[3], "intro": unit[4], "trail_id": unit[1], "order": unit[2]},
        question=question_data,
        unit_finished=unit_finished,
        perfect=perfect,
        view=view,
        cards=cards,
        must_read=must_read,
        out_of_hearts=(not unit_finished) and state["hearts"] <= 0,
        hearts=state["hearts"],
        hearts_max=HEARTS_MAX,
        done_count=done_count,
        total_count=total_count,
        discipline=DISCIPLINAS.get(unit[1], ""),
        base_note=content.get("base", ""),
        lab_link=f"/lab?to={lab_key}" if lab_key in LAB_TARGETS else "",
    )


@app.route("/api/unidade/<int:unit_id>/teoria", methods=["POST"])
def unidade_teoria(unit_id):
    """O aluno terminou de ler os cards: libera as perguntas e, se estava sem corações, recarrega."""
    user = current_user()
    if not user:
        return jsonify({"error": "Acesso negado", "login_url": "/login"}), 403
    db = get_db()
    unit = db.fetchone("SELECT id, trail_id, unit_order FROM units WHERE id=%s", (unit_id,))
    if not unit:
        return jsonify({"error": "Unidade não encontrada"}), 404
    if not unit_is_unlocked(db, user["id"], unit[1], unit[2]):
        return jsonify({"error": "Unidade bloqueada"}), 403

    state = get_unit_state(db, user["id"], unit_id)
    refilled = state["hearts"] <= 0
    state["theory_read"] = True
    if refilled:
        state["hearts"] = HEARTS_MAX
        state["combo"] = 0
    save_unit_state(db, user["id"], unit_id, state)
    db.commit()
    return jsonify({"ok": True, "hearts": state["hearts"], "refilled": refilled})


# ==========================
# REVISÃO DE FALHAS (BANCO DE ERROS)
# ==========================

@app.route("/revisao")
@login_required
def revisao():
    user = current_user()
    db = get_db()
    uid = user["id"]

    total_errors = count_errors(db, uid)
    try:
        skip = int(request.args.get("skip", 0))
    except ValueError:
        skip = 0

    base_sql = (
        f"""SELECT q.id, q.question, q.answer, q.difficulty, q.type, q.opt1, q.opt2, q.opt3, q.opt4,
                   u.title, u.id
            FROM answered a
            JOIN questions q ON q.id = a.question_id
            JOIN units u ON u.id = q.unit_id
            WHERE a.user_id=%s AND a.correct=%s AND a.fixed=%s"""
    )
    row = None
    if skip:
        row = db.fetchone(base_sql + " AND q.id <> %s ORDER BY RANDOM() LIMIT 1", (uid, False, False, skip))
    if not row:
        row = db.fetchone(base_sql + " ORDER BY RANDOM() LIMIT 1", (uid, False, False))

    question_data = None
    unit_title = ""
    unit_id = None
    if row:
        options_list = [opt for opt in (row[5], row[6], row[7], row[8]) if opt]
        if row[4] in ("multiple", "wordbank"):
            random.shuffle(options_list)
        question_data = {"id": row[0], "question": row[1], "type": row[4], "options": options_list}
        unit_title, unit_id = row[9], row[10]

    return render_template(
        "revisao.html",
        question=question_data,
        total_errors=total_errors,
        unit_title=unit_title,
        unit_id=unit_id,
        xp_reward=XP_PER_CORRECT * REVIEW_XP_MULTIPLIER,
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
        elif not re.fullmatch(r"[A-Za-z0-9]+", username):
            error = "Use apenas letras e números no usuário, sem espaços."
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
                    nxt = safe_next(request.args.get("next"))
                    return redirect("/login?" + urlencode({"next": nxt}) if nxt else "/login")
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
    nxt = safe_next(request.args.get("next"))
    if current_user():
        return redirect(nxt or "/")

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
                return redirect(nxt or "/")
            else:
                error = "Usuário ou senha incorretos."

    return render_template("login.html", error=error, next_url=nxt)


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

    mode = "review" if data.get("mode") == "review" else "unit"
    db = get_db()
    uid = user["id"]

    row = db.fetchone(
        "SELECT q.answer, q.unit_id, u.trail_id, u.unit_order FROM questions q "
        "JOIN units u ON u.id = q.unit_id WHERE q.id=%s",
        (question_id,),
    )
    if not row:
        return jsonify({"error": "Pergunta não encontrada"}), 404
    correct, unit_id, trail_id, unit_order = row
    is_correct = answers_match(user_answer, correct)

    if mode == "review":
        return _answer_review(db, user, question_id, correct, unit_id, is_correct)

    # ---------------- modo unidade ----------------
    if not unit_is_unlocked(db, uid, trail_id, unit_order):
        return jsonify({"error": "Unidade bloqueada"}), 403

    state = get_unit_state(db, uid, unit_id)
    if not state["theory_read"] or state["hearts"] <= 0:
        return jsonify({"result": "theory_required", "error": "Leia o resumo da unidade para continuar."}), 409

    if db.fetchone("SELECT 1 FROM answered WHERE user_id=%s AND question_id=%s", (uid, question_id)):
        return jsonify({"result": "already_answered"})

    # Registrar PRIMEIRO e só dar XP se a linha realmente entrou (clique duplo não duplica XP)
    cur = db.execute(
        "INSERT INTO answered (user_id, question_id, correct, fixed, answered_at) "
        "VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
        (uid, question_id, bool(is_correct), False, now_utc_iso()),
    )
    inserted = cur.rowcount == 1
    cur.close()
    if not inserted:
        db.rollback()
        return jsonify({"result": "already_answered"})

    xp_gained = 0
    heart_regained = False
    if is_correct:
        db.execute("UPDATE users SET xp = COALESCE(xp, 0) + %s WHERE id=%s", (XP_PER_CORRECT, uid)).close()
        xp_gained = XP_PER_CORRECT
        state["combo"] += 1
        if state["combo"] >= COMBO_FOR_HEART:
            state["combo"] = 0
            if state["hearts"] < HEARTS_MAX:
                state["hearts"] += 1
                heart_regained = True
    else:
        state["hearts"] = max(0, state["hearts"] - 1)
        state["combo"] = 0
    save_unit_state(db, uid, unit_id, state)
    db.commit()

    streak = update_streak(uid)
    award_time_badges(uid)

    done_count, total_count = _unit_counts(db, uid, unit_id)
    unit_complete = done_count >= total_count
    if unit_complete:
        wrong = db.fetchone(
            "SELECT COUNT(*) FROM answered a JOIN questions q ON q.id=a.question_id "
            "WHERE a.user_id=%s AND q.unit_id=%s AND a.correct=%s",
            (uid, unit_id, False),
        )[0]
        if wrong == 0:
            check_and_award_badge(uid, "perfeccionista")

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
        "hearts": state["hearts"],
        "hearts_max": HEARTS_MAX,
        "heart_regained": heart_regained,
        "out_of_hearts": state["hearts"] <= 0 and not unit_complete,
        "done": done_count,
        "total": total_count,
        "unit_complete": unit_complete,
        "new_badges": pop_pending_badges(),
    })


def _answer_review(db, user, question_id, correct, unit_id, is_correct):
    """Revisão de Falhas: só aceita perguntas que o aluno errou e ainda não corrigiu."""
    uid = user["id"]
    row = db.fetchone("SELECT correct, fixed FROM answered WHERE user_id=%s AND question_id=%s", (uid, question_id))
    if not row or row[0] is None or bool(row[0]) or bool(row[1]):
        return jsonify({"error": "Esta questão não está no seu banco de erros.", "result": "not_in_review"}), 400

    xp_gained = 0
    fixed_now = False
    if is_correct:
        cur = db.execute(
            "UPDATE answered SET fixed=%s WHERE user_id=%s AND question_id=%s AND fixed=%s",
            (True, uid, question_id, False),
        )
        fixed_now = cur.rowcount == 1
        cur.close()
        if fixed_now:
            xp_gained = XP_PER_CORRECT * REVIEW_XP_MULTIPLIER
            db.execute("UPDATE users SET xp = COALESCE(xp, 0) + %s WHERE id=%s", (xp_gained, uid)).close()
        db.commit()

    streak = update_streak(uid)
    award_time_badges(uid)
    if fixed_now:
        fixed_total = db.fetchone(
            "SELECT COUNT(*) FROM answered WHERE user_id=%s AND fixed=%s", (uid, True)
        )[0]
        if fixed_total >= REVISOR_GOAL:
            check_and_award_badge(uid, "revisor")

    xp_row = db.fetchone("SELECT xp FROM users WHERE id=%s", (uid,))
    xp_now = (xp_row[0] if xp_row else user["xp"] + xp_gained) or 0
    return jsonify({
        "result": "correct" if is_correct else "wrong",
        "mode": "review",
        "correct_answer": correct,
        "unit_id": unit_id,
        "xp_gained": xp_gained,
        "xp": xp_now,
        "level": get_level(xp_now),
        "leveled_up": get_level(xp_now) > get_level(user["xp"]),
        "streak": streak,
        "errors_left": count_errors(db, uid),
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
    """Abre o CodeQuest LAB já identificado (token assinado), com o tema atual e, se pedido, na ferramenta certa."""
    return redirect(build_lab_url(request.args.get("to", ""), request.args.get("theme", "")))


# ==========================
# PAINEL ADMIN / RANKING / PERFIL
# ==========================

def _admin_metrics(db):
    now = datetime.now(timezone.utc)
    online_since = (now - timedelta(minutes=ONLINE_WINDOW_MIN)).strftime("%Y-%m-%dT%H:%M:%S")
    start_today_local = datetime.combine(today_local(), datetime.min.time(), tzinfo=APP_TZ)
    today_since = start_today_local.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    total_answers = db.fetchone("SELECT COUNT(*) FROM answered")[0]
    correct_answers = db.fetchone("SELECT COUNT(*) FROM answered WHERE correct=%s", (True,))[0]
    m = {
        "users_total": db.fetchone("SELECT COUNT(*) FROM users")[0],
        "online_now": db.fetchone("SELECT COUNT(*) FROM users WHERE last_seen >= %s", (online_since,))[0],
        "active_today": db.fetchone("SELECT COUNT(*) FROM users WHERE last_seen >= %s", (today_since,))[0],
        "answers_total": total_answers,
        "accuracy": round(100 * correct_answers / total_answers) if total_answers else 0,
        "units_done": db.fetchone("SELECT COUNT(*) FROM unit_progress WHERE completed=%s", (True,))[0],
        "errors_pending": db.fetchone("SELECT COUNT(*) FROM answered WHERE correct=%s AND fixed=%s", (False, False))[0],
        "errors_fixed": db.fetchone("SELECT COUNT(*) FROM answered WHERE fixed=%s", (True,))[0],
        "hearts_empty": db.fetchone("SELECT COUNT(*) FROM unit_state WHERE hearts <= 0")[0],
        "bughunt_solved": safe_scalar(
            "SELECT COUNT(DISTINCT CAST(user_id AS TEXT) || '-' || CAST(challenge_id AS TEXT)) "
            "FROM lab_submissions WHERE passed=%s", (True,)),
        "bughunt_attempts": safe_scalar("SELECT COUNT(*) FROM lab_submissions"),
        "badges_total": db.fetchone("SELECT COUNT(*) FROM user_badges")[0],
        "online_window": ONLINE_WINDOW_MIN,
    }
    m["trails"] = [
        {"name": r[0], "icon": r[1], "done": r[2], "units": r[3]}
        for r in db.fetchall(
            """SELECT t.name, t.icon,
                      (SELECT COUNT(*) FROM unit_progress up JOIN units u ON u.id = up.unit_id
                        WHERE u.trail_id = t.id AND up.completed = %s),
                      (SELECT COUNT(*) FROM units u2 WHERE u2.trail_id = t.id)
               FROM trails t ORDER BY t.trail_order ASC""",
            (True,),
        )
    ]
    since = (now - timedelta(days=6)).strftime("%Y-%m-%d")
    per_day = {
        r[0]: r[1]
        for r in db.fetchall(
            "SELECT SUBSTR(answered_at, 1, 10), COUNT(*) FROM answered "
            "WHERE answered_at >= %s GROUP BY SUBSTR(answered_at, 1, 10)",
            (since,),
        )
    }
    days = []
    for i in range(6, -1, -1):
        d = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        days.append({"label": d[8:10] + "/" + d[5:7], "count": per_day.get(d, 0)})
    peak = max([d["count"] for d in days] + [1])
    for d in days:
        d["pct"] = int(100 * d["count"] / peak)
    m["days"] = days
    return m


def _admin_users(db):
    rows = db.fetchall(
        """SELECT u.id, u.username, u.xp, u.is_admin, u.streak, u.last_seen,
                  (SELECT COUNT(*) FROM answered a WHERE a.user_id = u.id),
                  (SELECT COUNT(*) FROM answered a WHERE a.user_id = u.id AND a.correct = %s),
                  (SELECT COUNT(*) FROM unit_progress p WHERE p.user_id = u.id AND p.completed = %s)
           FROM users u ORDER BY u.id ASC""",
        (True, True),
    )
    online_since = datetime.now(timezone.utc) - timedelta(minutes=ONLINE_WINDOW_MIN)
    out = []
    for r in rows:
        seen = _parse_utc(r[5])
        out.append({
            "id": r[0], "username": r[1], "xp": r[2] or 0, "is_admin": bool(r[3]), "streak": r[4] or 0,
            "last_seen": fmt_ago(r[5]), "last_seen_raw": r[5] or "",
            "online": bool(seen and seen >= online_since),
            "answers": r[6], "correct": r[7], "units": r[8],
            "accuracy": round(100 * r[7] / r[6]) if r[6] else None,
        })
    return out


@app.route("/admin")
@login_required
@admin_required(redirect_non_admin=True)
def admin():
    db = get_db()
    users = _admin_users(db)
    questions = db.fetchall("SELECT id, question, difficulty FROM questions ORDER BY id DESC LIMIT 10")
    total_questions = db.fetchone("SELECT COUNT(*) FROM questions")[0]
    return render_template(
        "admin.html",
        users=users,
        questions=questions,
        total_questions=total_questions,
        metrics=_admin_metrics(db),
        lab_url=LAB_URL,
        analytics_on=VERCEL_ANALYTICS,
        current_admin_id=current_user()["id"],
    )


def _csv_safe(value):
    """Evita 'injeção de fórmula' ao abrir o CSV no Excel."""
    text = "" if value is None else str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@", "\t", "\r") else text


@app.route("/admin/export.csv")
@admin_required()
def admin_export():
    out = io.StringIO()
    writer = csv.writer(out, delimiter=";")
    writer.writerow(["id", "usuario", "xp", "nivel", "ofensiva", "respostas", "acertos", "taxa_acerto_%",
                     "unidades_concluidas", "visto_por_ultimo_utc"])
    for u in _admin_users(get_db()):
        writer.writerow([
            u["id"], _csv_safe(u["username"]), u["xp"], get_level(u["xp"]), u["streak"], u["answers"],
            u["correct"], "" if u["accuracy"] is None else u["accuracy"], u["units"], u["last_seen_raw"],
        ])
    data = "﻿" + out.getvalue()  # BOM: o Excel abre os acentos certinho
    return Response(
        data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=codequest-usuarios.csv"},
    )


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

    for table in ("answered", "unit_progress", "user_badges", "unit_state"):
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
    uid = user["id"]

    rows = db.fetchall(
        """SELECT b.name, b.description, b.icon, ub.earned_at, b.code, b.secret
           FROM user_badges ub JOIN badges b ON ub.badge_id = b.id
           WHERE ub.user_id=%s ORDER BY ub.earned_at ASC""",
        (uid,),
    )
    user_badges = [
        {"name": r[0], "description": r[1], "icon": r[2], "earned_at": r[3], "code": r[4], "secret": bool(r[5])}
        for r in rows
    ]
    earned_codes = {b["code"] for b in user_badges}

    # catálogo: as secretas só aparecem depois de conquistadas (as outras aparecem bloqueadas)
    all_rows = db.fetchall("SELECT code, name, description, icon, secret FROM badges ORDER BY id ASC")
    locked_badges = [
        {"code": r[0], "name": r[1], "description": r[2], "icon": r[3]}
        for r in all_rows if r[0] not in earned_codes and not r[4]
    ]
    hidden_secrets = sum(1 for r in all_rows if r[4] and r[0] not in earned_codes)

    answers = db.fetchone("SELECT COUNT(*) FROM answered WHERE user_id=%s", (uid,))[0]
    correct = db.fetchone("SELECT COUNT(*) FROM answered WHERE user_id=%s AND correct=%s", (uid, True))[0]
    stats = {
        "answers": answers,
        "accuracy": round(100 * correct / answers) if answers else 0,
        "units": db.fetchone("SELECT COUNT(*) FROM unit_progress WHERE user_id=%s AND completed=%s", (uid, True))[0],
        "errors": count_errors(db, uid),
        "fixed": db.fetchone("SELECT COUNT(*) FROM answered WHERE user_id=%s AND fixed=%s", (uid, True))[0],
        "bughunt": safe_scalar(
            "SELECT COUNT(DISTINCT CAST(challenge_id AS TEXT)) FROM lab_submissions "
            "WHERE CAST(user_id AS TEXT)=%s AND passed=%s", (str(uid), True)),
        "bughunt_total": BUGHUNT_TOTAL,
    }

    return render_template(
        "profile.html",
        username=user["username"],
        xp=user["xp"],
        level=get_level(user["xp"]),
        streak=user["streak"],
        badges=user_badges,
        locked_badges=locked_badges,
        hidden_secrets=hidden_secrets,
        stats=stats,
    )


@app.route("/health")
def health():
    db = get_db()
    try:
        db.fetchone("SELECT 1")
    except Exception:  # noqa: BLE001
        app.logger.exception("Health check falhou")
        return jsonify({"status": "error", "database": False}), 503
    try:  # confere se o init_db.py desta versão já foi executado
        db.fetchone("SELECT hearts FROM unit_state LIMIT 1")
        db.fetchone("SELECT correct, fixed FROM answered LIMIT 1")
        db.fetchone("SELECT last_seen FROM users LIMIT 1")
        db.fetchone("SELECT secret FROM badges LIMIT 1")
        schema = "ok"
    except DB_ERRORS:
        db.rollback()
        schema = "desatualizado: rode python init_db.py"
    return jsonify({"status": "ok", "database": "postgres" if IS_PG else "sqlite", "schema": schema})


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


_ANALYTICS_TAG = (
    "<script>window.va=window.va||function(){(window.vaq=window.vaq||[]).push(arguments);};</script>"
    '<script defer src="/_vercel/insights/script.js"></script>'
)


@app.after_request
def after_request(resp):
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")

    if resp.mimetype == "text/html":
        resp.headers.setdefault("Cache-Control", "no-cache, private")
    elif request.path.startswith(("/api/", "/answer", "/health")):
        resp.headers["Cache-Control"] = "no-store"

    # Injeta, antes de </body>: o toast de conquistas (usuário logado) e o Vercel Analytics (se ligado).
    if resp.status_code == 200 and resp.mimetype == "text/html" and not resp.direct_passthrough:
        want_toast = AUTO_INJECT_ACHIEVEMENTS and "user_id" in session
        if want_toast or VERCEL_ANALYTICS:
            body = resp.get_data(as_text=True)
            idx = body.rfind("</body>")
            extra = ""
            if idx != -1:
                if want_toast and "achievements.js" not in body:
                    extra += (
                        f'<script src="/static/achievements.js?v={ASSET_VERSION}" '
                        'data-pending-url="/api/badges/pending" defer></script>'
                    )
                if VERCEL_ANALYTICS and "_vercel/insights" not in body:
                    extra += _ANALYTICS_TAG
                if extra:
                    resp.set_data(body[:idx] + extra + body[idx:])
    return resp


if __name__ == "__main__":
    app.run(
        debug=os.environ.get("FLASK_DEBUG", "1") == "1",
        port=int(os.environ.get("PORT", 5000)),
    )
