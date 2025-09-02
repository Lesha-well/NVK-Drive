import sqlite3
from sqlite3 import Error

def create_connection():
    """Создает подключение к базе данных SQLite."""
    conn = None
    try:
        conn = sqlite3.connect("data.db")
        return conn
    except Error as e:
        print(f"Ошибка подключения к базе данных: {e}")
    return conn

def init_db():
    """Инициализация базы данных и создание таблицы users."""
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL,
                    course TEXT NOT NULL,
                    photo_id TEXT,
                    skills TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
        except Error as e:
            print(f"Ошибка при создании таблицы: {e}")
        finally:
            conn.close()

def add_user(user_id, username, course, photo_id=None, skills=None):
    """Добавление или обновление анкеты пользователя."""
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, username, course, photo_id, skills)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, course, photo_id, skills))
            conn.commit()
        except Error as e:
            print(f"Ошибка при добавлении пользователя: {e}")
        finally:
            conn.close()

def get_user(user_id):
    """Получение анкеты пользователя по user_id."""
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            return cursor.fetchone()
        except Error as e:
            print(f"Ошибка при получении пользователя: {e}")
        finally:
            conn.close()
    return None

def delete_user(user_id):
    """Удаление анкеты пользователя."""
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            conn.commit()
        except Error as e:
            print(f"Ошибка при удалении пользователя: {e}")
        finally:
            conn.close()

def get_all_users(exclude_user_id):
    """Получение всех анкет, кроме анкеты текущего пользователя."""
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id != ?", (exclude_user_id,))
            return cursor.fetchall()
        except Error as e:
            print(f"Ошибка при получении пользователей: {e}")
        finally:
            conn.close()
    return []