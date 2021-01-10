from twisted.internet import reactor, task

# Required to import from shared modules
import sys
from pathlib import Path

file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

from server import manage
from server.mlserver import MoonlapseServer


if __name__ == '__main__':
    print(f"Starting MoonlapseMUD server")
    PORT: int = 42523
    reactor.listenTCP(PORT, MoonlapseServer())
    print(f"Server listening on port {42523}")
    reactor.run()
