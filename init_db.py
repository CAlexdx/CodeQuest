import os
import secrets
import sqlite3
import sys

from werkzeug.security import check_password_hash, generate_password_hash

from seed_data import RAW_DATA, TRAILS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
IS_PG = bool(DATABASE_URL)
SQLITE_PATH = os.path.join(BASE_DIR, "database.db")

# Catálogo de conquistas. (code, nome, descrição, ícone)
# Os mesmos códigos são usados pelo app principal e pelo CodeQuest LAB.
BADGES = [
    ("primeiro_login", "Primeiro Passo", "Realizou o primeiro acesso na plataforma CodeQuest.", "🚀"),
    ("trilha_concluida", "Mestre das Trilhas", "Completou todas as unidades de uma trilha de aprendizado.", "🏆"),
    ("ofensiva_5", "Chama Acesa", "Alcançou uma ofensiva de 5 dias seguidos.", "🔥"),
    ("lab_explorador", "Explorador do LAB", "Visitou o CodeQuest LAB pela primeira vez.", "🧪"),
    ("mestre_bugs", "Mestre dos Bugs", "Corrigiu desafios do Bug Hunt no CodeQuest LAB.", "🐛"),
]

TABLES = [
    "users", "trails", "units", "questions", "unit_progress",
    "answered", "badges", "user_badges", "lab_submissions",
]


# ---------------------------------------------------------------------------
# Camada fina de banco: o SQL é escrito com %s e convertido para ? no SQLite.
# ---------------------------------------------------------------------------
class DB:
    def __init__(self, conn):
        self.conn = conn

    def execute(self, sql, params=()):
        cur = self.conn.cursor()
        cur.execute(sql if IS_PG else sql.replace("%s", "?"), tuple(params))
        return cur

    def one(self, sql, params=()):
        cur = self.execute(sql, params)
        try:
            return cur.fetchone()
        finally:
            cur.close()

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()

    def optional(self, sql, label):
        """Executa um passo opcional; se falhar, desfaz só ele e segue em frente."""
        try:
            if IS_PG:
                self.execute("SAVEPOINT cq_optional")
            self.execute(sql).close()
            if IS_PG:
                self.execute("RELEASE SAVEPOINT cq_optional")
            return True
        except Exception as exc:  # noqa: BLE001 - passo opcional, só avisamos
            if IS_PG:
                self.execute("ROLLBACK TO SAVEPOINT cq_optional")
            print(f"   (aviso) passo opcional ignorado [{label}]: {exc}")
            return False


def connect():
    if IS_PG:
        import psycopg2

        kwargs = {"connect_timeout": 15}
        if "sslmode" not in DATABASE_URL:
            kwargs["sslmode"] = os.environ.get(
                "DB_SSLMODE", "require" if "supabase" in DATABASE_URL else "prefer"
            )
        return DB(psycopg2.connect(DATABASE_URL, **kwargs))
    return DB(sqlite3.connect(SQLITE_PATH, timeout=15))


