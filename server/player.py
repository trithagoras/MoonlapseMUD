import random
import sys
from typing import *
import traceback

class Player:
    def __init__(self, client_socket,  username: str):
        self.client_socket = client_socket
        self.username = username

    def init_data(self, data) -> None:
        self.player_id = data['id']
        self.walls = data['walls']
        self.map_width, self.map_height = data['w'], data['h']

        ids: List[chr] = ['#', '@', '&', '+', '%', '$', '£']

        player_char: chr = ids[self.player_id]
        if self.player_id + 1 > len(ids):
            player_char = 65 + self.player_id - len(ids)

        self.state = {
            'pos': {},
            'c': player_char
        }

    def spawn_player(self, pos) -> None:
        if pos == (None, None):
            while True:
                pos: List[int, int] = [random.randint(1, self.map_width - 2), random.randint(1, self.map_height - 2)]
                if pos not in self.walls:
                    break

        self.state['pos'] = {
            'x': pos[0],
            'y': pos[1]
        }

    def disconnect(self) -> None:
        try:
            self.client_socket.close()
        except Exception:
            print("Error: Traceback: ", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
