import socket, json, time, os
from room import Room
from threading import Thread

if __name__ == '__main__':

  ip, port = '', 8081

  pwd = os.path.dirname(__file__)
  room = Room(ip, port, os.path.join(pwd, '../map.bmp.json'))

  Thread(target = room.acceptClients, daemon = True).start()

  while True:
    try:
      room.updatePlayers()

      room.updateClients()

      time.sleep(1 / room.tickrate)

    except KeyboardInterrupt:
      for player in room.players:
        if not player == None:
          player.disconnect()

      break