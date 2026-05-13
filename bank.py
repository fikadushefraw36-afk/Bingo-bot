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
                total_won INTEGER DEFAULT 0,
                bonus_received INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        ref = reference or f"DEP_{user_id}_{datetime.now().timestamp()}"
        cursor.execute('INSERT INTO transactions (user_id, type, amount, status, reference) VALUES (?, "deposit", ?, "completed", ?)', (user_id, amount, ref))
        self.conn.commit()
        return True, f"{amount} ብር ገብቷል!"
    
    def withdraw(self, user_id, amount, reference=None):
        if amount <= 0:
            return False, "ዋጋው ከዜሮ በላይ መሆን አለበት!"
        if self.get_balance(user_id) < amount:
            return False, f"በቂ ገንዘብ የለም!"
        cursor = self.conn.cursor()
        cursor.execute('UPDATE accounts SET balance = balance - ?, total_withdrawn = total_withdrawn + ? WHERE user_id = ?', (amount, amount, user_id))
        ref = reference or f"WTD_{user_id}_{datetime.now().timestamp()}"
        cursor.execute('INSERT INTO transactions (user_id, type, amount, status, reference) VALUES (?, "withdraw", ?, "completed", ?)', (user_id, amount, ref))
        self.conn.commit()
        return True, f"{amount} ብር ወጥቷል!"
    
    def add_winnings(self, user_id, amount):
        if amount <= 0:
            return False
        cursor = self.conn.cursor()
        cursor.execute('UPDATE accounts SET balance = balance + ?, total_won = total_won + ? WHERE user_id = ?', (amount, amount, user_id))
        ref = f"WIN_{user_id}_{datetime.now().timestamp()}"
        cursor.execute('INSERT INTO transactions (user_id, type, amount, status, reference) VALUES (?, "winning", ?, "completed", ?)', (user_id, amount, ref))
        self.conn.commit()
        return True
    
    def add_bonus(self, user_id):
        """አዲስ ተጠቃሚ ሲመዘገብ 10 ብር ቦነስ መስጠት"""
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT bonus_received FROM accounts WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result and result[0]:
            return False, "ቦነስ ቀድሞውኑ ተሰጥቶዎታል!"
        
        cursor.execute('''
            UPDATE accounts 
            SET balance = balance + 10, 
                total_deposited = total_deposited + 10,
                bonus_received = 1 
            WHERE user_id = ?
        ''', (user_id,))
        
        ref = f"BONUS_{user_id}_{datetime.now().timestamp()}"
        cursor.execute('''
            INSERT INTO transactions (user_id, type, amount, status, reference)
            VALUES (?, 'bonus', 10, 'completed', ?)
        ''', (user_id, ref))
        
        self.conn.commit()
        return True, "10 ብር ቦነስ አግኝተዋል! 🎉"
    
    def get_transaction_history(self, user_id, limit=20):
        cursor = self.conn.cursor()
        cursor.execute('SELECT type, amount, status, created_at FROM transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?', (user_id, limit))
        return cursor.fetchall()
    
    def get_account_summary(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT balance, total_deposited, total_withdrawn, total_won FROM accounts WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        if result:
            return {'balance': result[0], 'total_deposited': result[1], 'total_withdrawn': result[2], 'total_won': result[3]}
        return None