# ---------------------------------------------------------------------------
# Etapas
# ---------------------------------------------------------------------------
def create_tables(db):
    pk = "SERIAL PRIMARY KEY" if IS_PG else "INTEGER PRIMARY KEY AUTOINCREMENT"

    db.execute(f"""
        CREATE TABLE IF NOT EXISTS users (
            id {pk},
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            xp INTEGER DEFAULT 0,
            streak INTEGER DEFAULT 0,
            last_active TEXT DEFAULT NULL,
            is_admin BOOLEAN DEFAULT FALSE
        )""")
    db.execute(f"""
        CREATE TABLE IF NOT EXISTS trails (
            id {pk},
            name TEXT NOT NULL,
            icon TEXT NOT NULL,
            description TEXT NOT NULL,
            color TEXT NOT NULL,
            trail_order INTEGER NOT NULL
        )""")
    db.execute(f"""
        CREATE TABLE IF NOT EXISTS units (
            id {pk},
            trail_id INTEGER NOT NULL,
            unit_order INTEGER NOT NULL,
            title TEXT NOT NULL,
            intro_text TEXT NOT NULL
        )""")
    db.execute(f"""
        CREATE TABLE IF NOT EXISTS questions (
            id {pk},
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            difficulty INTEGER NOT NULL DEFAULT 1,
            type TEXT NOT NULL DEFAULT 'multiple',
            opt1 TEXT, opt2 TEXT, opt3 TEXT, opt4 TEXT,
            unit_id INTEGER NOT NULL
        )""")
    db.execute("""
        CREATE TABLE IF NOT EXISTS unit_progress (
            user_id INTEGER NOT NULL,
            unit_id INTEGER NOT NULL,
            completed BOOLEAN DEFAULT FALSE,
            PRIMARY KEY (user_id, unit_id)
        )""")
    db.execute("""
        CREATE TABLE IF NOT EXISTS answered (
            user_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL
        )""")
    db.execute(f"""
        CREATE TABLE IF NOT EXISTS badges (
            id {pk},
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            icon TEXT NOT NULL
        )""")
    db.execute("""
        CREATE TABLE IF NOT EXISTS user_badges (
            user_id INTEGER NOT NULL,
            badge_id INTEGER NOT NULL,
            earned_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, badge_id)
        )""")
    # Histórico de tentativas do CodeQuest LAB (Bug Hunt).
    # Se a tabela já existir (criada à mão no Supabase), ela é mantida como está.
    db.execute(f"""
        CREATE TABLE IF NOT EXISTS lab_submissions (
            id {pk},
            user_id INTEGER NOT NULL,
            challenge_id TEXT NOT NULL,
            language TEXT NOT NULL DEFAULT 'python',
            passed BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")


def ensure_columns(db):
    """Bancos antigos: garante colunas adicionadas depois da primeira versão."""
    wanted = {
        "users": [
            ("streak", "INTEGER DEFAULT 0"),
            ("last_active", "TEXT DEFAULT NULL"),
            ("is_admin", "BOOLEAN DEFAULT FALSE"),
        ],
        "user_badges": [("earned_at", "TEXT DEFAULT CURRENT_TIMESTAMP")],
    }
    for table, cols in wanted.items():
        for name, ddl in cols:
            if IS_PG:
                db.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {name} {ddl}").close()
            else:
                existing = {r[1] for r in db.execute(f"PRAGMA table_info({table})").fetchall()}
                if name not in existing:
                    # SQLite não aceita DEFAULT CURRENT_TIMESTAMP em ADD COLUMN
                    safe = ddl.replace(" DEFAULT CURRENT_TIMESTAMP", "")
                    db.execute(f"ALTER TABLE {table} ADD COLUMN {name} {safe}").close()


def create_indexes(db):
    # 1) remove respostas duplicadas antigas e cria o índice único
    if IS_PG:
        db.execute("""
            DELETE FROM answered a USING answered b
            WHERE a.ctid < b.ctid AND a.user_id = b.user_id AND a.question_id = b.question_id
        """).close()
    else:
        db.execute("""
            DELETE FROM answered WHERE rowid NOT IN (
                SELECT MIN(rowid) FROM answered GROUP BY user_id, question_id)
        """).close()
    db.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_answered_user_question ON answered (user_id, question_id)").close()

    # 2) índices de desempenho
    db.execute("CREATE INDEX IF NOT EXISTS idx_units_trail_order ON units (trail_id, unit_order)").close()
    db.execute("CREATE INDEX IF NOT EXISTS idx_questions_unit ON questions (unit_id)").close()
    db.execute("CREATE INDEX IF NOT EXISTS idx_user_badges_user ON user_badges (user_id)").close()
    db.execute("CREATE INDEX IF NOT EXISTS idx_unit_progress_user ON unit_progress (user_id)").close()
    db.execute("CREATE INDEX IF NOT EXISTS idx_users_xp ON users (xp DESC)").close()
    # lab_submissions pode ter sido criada à mão com outro formato: passo opcional
    db.optional(
        "CREATE INDEX IF NOT EXISTS idx_lab_sub_user_challenge ON lab_submissions (user_id, challenge_id)",
        "índice lab_submissions",
    )


def seed_badges(db):
    for code, name, desc, icon in BADGES:
        db.execute(
            "INSERT INTO badges (code, name, description, icon) VALUES (%s, %s, %s, %s) "
            "ON CONFLICT (code) DO NOTHING",
            (code, name, desc, icon),
        ).close()


def ensure_admin(db):
    env_pw = os.environ.get("ADMIN_PASSWORD", "").strip()
    row = db.one("SELECT id, password FROM users WHERE username = %s", ("admin",))

    if row is None:
        generated = not env_pw
        password = env_pw or secrets.token_urlsafe(9)
        db.execute(
            "INSERT INTO users (username, password, is_admin) VALUES (%s, %s, %s)",
            ("admin", generate_password_hash(password), True),
        ).close()
        print("   Usuário 'admin' criado.")
        if generated:
            print(f"   >>> Senha gerada para o admin (anote agora, não será mostrada de novo): {password}")
        return

    if env_pw and os.environ.get("RESET_ADMIN_PASSWORD") == "1":
        db.execute(
            "UPDATE users SET password = %s, is_admin = %s WHERE id = %s",
            (generate_password_hash(env_pw), True, row[0]),
        ).close()
        print("   Senha do admin redefinida a partir de ADMIN_PASSWORD.")
    elif check_password_hash(row[1], "admin123"):
        print("   !!! ATENÇÃO: o admin ainda usa a senha padrão 'admin123'. Qualquer pessoa pode entrar no painel.")
        print("   !!! Troque agora:  $env:ADMIN_PASSWORD='nova-senha-forte'; $env:RESET_ADMIN_PASSWORD='1'; python init_db.py")


def seed_content(db):
    if db.one("SELECT COUNT(*) FROM trails")[0] > 0:
        print("   Trilhas já existem - conteúdo mantido.")
        return

    for t in TRAILS:
        db.execute(
            "INSERT INTO trails (id, name, icon, description, color, trail_order) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            t,
        ).close()

    for trail_id, unit_order, title, intro_text, questions in RAW_DATA:
        if IS_PG:
            cur = db.execute(
                "INSERT INTO units (trail_id, unit_order, title, intro_text) "
                "VALUES (%s, %s, %s, %s) RETURNING id",
                (trail_id, unit_order, title, intro_text),
            )
            unit_id = cur.fetchone()[0]
            cur.close()
        else:
            cur = db.execute(
                "INSERT INTO units (trail_id, unit_order, title, intro_text) VALUES (%s, %s, %s, %s)",
                (trail_id, unit_order, title, intro_text),
            )
            unit_id = cur.lastrowid
            cur.close()

        for q in questions:
            db.execute(
                "INSERT INTO questions (question, answer, difficulty, type, opt1, opt2, opt3, opt4, unit_id) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (*q, unit_id),
            ).close()

    total_q = sum(len(u[4]) for u in RAW_DATA)
    print(f"   {len(RAW_DATA)} unidades e {total_q} perguntas inseridas.")


def fix_sequences(db):
    """As trilhas são inseridas com id explícito: alinha a sequência do Postgres."""
    if IS_PG:
        db.execute(
            "SELECT setval(pg_get_serial_sequence('trails', 'id'), "
            "COALESCE((SELECT MAX(id) FROM trails), 1))"
        ).close()


def lock_down_supabase(db):
    """
    Supabase expõe o schema public pela Data API (REST) usando a chave
    publishable/anon. Tabelas criadas via SQL vêm SEM RLS, ou seja, qualquer
    pessoa com a chave pública conseguiria ler `users` (hashes de senha).
    Ligar o RLS sem policies bloqueia anon/authenticated; a conexão direta
    (role postgres, usada pelo app) continua funcionando normalmente.
    """
    if not IS_PG:
        return
    if os.environ.get("ENABLE_RLS", "1") == "0":
        print("   RLS NÃO foi ligado (ENABLE_RLS=0).")
        return
    for table in TABLES:
        db.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY").close()
    db.optional(
        "DO $$ BEGIN "
        "IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN "
        f"EXECUTE 'REVOKE ALL ON TABLE {', '.join(TABLES)} FROM anon'; END IF; "
        "IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN "
        f"EXECUTE 'REVOKE ALL ON TABLE {', '.join(TABLES)} FROM authenticated'; END IF; "
        "END $$;",
        "revoke anon/authenticated",
    )
    print("   RLS ligado em todas as tabelas (acesso público pela Data API bloqueado).")


def init_db():
    print("--- Iniciando CodeQuest Database Setup ---")
    print(f"   Banco: {'PostgreSQL (DATABASE_URL)' if IS_PG else 'SQLite local (' + SQLITE_PATH + ')'}")
    db = connect()
    try:
        create_tables(db)
        ensure_columns(db)
        create_indexes(db)
        seed_badges(db)
        ensure_admin(db)
        seed_content(db)
        fix_sequences(db)
        lock_down_supabase(db)
        db.commit()
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        print(f"\n!!! Falha no setup (nada foi gravado): {exc}")
        sys.exit(1)
    finally:
        db.close()
    print("--- Setup Finalizado com Sucesso ---")


if __name__ == "__main__":
    init_db()
