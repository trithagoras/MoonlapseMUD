import datetime
import json
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
        # TODO: Find a better way of setting the default room
        return self.dbpool.runOperation(f"""
            INSERT INTO users (username, password)
            VALUES ('{username}', '{password}');

            INSERT INTO entities (type, lastupdated, roomid)
            SELECT 'Player', '{now}', MIN(id)
            FROM rooms;

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

    def update_player_pos(self, username: str, y: int, x: int) -> Deferred:
        print(f"Updating player position ({username})...")
        return self.dbpool.runOperation(f"""
            UPDATE entities
            SET position = '{y}, {x}'
            WHERE id IN (
                SELECT p.entityid
                FROM players AS p
                INNER JOIN users AS u 
                ON p.userid = u.id and u.username = '{username}' 
            )
        """)

    def get_player_pos(self, username: str) -> Deferred:
        print(f"Getting player position ({username})...")
        return self.dbpool.runQuery(f"""
            SELECT position[0], position[1]
            FROM entities
            where id IN (
                SELECT p.entityid
                FROM players as p 
                INNER JOIN users AS u 
                ON p.userid = u.id AND u.username = '{username}'
            )
        """)

    def set_player_room(self, username: str, roomname: str) -> Deferred:
        print(f"Updating player room ({username})...")
        return self.dbpool.runOperation(f"""
                    UPDATE entities
                    SET roomid = (
                        SELECT id
                        FROM rooms
                        WHERE name = '{roomname}'
                    )
                    WHERE id IN (
                        SELECT p.entityid
                        FROM players AS p
                        INNER JOIN users AS u 
                        ON p.userid = u.id and u.username = '{username}' 
                    )
                """)

    def get_player_roomname(self, username: str) -> Deferred:
        print(f"Getting player room ({username})...")
        return self.dbpool.runQuery(f"""
            SELECT name 
            FROM rooms
            WHERE id IN (
                SELECT roomid
                FROM entities AS e
                INNER JOIN players AS p
                ON e.id = p.entityid
                INNER JOIN users AS u
                ON p.userid = u.id AND u.username = '{username}'
            )
        """)

    def create_room(self, name: str, path: str) -> Deferred:
        print(f"Creating room ({name})...")
        return self.dbpool.runOperation(f"""
            DO
            $do$
            BEGIN
                IF EXISTS (
                    SELECT NULL
                    FROM rooms
                    WHERE path = '{path}'
                ) THEN
                    UPDATE rooms
                    SET name = '{name}'
                    WHERE path = '{path}';
                ELSE
                    INSERT INTO rooms (name, path)
                    VALUES ('{name}', '{path}');
                END IF;
            END;
            $do$;
        """)