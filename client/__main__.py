import curses, sys
from game import Game
from typing import *
from curses_helper import Window


def main(s: Window) -> None:
    hostname: str = 'moonlapse.net'
    port: int = 8081

    n_args: int = len(sys.argv)
    if n_args not in (1, 2, 3):
        print("Usage: client [hostname=moonlapse.net] [port=8081]", file=sys.stderr)
        sys.exit()
    elif n_args >= 2:
        hostname = sys.argv[1]
    elif n_args == 3:
        port = sys.argv[2]

    ui_error: Optional[str] = None

    try:
        game: Game = Game(hostname, port)
        game.connect()

        window_size: Tuple[int, int] = s.getmaxyx()

        if window_size[0] < game.size[0] or window_size[1] < game.size[1]:
            ui_error = "Sorry, your terminal window has to be at least %dx%d." % (game.size[0], game.size[1])

        else:
            game.start()

    except Exception as e:
        ui_error = "Error: Connection refused. %s" % str(e)

    if ui_error:
        print(ui_error, file=sys.stderr)


if __name__ == '__main__':
    curses.wrapper(main)
