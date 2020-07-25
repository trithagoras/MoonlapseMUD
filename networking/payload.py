import json
import inspect
from .models import *


class Payload:
    def __init__(self, value: Any):
        self.value: Any = value

    def serialize(self):
        def default(o):
            if hasattr(o, '__dict__'):
                d = o.__dict__
                d['classkey'] = o.__class__.__name__
                return d
            else:
                return o

        if hasattr(self.value, '__dict__'):
            data = json.dumps(self.value.__dict__, default=default, separators=(',', ': '))
            data = f'{data[:1]}"classkey":"{self.value.__class__.__name__}",{data[1:]}'
            return data
        else:
            return json.dumps(self.value, default=default, separators=(',', ': '))

    def __repr__(self):
        return f"(Payload: {self.value})"

    def __eq__(self, obj):
        return isinstance(obj, Payload) and obj.value == self.value


def deserialize(serialized: str) -> 'Payload':
    attrs = json.loads(serialized)

    if isinstance(attrs, dict):
        # Use reflection to construct the specific payload type we're looking for
        classkey: str = attrs.pop('classkey')
        constructor: Type = globals()[classkey]
        required_params = list(inspect.signature(constructor).parameters.values())

        # TODO: This is horrible, think of a better way
        value = constructor.__new__(constructor)
        for k, v in attrs.items():
            # If it's a nested object, use recursion to deserialize that too
            if isinstance(v, dict) and 'classkey' in v:
                setattr(value, k, deserialize(json.dumps(v)).value)
            else:
                setattr(value, k, v)

    else:
        value = attrs

    return Payload(value)
