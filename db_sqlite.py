# db_sqlite.py
import sqlite3
import os

DB_NAME = "game_bot.db"

def init_db():
    """Создаем таблицу, если её нет"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                subscribed BOOLEAN DEFAULT 0,
                verif_joined BOOLEAN DEFAULT 0,
                registered BOOLEAN DEFAULT 0
            )
        """)
        conn.commit()

def add_user(user_id):
    """Добавляем нового пользователя, если его нет"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()

def update_subscription(user_id, status=True):
    """Обновляем статус подписки"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET subscribed = ? WHERE user_id = ?", (status, user_id))
        conn.commit()

def update_verification(user_id, status=True):
    """Обновляем статус участия в чате верификации"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET verif_joined = ? WHERE user_id = ?", (status, user_id))
        conn.commit()

def mark_registered(user_id):
    """Пользователь зарегистрировался по промокоду"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET registered = ? WHERE user_id = ?", (True, user_id))
        conn.commit()

def get_user_status(user_id):
    """Получаем статус пользователя"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT subscribed, verif_joined, registered FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            return {"subscribed": False, "verif_joined": False, "registered": False}
        return {
            "subscribed": bool(row[0]),
            "verif_joined": bool(row[1]),
            "registered": bool(row[2])
        }