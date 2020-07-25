from typing import *
import os

_ = ' '
_ = '!'
_ = '"'
WATER = '#'
LEAF = '$'
_ = '%'
_ = '&'
_ = '\''
GRASS = '('
_ = ')'
_ = '*'
_ = '+'
_ = ''
_ = '-'
_ = '.'
_ = '/'
_ = ':'
_ = ';'
_ = '<'
_ = '='
_ = '>'
_ = '?'
_ = '@'
_ = 'A'
WOOD = 'B'
_ = 'C'
_ = 'D'
_ = 'E'
_ = 'F'
_ = 'G'
_ = 'H'
_ = 'I'
_ = 'J'
_ = 'K'
_ = 'L'
_ = 'M'
_ = 'N'
_ = 'O'
_ = 'P'
_ = 'Q'
_ = 'R'
_ = 'S'
_ = 'T'
_ = 'U'
_ = 'V'
_ = 'W'
_ = 'X'
_ = 'Y'
SAND = 'Z'
_ = '['
_ = '\\'
_ = ']'
_ = '^'
_ = '_'
_ = '`'
_ = 'a'
_ = 'b'
_ = 'c'
_ = 'd'
_ = 'e'
_ = 'f'
_ = 'g'
_ = 'h'
NOTHING = 'i'
_ = 'j'
_ = 'k'
_ = 'l'
_ = 'm'
_ = 'n'
_ = 'o'
_ = 'p'
_ = 'q'
_ = 'r'
_ = 's'
_ = 't'
_ = 'u'
_ = 'v'
_ = 'w'
_ = 'x'
_ = 'y'
COBBLESTONE = 'z'
_ = '{'
_ = '|'
STONE = '}'


class AsciiRun:
    """
    A strip of a length of colours (84) possible represented as ascii characters of 32 (' ') and 96 ('`') excluding
    digits.
    """
    def __init__(self, asciirunstr):
        lengthstr = ''
        self.ascii = ''
        for c in asciirunstr:
            if c.isdigit():
                lengthstr += c
            else:
                self.ascii += c

        try:
            self.length = int(lengthstr)
        except ValueError:
            self.length = 1

    def inflate(self):
        return self.ascii * self.length


def ml2asciilist(ml_file: List[str]) -> List[str]:
    asciilist = []

    for line in ml_file:
        thisasciirun = ''
        thisasciiline = ''

        i = 0
        while i < len(line):
            c = line[i]
            thisasciirun += c
            while c.isdigit():
                i += 1
                c = line[i]
                thisasciirun += c
            ar = AsciiRun(thisasciirun)
            thisasciiline += ar.inflate()
            thisasciirun = ''
            i += 1

        asciilist.append(thisasciiline)

    return asciilist


def mappathtodict(mappath) -> List[str]:
    # Load in the map files and convert them to palatable data types to be sent out to the client.
    with open(mappath, 'r') as f:
        lines = [line.strip('\n') for line in f.readlines()]

    return ml2asciilist(lines)


class Room:
    DEFAULT: str = 'forest'

    def __init__(self, name: str):
        if not name:
            name = self.DEFAULT
        self.name = name

        pwd: str = os.path.dirname(__file__)
        path_to_room_dir = os.path.join(pwd, name)
        groundmappath = os.path.join(path_to_room_dir, 'ground.data')
        solidmappath = os.path.join(path_to_room_dir, 'solid.data')
        roofmappath = os.path.join(path_to_room_dir, 'roof.data')

        self.grounddata: List[str] = mappathtodict(groundmappath)
        self.soliddata: List[str] = mappathtodict(solidmappath)
        self.roofdata: List[str] = mappathtodict(roofmappath)

        self.height = len(self.grounddata)
        self.width = len(self.grounddata[0])

        self.groundmap: Dict[Tuple[int, int], chr] = {}
        self.solidmap: Dict[Tuple[int, int], chr] = {}
        self.roofmap: Dict[Tuple[int, int], chr] = {}

        self._is_unpacked = False

    def unpack(self):
        """
        Calculations to be run client side which unpacks the compressed map data into a more readable format.
        Don't call this before sending over the network unless you call pack first.
        """
        for y, (grow, srow, rrow) in enumerate(zip(self.grounddata, self.soliddata, self.roofdata)):
            for x, (gc, sc, rc) in enumerate(zip(grow, srow, rrow)):
                if gc != NOTHING:
                    self.groundmap[(y, x)] = gc
                if sc != NOTHING:
                    self.solidmap[(y, x)] = sc
                if rc != NOTHING:
                    self.roofmap[(y, x)] = rc

        self._is_unpacked = True

    def is_unpacked(self):
        return self._is_unpacked

    def pack(self):
        self.groundmap = {}
        self.solidmap = {}
        self.roofmap = {}

        self._is_unpacked = False


if __name__ == '__main__':
    asciilist = ml2asciilist([
        "64$",
        "30$}$}2$}2$2}24$",
        "24$6(10}24$",
        "24$5(4}2z4}3(22$",
        "24$4(5}2z5}6(18$",
        "21$5(6}4z6}5(2$3(12$",
        "20$6(5}6z5}11(11$"
    ])
    for line in asciilist:
        print(line)
