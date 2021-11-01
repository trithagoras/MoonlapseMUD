from twisted.internet import reactor, task

# Required to import from shared modules
import sys
import os
from pathlib import Path

file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

import get_dependencies  # This will create a virtual environment all dependencies on it
get_dependencies.install_requirements(parent)

# Ensure from now on, we are running in a virtual environment with all dependencies installed
vpy = get_dependencies.get_vpy_from_root_dir(parent)
if sys.executable != vpy:
    import subprocess
    subprocess.run([vpy, parent] + sys.argv[1:])
    exit()

from server import manage
from server.mlserver import MoonlapseServer


if __name__ == '__main__':
    print(f"Starting MoonlapseMUD server")
    PORT: int = 42523
    reactor.listenTCP(PORT, MoonlapseServer())
    print(f"Server listening on port {42523}")
    reactor.run()
