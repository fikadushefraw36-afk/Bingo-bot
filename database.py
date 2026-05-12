import sqlite3

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('bingo.db')
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                wins INTEGER DEFAULT 0,
                games_played INTEGER DEFAULT 0
            )
        ''')
        self.conn.commit()
    
    def add_user(self, user_id, username):
        cursor = self.conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', (user_id, username))
        self.conn.commit()
    
    def update_win(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET wins = wins + 1, games_played = games_played + 1 WHERE user_id = ?', (user_id,))
        self.conn.commit()
    
    def get_leaderboard(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT username, wins FROM users ORDER BY wins DESC LIMIT 10')
        return cursor.fetchall()
