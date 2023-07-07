import sqlite3
from typing import List


class Database:
    def __init__(self):
        self.conn = sqlite3.connect("matches.db")
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('CREATE TABLE IF NOT EXISTS matches (user_id INTEGER PRIMARY KEY)')

    def add_match(self, user_id):
        self.cursor.execute('INSERT OR IGNORE INTO matches (user_id) VALUES (?)', (user_id,))
        self.conn.commit()

    def get_matches(self, user_id) -> List[int]:
        self.cursor.execute('SELECT user_id FROM matches')
        return [match[0] for match in self.cursor.fetchall()]


