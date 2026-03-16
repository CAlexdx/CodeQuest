import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    type TEXT,
    option1 TEXT,
    option2 TEXT,
    option3 TEXT,
    option4 TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    xp INTEGER DEFAULT 0
)
""")

cursor.execute("DELETE FROM questions")

cursor.execute("""
INSERT INTO questions (question, answer, type)
VALUES
("Quanto é 2 + 2?", "4", "text"),
("Capital do Brasil?", "brasilia", "text"),
("Quanto é 10 / 2?", "5", "text")
""")

cursor.execute("""
INSERT OR IGNORE INTO users (id, username, xp)
VALUES (1, "Player", 0)
""")

conn.commit()
conn.close()

print("Banco de dados criado com sucesso!")