import curses
import os
import socket
import sys
from typing import *

# Required to import top level modules
from pathlib import Path
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

from client.utils import ClientState, NetworkState


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
    hostname = 'play.moonlapse.net'
    port = 42523

    # sys.argv will return something like ['client', 'localhost', 8123]
    n_args = len(sys.argv)

    if n_args not in (1, 2, 3):
        print("Usage: client [hostname=moonlapse.net] [port=42523]", file=sys.stderr)
        sys.exit(2)
    elif n_args >= 2:
        hostname = sys.argv[1]
        if n_args == 3:
            port = int(sys.argv[2])

    return hostname, port


def main() -> None:
    """
    The main entry point of the game. Starts a MainMenu object to connect to the specified remote server (specified in
    the command line arguments) to begin the game. Prints error details to stderr and exits if there was an exception.
    """
    address = handle_arguments()

    try:
        s = socket.create_connection(address)
    except ConnectionRefusedError:
        print(f"Connection to {address[0]}:{address[1]} refused. Is the server up?")
        sys.exit(-1)
    except Exception as e:
        print(f"Could not establish a connection to {address[0]}:{address[1]}. {e}.")
        sys.exit(-1)

    ns = NetworkState()
    ns.socket = s

    # Eliminate delay in the program after the ESC key is pressed
    os.environ.setdefault('ESCDELAY', '25')

    curses.wrapper(ClientState, ns)


if __name__ == '__main__':
    main()
