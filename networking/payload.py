from typing import *
import pickle


class Payload:
    def __init__(self, value: Any):
        self.value: Any = value

    def serialize(self):
        return pickle.dumps(self.value).hex()

    def __repr__(self):
        return f"(Payload: {self.value})"

    def __eq__(self, obj):
        return isinstance(obj, Payload) and obj.value == self.value


class StdPayload(Payload):
    MOVE_UP = Payload("u")
    MOVE_DOWN = Payload("d")
    MOVE_LEFT = Payload("l")
    MOVE_RIGHT = Payload("r")
