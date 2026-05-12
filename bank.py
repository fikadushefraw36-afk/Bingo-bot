import sqlite3
from datetime import datetime

class BankSystem:
    def __init__(self):
        self.conn = sqlite3.connect('bingo_bank.db', check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance INTEGER DEFAULT 0,
                total_deposited INTEGER DEFAULT 0,
                total_withdrawn INTEGER DEFAULT 0,
                total_won INTEGER DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT,
                amount INTEGER,
                status TEXT,
                reference TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()
    
    def create_account(self, user_id, username):
        cursor = self.conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO accounts (user_id, username) VALUES (?, ?)', (user_id, username))
        self.conn.commit()
        return True
    
    def get_balance(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT balance FROM accounts WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else 0
    
    def deposit(self, user_id, amount, reference=None):
        if amount <= 0:
            return False, "ዋጋው ከዜሮ በላይ መሆን አለበት!"
        cursor = self.conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO accounts (user_id, balance) VALUES (?, 0)', (user_id,))
        cursor.execute('UPDATE accounts SET balance = balance + ?, total_deposited = total_deposited + ? WHERE user_id = ?', (amount, amount, user_id))
        self.conn.commit()
        return True, f"{amount} ብር ገብቷል!"
    
    def withdraw(self, user_id, amount, reference=None):
        if amount <= 0:
            return False, "ዋጋው ከዜሮ በላይ መሆን አለበት!"
        if self.get_balance(user_id) < amount:
            return False, f"በቂ ገንዘብ የለም!"
        cursor = self.conn.cursor()
        cursor.execute('UPDATE accounts SET balance = balance - ?, total_withdrawn = total_withdrawn + ? WHERE user_id = ?', (amount, amount, user_id))
        self.conn.commit()
        return True, f"{amount} ብር ወጥቷል!"
    
    def add_winnings(self, user_id, amount):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE accounts SET balance = balance + ?, total_won = total_won + ? WHERE user_id = ?', (amount, amount, user_id))
        self.conn.commit()
        return True
