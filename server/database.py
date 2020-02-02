import json
import psycopg2
import datetime


class Database:
    def __init__(self, connectionstringfilename: str):
        self.conn = None
        self.curs = None

        with open(connectionstringfilename, 'r') as f:
            self.cs = json.load(f)

    def connect(self):
        print("Connecting to database... ", end='')
        if self.conn:
            self.conn.close()
        if self.curs:
            self.curs.close()

        self.conn = psycopg2.connect(
            user=self.cs['user'],
            password=self.cs['password'],
            host=self.cs['host'],
            port=self.cs['port'],
            database=self.cs['database']
        )

        self.curs = self.conn.cursor()

        p = self.conn.get_dsn_parameters()
        print(f"done: host={p['host']}, port={p['port']}, dbname={p['dbname']}, user={p['user']}")

    def register_player(self, username, password):
        print(f"Attempting to register player to database: {username}:{password}...", end='')
        self.curs.execute(f"""
            INSERT INTO users (username, password)
            VALUES ('{username}', '{password}')
            RETURNING id;
        """)
        userid = self.curs.fetchone()[0]

        now = str(datetime.datetime.utcnow())
        self.curs.execute(f"""
            INSERT INTO entities (type, lastupdated)
            VALUES ('Player', '{now}')
            RETURNING id;
        """)
        entityid = self.curs.fetchone()[0]

        self.curs.execute(f"""
            INSERT INTO players (entityid, userid, name, locationid) 
            VALUES ({entityid}, {userid}, '{username}', 1);
        """)

        self.conn.commit()
        print("Success!")

    def user_exists(self, username: str) -> bool:
        print(f"Checking if user exists: {username}...", end='')
        self.curs.execute(f"""
            SELECT CASE 
                WHEN EXISTS (
                    SELECT NULL
                    FROM users
                    WHERE username = '{username}'
                ) THEN TRUE
                  ELSE FALSE
            END;
        """)
        result = self.curs.fetchone()[0]
        print(f"Result: {result}")
        return result

    def password_correct(self, username: str, password: str) -> bool:
        print(f"Checking if credentials: {username}:{password} are correct...", end='')
        self.curs.execute(f"""
            SELECT CASE 
                WHEN EXISTS (
                    SELECT NULL
                    FROM users
                    WHERE username = '{username}'
                    AND password = '{password}'
                ) THEN TRUE
                  ELSE FALSE
            END;
        """)
        result = self.curs.fetchone()[0]
        print(f"Result: {result}")
        return result
