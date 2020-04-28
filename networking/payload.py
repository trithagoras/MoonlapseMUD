from typing import *
import json


class Payload:
    def __init__(self, value: Any):
        self.value: Any = value

        # Sanitise semicolons if it's a string
        if type(value) == str:
            self.value: str = value.replace(';', '\\;')

    def serialize(self):
        return self.value

    def __repr__(self):
        return str(self.value)


class StdPayload(Payload):
    MOVE_UP = Payload("MOVE_UP")
    MOVE_DOWN = Payload("MOVE_DOWN")
    MOVE_LEFT = Payload("MOVE_LEFT")
    MOVE_RIGHT = Payload("MOVE_RIGHT")
