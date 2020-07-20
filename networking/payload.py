from typing import *
import json


class Payload:
    def __init__(self, value: Any):
        self.value: Any = value

    def serialize(self):
        def default(o):
            if hasattr(o, '__dict__'):
                data = o.__dict__
                o['classkey'] = o.__class__.__name__
                return data
            else:
                return o

        if hasattr(self.value, '__dict__'):
            data = json.dumps(self.value.__dict__, default=default, separators=(',', ': '))
            data = data[:1] + f'"classkey":"{self.value.__class__.__name__}",' + data[1:]
            return data
        else:
            return json.dumps(self.value, default=default, separators=(',', ': '))

    def __repr__(self):
        return f"(Payload: {self.value})"

    def __eq__(self, obj):
        return isinstance(obj, Payload) and obj.value == self.value
