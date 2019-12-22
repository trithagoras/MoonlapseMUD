import sys
from typing import *
import curses as ncurses
from game import Game


def main() -> None:
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

        ncurses.wrapper(game.start, ncurses)

    except Exception as e:
        ui_error = f"Error: Connection refused. {e}"

    if ui_error:
        print(ui_error, file=sys.stderr)


if __name__ == '__main__':
    main()
