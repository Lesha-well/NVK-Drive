import sqlite3
from sqlite3 import Error

def create_connection():
    """Создает подключение к базе данных SQLite с доступом к полям по именам."""
    conn = None
    try:
        conn = sqlite3.connect("data.db")
        conn.row_factory = sqlite3.Row
        return conn
    except Error as e:
        print(f"Ошибка подключения к базе данных: {e}")
    return conn

def _ensure_tags_column(conn: sqlite3.Connection):
    """Гарантирует наличие колонки tags в таблице users."""
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(users)")
        columns = {row["name"] for row in cursor.fetchall()}
        if "tags" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN tags TEXT")
            conn.commit()
    except Error as e:
        print(f"Ошибка при добавлении колонки tags: {e}")

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
                    tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            _ensure_tags_column(conn)
        except Error as e:
            print(f"Ошибка при создании таблицы: {e}")
        finally:
            conn.close()

def add_user(user_id, username, course, photo_id=None, skills=None, tags=None):
    """Добавление или обновление анкеты пользователя."""
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, username, course, photo_id, skills, tags)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, username, course, photo_id, skills, tags))
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