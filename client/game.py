import socket, json, curses, sys
from time import sleep
from threading import Thread

class Game:
  def __init__(self, host, port):
    self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.address = (host, port)

    self.playerid = 0
    self.game = {}
    self.walls = []
    self.facing = 0

  def move(self, direction):
    try:
      self.s.send(bytes(json.dumps({'a': 'm', 'p': direction}) + ";", "utf-8")) # Action: Move, payload: direction
      self.facing = direction 
    except:
      pass

  def connect(self):
    self.s.connect(self.address)
    message = ""
    while True:
      message += self.s.recv(1).decode('utf-8')
      if message[-1] == ";":
        if message[:-1] == 'full':
          print('Session is full.')
          sys.exit()
        else:
          data = json.loads(message[:-1])
          break

    self.size = (data['h'], data['w'])
    self.playerid = data['id']
    self.walls = data['walls']
    self.tickrate = data['t']

    self.window = curses.newwin(self.size[0], self.size[1], 0, 0)
    self.window.keypad(1)
    self.window.timeout(round(1000 / self.tickrate))

  def start(self):
    self.listen()
    self.getPlayerInput()

  def listen(self):
    Thread(target = self.update, daemon = True).start()

  def getPlayerInput(self):
    while self.game == {}:
      sleep(0.2)

    while True:
      try:
        key = self.window.getch()

        if key == curses.KEY_UP:
          self.move(0)
        elif key == curses.KEY_RIGHT:
          self.move(1)
        elif key == curses.KEY_DOWN:
          self.move(2)
        elif key == curses.KEY_LEFT:
          self.move(3)

        self.draw()

      except KeyboardInterrupt:
        break

  def update(self): # Update positions
    message = ""
    while True:
      try:
        message += self.s.recv(1).decode('utf-8')
        if message[-1] == ";":
            self.game = json.loads(message[:-1])
            message = ""
      except:
        message = ""

  def draw(self):
    self.window.erase()
    self.window.border(0) # Draw border

    for index in range(0, len(self.game['p'])): # Players
      player = self.game['p'][index]

      if not player == None:
        self.window.addch(player['pos']['y'], player['pos']['x'], player['c'])

    self.window.addstr(0, 2, "Moonlapse MUD 0.1")

    for wall in self.walls:
      self.window.addch(wall[1], wall[0], '▓')