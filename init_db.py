import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL
)
""")

cursor.execute("""
INSERT INTO questions (question, answer)
VALUES
("Quanto é 2 + 2?", "4"),
("Capital do Brasil?", "Brasilia"),
("Quanto é 10 / 2?", "5")
""")

conn.commit()
conn.close()

print("Banco de dados criado com sucesso!")