import datetime
import json
from networking import models
from twisted.enterprise import adbapi
from twisted.internet.defer import Deferred


class Database:
    def __init__(self, connectionstringfilename: str):
        self.dbpool = None

        with open(connectionstringfilename, 'r') as f:
            self.cs = json.load(f)

    def connect(self):
        print("Connecting to database...")

        self.dbpool = adbapi.ConnectionPool(
            dbapiName='psycopg2',
            user=self.cs['user'],
            password=self.cs['password'],
            host=self.cs['host'],
            port=self.cs['port'],
            database=self.cs['database']
        )

        print("Done.")

    def register_user(self, username: str, password: str) -> Deferred:
        print(f"Attempting to register player to database: {username}:{password}...")
        now: str = str(datetime.datetime.utcnow())
        return self.dbpool.runOperation(f"""
            INSERT INTO users (username, password)
            VALUES ('{username}', '{password}');

            INSERT INTO entities (type, lastupdated)
            VALUES ('Player', '{now}');

            INSERT INTO players (entityid, userid, name, character)
            SELECT e.id, u.id, '{username}', '@'
            FROM users AS u
            CROSS JOIN entities AS e
            WHERE u.username = '{username}'
            AND e.lastupdated = '{now}';
        """)

    def user_exists(self, username: str) -> Deferred:
        print(f"Checking if user {username} exists...")
        return self.dbpool.runQuery(f"""
            SELECT CASE 
                WHEN EXISTS (
                    SELECT NULL
                    FROM users
                    WHERE username = '{username}'
                ) THEN TRUE
                  ELSE FALSE
            END;
        """)

    def password_correct(self, username: str, password: str) -> Deferred:
        print(f"Checking if credentials {username}:{password} are correct...")
        return self.dbpool.runQuery(f"""
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

    def update_player_pos(self, player: models.Player, y: int, x: int) -> Deferred:
        print(f"Updating player position ({player.get_username()})...")
        return self.dbpool.runOperation(f"""
            UPDATE entities
            SET position = '{y}, {x}'
            WHERE id IN (
                SELECT p.entityid
                FROM players AS p
                INNER JOIN users AS u 
                ON p.userid = u.id and u.username = '{player.get_username()}' 
            )
        """)

    def get_player_pos(self, player: models.Player) -> Deferred:
        print(f"Getting player position ({player.get_username()})...", end='')
        return self.dbpool.runQuery(f"""
            SELECT position[0], position[1]
            FROM entities
            where id IN (
                SELECT p.entityid
                FROM players as p 
                INNER JOIN users AS u 
                ON p.userid = u.id AND u.username = '{player.get_username()}'
            )
        """)
