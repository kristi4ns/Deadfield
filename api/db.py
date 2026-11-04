import os
import sqlite3

# Datubāzes fails tiek saglabāts api mapē
DATABASE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scores.db")


def run_query(sql, parameters=()):
    # Atver savienojumu, izpilda vienu SQL vaicājumu, aizver savienojumu
    # un atgriež rezultātu kā vārdnīcu sarakstu
    # ? zīmes aizstāj ar vērtībām no parameters, tāpēc tekstu SQL iekšā nekad nesalīmējam
    connection = sqlite3.connect(DATABASE_FILE)

    # Ļauj nolasīt kolonnas pēc nosaukuma, piemēram row["points"]
    connection.row_factory = sqlite3.Row

    rows = connection.execute(sql, parameters).fetchall()
    connection.commit()
    connection.close()

    # Katru rindu pārvēršam par vārdnīcu
    results = []
    for row in rows:
        results.append(dict(row))
    return results


def create_tables():
    # Izveido tabulu, ja tās vēl nav
    run_query(
        """
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            points INTEGER NOT NULL,
            played_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def add_score(name, points):
    run_query("INSERT INTO scores (name, points) VALUES (?, ?)", (name, points))


def get_top_scores(limit):
    # Labākie rezultāti pirmie. Ja divi rezultāti ir vienādi, vecākais ir augstāk
    return run_query(
        "SELECT name, points, played_at FROM scores ORDER BY points DESC, id ASC LIMIT ?",
        (limit,),
    )


def get_player_stats(name):
    # Cik spēles spēlētājs nospēlējis un kāds ir viņa labākais rezultāts
    # Ja spēlētājam nav neviena rezultāta, atgriež None
    rows = run_query(
        "SELECT COUNT(*) AS games, MAX(points) AS best_score FROM scores WHERE name = ?",
        (name,),
    )
    stats = rows[0]

    if stats["games"] == 0:
        return None

    return {"name": name, "games": stats["games"], "best_score": stats["best_score"]}