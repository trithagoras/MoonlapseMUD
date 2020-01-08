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

        try:
            self.tcpsrv.connect_socket()
        except Exception as e:
            print(e, file=sys.stderr)

        with open(room_map) as data:
            map_data = json.load(data)
            self.walls = map_data['walls']
            self.width, self.height = map_data['size']

        # Create player spots in game object
        for index in range(0, self.capacity):
            self.players.append(None)

    def kick(self, player_id: int):
        self.players[player_id].disconnect()
        self.tcpsrv.log.log(time.time(), f"Player {player_id} has departed.")
        self.players[player_id] = None
        print(f"Kicked player {player_id}")
