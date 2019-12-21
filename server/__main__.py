import time
import os
import sys
from room import Room
from threading import Thread

if __name__ == '__main__':
    pwd: str = os.path.dirname(__file__)
    for path in ('..', '../payload', '../client', '../server'):
        sys.path.append(os.path.abspath(os.path.join(pwd, path)))

    ip, port = '', 8081
    room = Room(ip, port, os.path.join(pwd, '..', 'maps', 'map.bmp.json'))

    Thread(target=room.accept_clients, daemon=True).start()

    while True:
        try:
            room.update_clients()
            time.sleep(1 / room.tick_rate)

        except KeyboardInterrupt:
            for player in room.players:
                if player is not None:
                    player.disconnect()

        except Exception as e:
            print(e, file=sys.stderr)
