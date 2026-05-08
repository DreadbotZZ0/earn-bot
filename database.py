import sqlite3
from datetime import datetime

DB_PATH = "earn_bot.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            full_name TEXT,
            balance INTEGER DEFAULT 0,
            referrer_id INTEGER,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            link TEXT NOT NULL,
            reward INTEGER DEFAULT 1000,
            active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS completed_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,
            completed_at TEXT DEFAULT (datetime('now')),
            UNIQUE(user_id, channel_id)
        );

        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            card_number TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()

# --- Users ---
def get_user(tg_id):
    conn = get_conn()
    user = conn.execute("SELECT * FROM users WHERE tg_id=?", (tg_id,)).fetchone()
    conn.close()
    return user

def create_user(tg_id, username, full_name, referrer_id=None):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO users (tg_id, username, full_name, referrer_id) VALUES (?,?,?,?)",
            (tg_id, username, full_name, referrer_id)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

def add_balance(tg_id, amount):
    conn = get_conn()
    conn.execute("UPDATE users SET balance=balance+? WHERE tg_id=?", (amount, tg_id))
    conn.commit()
    conn.close()

def deduct_balance(tg_id, amount):
    conn = get_conn()
    conn.execute("UPDATE users SET balance=balance-? WHERE tg_id=?", (amount, tg_id))
    conn.commit()
    conn.close()

def get_referral_count(tg_id):
    conn = get_conn()
    row = conn.execute("SELECT COUNT(*) as cnt FROM users WHERE referrer_id=?", (tg_id,)).fetchone()
    conn.close()
    return row["cnt"]

def get_all_users():
    conn = get_conn()
    rows = conn.execute("SELECT tg_id FROM users").fetchall()
    conn.close()
    return [r["tg_id"] for r in rows]

# --- Channels ---
def get_channels():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM channels WHERE active=1").fetchall()
    conn.close()
    return rows

def add_channel(channel_id, title, link, reward=1000):
    conn = get_conn()
    try:
        conn.execute("INSERT INTO channels (channel_id,title,link,reward) VALUES (?,?,?,?)",
                     (channel_id, title, link, reward))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def delete_channel(channel_id):
    conn = get_conn()
    conn.execute("DELETE FROM channels WHERE id=?", (channel_id,))
    conn.commit()
    conn.close()

def is_task_completed(user_id, channel_id):
    conn = get_conn()
    row = conn.execute("SELECT id FROM completed_tasks WHERE user_id=? AND channel_id=?",
                       (user_id, channel_id)).fetchone()
    conn.close()
    return row is not None

def complete_task(user_id, channel_id):
    conn = get_conn()
    try:
        conn.execute("INSERT INTO completed_tasks (user_id,channel_id) VALUES (?,?)", (user_id, channel_id))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

# --- Withdrawals ---
def create_withdrawal(user_id, amount, card_number):
    conn = get_conn()
    conn.execute("INSERT INTO withdrawals (user_id,amount,card_number) VALUES (?,?,?)",
                 (user_id, amount, card_number))
    conn.commit()
    conn.close()

def get_pending_withdrawals():
    conn = get_conn()
    rows = conn.execute("""
        SELECT w.*, u.tg_id, u.username, u.full_name
        FROM withdrawals w JOIN users u ON w.user_id=u.id
        WHERE w.status='pending' ORDER BY w.created_at
    """).fetchall()
    conn.close()
    return rows

def update_withdrawal(wid, status):
    conn = get_conn()
    conn.execute("UPDATE withdrawals SET status=? WHERE id=?", (status, wid))
    conn.commit()
    conn.close()

def get_withdrawal(wid):
    conn = get_conn()
    row = conn.execute("""
        SELECT w.*, u.tg_id, u.balance FROM withdrawals w
        JOIN users u ON w.user_id=u.id WHERE w.id=?
    """, (wid,)).fetchone()
    conn.close()
    return row

def get_stats():
    conn = get_conn()
    users = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
    total_paid = conn.execute("SELECT COALESCE(SUM(amount),0) as s FROM withdrawals WHERE status='approved'").fetchone()["s"]
    pending = conn.execute("SELECT COUNT(*) as c FROM withdrawals WHERE status='pending'").fetchone()["c"]
    conn.close()
    return users, total_paid, pending
