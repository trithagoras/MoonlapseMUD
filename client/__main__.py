import curses, sys
from game import Game

def main(s):
  uiError = None

  try:
      game = Game('localhost', 8081)
      game.connect()

      windowSize = s.getmaxyx()

      if windowSize[0] < game.size[0] or windowSize[1] < game.size[1]:
        uiError = "Sorry, your terminal window has to be at least %dx%d." % (game.size[0], game.size[1])

      else:
        game.start()

  except Exception as e:
      uiError = "Error: Connection refused. %s" % str(e)

  if uiError:
      print(uiError, file=sys.stderr)

if __name__ == '__main__':
  curses.wrapper(main)