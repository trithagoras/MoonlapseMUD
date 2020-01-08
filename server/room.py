import json
import sys
import datetime
import time
import psycopg2
from typing import *
from player import Player


class Room:
    def __init__(self, tcpsrv, room_map, capacity):
        self.walls: set = set()
        self.players: List[Optional[Player]] = []
        self.capacity = capacity

        self.tcpsrv = tcpsrv
        self.dbconn = None
        self.dbcurs = None

        try:
            self.tcpsrv.connect_socket()
        except Exception as e:
            print(e, file=sys.stderr)

        try:
            self.connect_db()
        except Exception as e:
            print(e, file=sys.stderr)

        with open(room_map) as data:
            map_data = json.load(data)
            self.walls = map_data['walls']
            self.width, self.height = map_data['size']

        # Create player spots in game object
        for index in range(0, self.capacity):
            self.players.append(None)

    def connect_db(self):
        print("Connecting to database... ", end='')
        if self.dbconn:
            self.dbconn.close()
        if self.dbcurs:
            self.dbcurs.close()

        with open('server/connectionstrings.json', 'r') as f:
            cs = json.load(f)

        self.dbconn = psycopg2.connect(
            user=cs['user'],
            password=cs['password'],
            host=cs['host'],
            port=cs['port'],
            database=cs['database']
        )

        self.dbcurs = self.dbconn.cursor()

        p = self.dbconn.get_dsn_parameters()
        print(f"done: host={p['host']}, port={p['port']}, dbname={p['dbname']}, user={p['user']}")

    def register_player(self, connection, username, password):
        cursor = connection.cursor()

        cursor.execute(f"""
            INSERT INTO users (username, password)
            VALUES ('{username}', '{password}')
            RETURNING id;
        """)
        userid = cursor.fetchone()[0]

        now = str(datetime.datetime.utcnow())
        cursor.execute(f"""
            INSERT INTO entities (type, lastupdated)
            VALUES ('Player', '{now}')
            RETURNING id;
        """)
        entityid = cursor.fetchone()[0]

        cursor.execute(f"""
            INSERT INTO players (entityid, userid, name, locationid) 
            VALUES ({entityid}, {userid}, '{username}', 1);
        """)

        connection.commit()

    def kick(self, player_id: int):
        self.players[player_id].disconnect()
        self.tcpsrv.log.log(time.time(), f"Player {player_id} has departed.")
        self.players[player_id] = None
        print(f"Kicked player {player_id}")
