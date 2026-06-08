import mysql.connector
from mysql.connector import errorcode
import os
from dotenv import load_dotenv

_ENV_PATH = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=_ENV_PATH, override=True)


def _get_db_settings():
    return {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "trackerfm"),
        "port": int(os.getenv("DB_PORT", "3306") or 3306),
        "charset": "utf8mb4",
    }


def _initialize_database_schema(conn):
    sql_path = os.path.join(os.path.dirname(__file__), "trackerfmm.sql")
    with open(sql_path, encoding="utf-8") as f:
        sql = f.read()

    cursor = conn.cursor()
    for result in cursor.execute(sql, multi=True):
        pass
    conn.commit()
    cursor.close()


def _ensure_database_schema(conn):
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES LIKE 'users'")
    has_users = cursor.fetchone() is not None
    cursor.close()

    if not has_users:
        _initialize_database_schema(conn)


def _create_database_if_missing():
    cfg = _get_db_settings()
    db_name = cfg["database"]

    conn = mysql.connector.connect(
        host=cfg["host"],
        user=cfg["user"],
        password=cfg["password"],
        port=cfg["port"],
        charset=cfg["charset"],
    )
    cursor = conn.cursor()
    cursor.execute(
        f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci"
    )
    cursor.close()
    conn.close()

    conn = mysql.connector.connect(
        host=cfg["host"],
        user=cfg["user"],
        password=cfg["password"],
        database=db_name,
        port=cfg["port"],
        charset=cfg["charset"],
    )
    _initialize_database_schema(conn)
    conn.close()


def get_connection():
    cfg = _get_db_settings()
    try:
        conn = mysql.connector.connect(
            host=cfg["host"],
            user=cfg["user"],
            password=cfg["password"],
            database=cfg["database"],
            port=cfg["port"],
            charset=cfg["charset"],
        )
        _ensure_database_schema(conn)
        return conn
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_BAD_DB_ERROR:
            _create_database_if_missing()
            conn = mysql.connector.connect(
                host=cfg["host"],
                user=cfg["user"],
                password=cfg["password"],
                database=cfg["database"],
                port=cfg["port"],
                charset=cfg["charset"],
            )
            _ensure_database_schema(conn)
            return conn
        raise
