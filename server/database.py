import json
from twisted.enterprise import adbapi
from twisted.internet.defer import inlineCallbacks
from twisted.internet.defer import Deferred
import datetime
from typing import *
import traceback
import sys

# Add server to path
import os
from pathlib import Path # if you haven't already done so
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

# Remove server from path
try:
    sys.path.remove(str(parent))
except ValueError:
    print("Error: Removing parent from path, already gone. Traceback: ")
    print(traceback.format_exc())

from networking import models


class Database:
    def __init__(self, connectionstringfilename: str):
        self.dbpool = None

        with open(connectionstringfilename, 'r') as f:
            self.cs = json.load(f)

    def connect(self):
        print("Connecting to database... ", end='')

        self.dbpool = adbapi.ConnectionPool('psycopg2', 
            user=self.cs['user'],
            password=self.cs['password'],
            host=self.cs['host'],
            port=self.cs['port'],
            database=self.cs['database'])

        print(f"Done.")

    @inlineCallbacks
    def register_player(self, username: str, password: str) -> None:
        print(f"Attempting to register player to database: {username}:{password}...", end='')
        now: str = str(datetime.datetime.utcnow())
        yield self.dbpool.runOperation(f"""=
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
        print("Done.")

    @inlineCallbacks
    def user_exists(self, username: str) -> bool:
        print(f"Checking if user {username} exists...", end='')
        result: bool = yield self.dbpool.runQuery(f"""
            SELECT CASE 
                WHEN EXISTS (
                    SELECT NULL
                    FROM users
                    WHERE username = '{username}'
                ) THEN TRUE
                  ELSE FALSE
            END;
        """)
        print("Done")
        return result

    @inlineCallbacks
    def password_correct(self, username: str, password: str) -> bool:
        print(f"Checking if credentials {username}:{password} are correct...")
        result: bool = yield self.dbpool.runQuery(f"""
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
        print("Done.")
        return result

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
