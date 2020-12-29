from PIL import Image
import os


BUSH_WALL = (0, 255, 0)
GRASS_FLOOR = (0, 128, 0)
STONE_WALL = (192, 192, 192)
STONE_FLOOR = (96, 96, 96)
WOOD_WALL = (220, 180, 132)
WOOD_FLOOR = (110, 90, 66)
WATER = (0, 0, 255)
SAND_FLOOR = (255, 255, 0)

SOLIDS = {
    BUSH_WALL, STONE_WALL, WOOD_WALL, WATER
}


class Room:
    def __init__(self, room_id, name, file_name):
        self.id = room_id
        self.name = name
        self._file_name = file_name

        self.height = 0
        self.width = 0

        self._ground = None
        self._ceiling = None

        self._unpack()

    def _unpack(self):
        mapsdir = os.path.dirname(os.path.realpath(__file__))
        mapdir = os.path.join(mapsdir, self._file_name)
        im = Image.open(os.path.join(mapdir, 'ground.png'))
        self.width, self.height = im.size
        self._ground = im.load()
        self._ceiling = Image.open(os.path.join(mapdir, 'ceiling.png')).load()

    def at(self, y, x) -> (int, int, int):
        """
        returns ground info at given position
        :param y:
        :param x:
        :return: 3-tuple of RGB
        """
        rgba = self._ground[x, y]
        return rgba[0], rgba[1], rgba[2]

    def is_ceil_at(self, y, x) -> bool:
        """
        returns if ceiling is at given position
        :param y:
        :param x:
        :return: true if ceiling
        """
        return self._ceiling[x, y] == (0, 0, 0, 255)
