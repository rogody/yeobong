# db_client.py
import pymysql

class DBClient:
    def __init__(self,
                 host="127.0.0.1",
                 port=3306,
                 user="root",
                 password="1q2w3e4r",
                 db="yubongdb"):
        self.conn = pymysql.connect(
            host=host, port=port,
            user=user, password=password,
            db=db, charset="utf8mb4",
            autocommit=True,
            cursorclass=pymysql.cursors.DictCursor
        )

    def execute(self, sql, params=None):
        with self.conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur

    def close(self):
        self.conn.close()
