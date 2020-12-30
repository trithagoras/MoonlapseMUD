from PIL import Image
import os

STONE = (0, 0, 0)
_ = (0, 0, 110)
_ = (0, 0, 220)
WATER = (0, 0, 255)
LEAF = (0, 70, 0)
_ = (0, 70, 110)
_ = (0, 70, 220)
_ = (0, 70, 255)
GRASS = (0, 140, 0)
_ = (0, 140, 110)
_ = (0, 140, 220)
_ = (0, 140, 255)
_ = (0, 210, 0)
_ = (0, 210, 110)
_ = (0, 210, 220)
_ = (0, 210, 255)
_ = (0, 255, 0)
_ = (0, 255, 110)
_ = (0, 255, 220)
_ = (0, 255, 255)
_ = (85, 0, 0)
_ = (85, 0, 110)
_ = (85, 0, 220)
_ = (85, 0, 255)
WOOD = (85, 70, 0)
_ = (85, 70, 110)
_ = (85, 70, 220)
_ = (85, 70, 255)
_ = (85, 140, 0)
_ = (85, 140, 110)
_ = (85, 140, 220)
_ = (85, 140, 255)
_ = (85, 210, 0)
_ = (85, 210, 110)
_ = (85, 210, 220)
_ = (85, 210, 255)
_ = (85, 255, 0)
_ = (85, 255, 110)
_ = (85, 255, 220)
_ = (85, 255, 255)
_ = (170, 0, 0)
_ = (170, 0, 110)
_ = (170, 0, 220)
_ = (170, 0, 255)
_ = (170, 70, 0)
_ = (170, 70, 110)
_ = (170, 70, 220)
_ = (170, 70, 255)
SAND = (170, 140, 0)
_ = (170, 140, 110)
_ = (170, 140, 220)
_ = (170, 140, 255)
_ = (170, 210, 0)
_ = (170, 210, 110)
_ = (170, 210, 220)
_ = (170, 210, 255)
_ = (170, 255, 0)
_ = (170, 255, 110)
_ = (170, 255, 220)
_ = (170, 255, 255)
_ = (255, 0, 0)
_ = (255, 0, 110)
_ = (255, 0, 220)
NOTHING = (255, 0, 255)
_ = (255, 70, 0)
_ = (255, 70, 110)
_ = (255, 70, 220)
_ = (255, 70, 255)
_ = (255, 140, 0)
_ = (255, 140, 110)
_ = (255, 140, 220)
_ = (255, 140, 255)
_ = (255, 210, 0)
_ = (255, 210, 110)
_ = (255, 210, 220)
_ = (255, 210, 255)
_ = (255, 255, 0)
_ = (255, 255, 110)
_ = (255, 255, 220)
_ = (255, 255, 255)
COBBLESTONE = (191, 191, 191)
_ = (128, 128, 128)
_ = (64, 64, 64)


class Room:
    def __init__(self, room_id, name, file_name):
        self.id = room_id
        self.name = name
        self._file_name = file_name

        self.height = 0
        self.width = 0

        self._ground = None
        self._solid = None
        self._ceiling = None

        self._unpack()

    def _unpack(self):
        mapsdir = os.path.dirname(os.path.realpath(__file__))
        mapdir = os.path.join(mapsdir, self._file_name)

        im = Image.open(os.path.join(mapdir, 'ground.png'))
        if im.getbands() == ('P',):
            im = im.convert('RGB')
        self.width, self.height = im.size
        self._ground = im.load()

        im = Image.open(os.path.join(mapdir, 'solid.png'))
        if im.getbands() == ('P',):
            im = im.convert('RGB')
        self._solid = im.load()

        im = Image.open(os.path.join(mapdir, 'ceiling.png'))
        if im.getbands() == ('P',):
            im = im.convert('RGB')
        self._ceiling = im.load()

    def at(self, what: str, y: int, x: int) -> (int, int, int):
        """
        returns terrain at given position where what is one of 'ground', 'solid', or 'ceiling'
        :param what: What are we looking at? One of 'ground', 'solid', or 'ceiling'
        :param y:
        :param x:
        :return: 3-tuple of RGB
        """
        if what == 'ground':
            map_data = self._ground
        elif what == 'solid':
            map_data = self._solid
        elif what == 'ceiling':
            map_data = self._ceiling
        else:
            raise ValueError(f"what must be one of 'ground', 'solid', or 'ceiling' - {what} provided instead")

        rgb = map_data[x, y]
        return rgb[0], rgb[1], rgb[2]

