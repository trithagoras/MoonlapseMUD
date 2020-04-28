import random
import sys
from typing import *
import traceback

class Player:
    def __init__(self, client_socket,  username: str):
        self.client_socket = client_socket
        self.username = username
        self.player_id: Optional[int] = None
        self.player_char: Optional[chr] = None
        self.position: Optional[List[int, int]] = None
        self.room = None

    def init_data(self, player_id) -> None:
        self.player_id = player_id

        ids: List[chr] = ['#', '@', '&', '+', '%', '$', '£']

        self.player_char: chr = ids[self.player_id]
        if self.player_id + 1 > len(ids):
            self.player_char = 65 + self.player_id - len(ids)

    def spawn_player(self, position: List[int], room) -> None:
        self.position = position
        self.room = room
        if self.position == (None, None):
            while True:
                self.position = [random.randint(1, self.room.height), random.randint(1, self.room.width)]
                if self.position not in self.room.walls:
                    break

    def disconnect(self) -> None:
        try:
            self.client_socket.close()
        except Exception:
            print("Error: Traceback: ", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
