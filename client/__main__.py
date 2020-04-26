import sys
from typing import *
from controller import MainMenu
import traceback


def handle_arguments() -> Tuple[str, int]:
    """
    Handles the arguments passed into the main module from the command line. Valid examples are:
        1. "client localhost 8081"
        2. "client localhost"
        3. "client"
    * In case 1, the hostname and port number of the server is explicitly stated so will be used.
    * Case 2 behaves like case 1, except the default port number of 8081 is used.
    * Case 3 behaves like case 2, except the default hostname of moonlapse.net is used.

    This function returns the specified hostname and port. It will also print an error to stderr and exit the
    application if the command line arguments were not of the correct form.

    :return: The hostname and/or port specified in the command line arguments, otherwise ('moonlapse.net', 8081).
    """
    hostname: str = 'moonlapse.net'
    port: int = 8081

    # sys.argv will return something like ['client', 'localhost', 8081]
    n_args: int = len(sys.argv)

    if n_args not in (1, 2, 3):
        print("Usage: client [hostname=moonlapse.net] [port=8081]", file=sys.stderr)
        sys.exit(2)
    elif n_args >= 2:
        hostname = sys.argv[1]
    elif n_args == 3:
        port = sys.argv[2]

    return hostname, port


def main() -> None:
    """
    The main entry point of the game. Starts a MainMenu object to connect to the specified remote server (specified in
    the command line arguments) to begin the game. Prints error details to stderr and exits if there was an exception.
    """
    hostname, port = handle_arguments()

    try:
        mainmenu = MainMenu(hostname, port)
        mainmenu.start()

    except Exception:
        # Print the whole stacktrace
        print(f"Error: Connection refused. Traceback: ", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
