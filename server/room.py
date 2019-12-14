import random, threading, json, socket
from player import Player

class Room:
  def __init__(self, ip, port, map):
    self.players = []
    self.walls = []

    self.maxPlayers = 100
    self.tickrate = 20

    self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.s.bind((ip, port))
    self.s.listen(16)

    with open(map) as data:
      mapData = json.load(data)
      self.walls = mapData['walls']
      self.width, self.height = mapData['size']

    for index in range(0, self.maxPlayers): # Create player spots in game object
      self.players.append(None)

  def acceptClients(self):
    while True:
      clientsocket, address = self.s.accept()
      
      for index in range(0, len(self.players)):
        if self.players[index] == None:
          playerid = index
          break
        else:
          playerid = -1

      if playerid == -1:
        clientsocket.send(bytes("full;", 'utf-8'))
        clientsocket.close()
        print("Connection from %s rejected." % address)
      else:
        print("Connection from %s. Assigning to player %d" % (address, playerid))
        initData = {'id': playerid, 'w': self.width, 'h': self.height, 'walls': self.walls, 't': self.tickrate}

        clientsocket.send(bytes(json.dumps(initData) + ";", 'utf-8'))
        self.players[playerid] = Player(clientsocket, initData)

        threading.Thread(target = self.listen, args = (playerid, ), daemon = True).start()

  def listen(self, playerid):
    while True:
      player = self.players[playerid]
      """
      recv = {
        do: move,
        payload: dir
      }
      """
      data = ""
      try:
        while True:
          data += player.clientsocket.recv(1024).decode('utf-8')

          if data[-1] == ";":
            break

      except:
        print("Player %d: Disconnected" % playerid)
        player.clientsocket.close()
        self.players[playerid] = None
        break

      try:
        data = json.loads(data[:-1])
        action = data['a']
        payload = data['p']

        pos = player.state['pos']
        
        if action == 'm': # Move
          if payload == 0 and pos['y'] - 1 > 0 and not any([pos['x'], pos['y'] - 1] == wall for wall in self.walls): # Up
            pos['y'] -= 1
          if payload == 1 and pos['x'] + 1 < self.width - 1 and not any([pos['x'] + 1, pos['y']] == wall for wall in self.walls): # Right
            pos['x'] += 1
          if payload == 2 and pos['y'] + 1 < self.height - 1 and not any([pos['x'], pos['y'] + 1] == wall for wall in self.walls): # Down
            pos['y'] += 1
          if payload == 3 and pos['x'] - 1 > 0 and not any([pos['x'] - 1, pos['y']] == wall for wall in self.walls): # Left
            pos['x'] -= 1

      except:
        pass

  def updatePlayers(self):
    for index in range(0, len(self.players)):
      player = self.players[index]

  def updateClients(self):
    players = []

    for index in range(0, len(self.players)):
      player = self.players[index]

      players.append(player.state if player else None)

    for player in self.players:
      if player:
        player.clientsocket.send(bytes(json.dumps({'p': players}) + ";", 'utf-8'))