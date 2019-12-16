import time, os, sys
from room import Room
from threading import Thread

if __name__ == '__main__':
  pwd: str = os.path.dirname(__file__)
  sys.path.append(os.path.abspath(os.path.join(pwd, '..')))
  sys.path.append(os.path.abspath(os.path.join(pwd, '../payload')))
  sys.path.append(os.path.abspath(os.path.join(pwd, '../server')))

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
