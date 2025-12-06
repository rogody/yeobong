# db_client.py
import configparser
from pathlib import Path

import pymysql


def _load_db_settings(config_path: Path):
    parser = configparser.ConfigParser()
    read_files = parser.read(config_path)
    if not read_files:
        raise FileNotFoundError(f"DB config file not found at {config_path}")

    if "database" not in parser:
        raise KeyError("Missing [database] section in DB config file.")

    section = parser["database"]
    return {
        "host": section.get("host", "localhost"),
        "port": section.getint("port", 3306),
        "user": section.get("user", ""),
        "password": section.get("password", ""),
        "db": section.get("db", ""),
    }


_CONFIG_PATH = Path(__file__).with_name("db_config.ini")
_DB_SETTINGS = _load_db_settings(_CONFIG_PATH)


class DBClient:
    def __init__(self,
                 host=None,
                 port=None,
                 user=None,
                 password=None,
                 db=None):
        settings = {
            "host": host or _DB_SETTINGS["host"],
            "port": int(port or _DB_SETTINGS["port"]),
            "user": user or _DB_SETTINGS["user"],
            "password": password or _DB_SETTINGS["password"],
            "db": db or _DB_SETTINGS["db"],
        }
        try:
            self.conn = pymysql.connect(
                host=settings["host"], port=settings["port"],
                user=settings["user"], password=settings["password"],
                db=settings["db"], charset="utf8mb4",
                autocommit=True,
                cursorclass=pymysql.cursors.DictCursor
            )
            print("database connected")
        
        except pymysql.MySQLError as e:
            print(f"Database connection failed: {e}")
            self.conn = None

    def execute(self, sql, params=None):
        """
        Execute INSERT/UPDATE/DELETE statements.
        Returns the lastrowid to make it easy to capture generated keys.
        """
        if self.conn is None:
            print("No database connection.")
            return None
        
        with self.conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.lastrowid

    def fetchone(self, sql, params=None):
        with self.conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchone()

    def fetchall(self, sql, params=None):
        with self.conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()

    def close(self):
        if self.conn:
            self.conn.close()
