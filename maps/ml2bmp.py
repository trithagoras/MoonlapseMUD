import argparse
from typing import *
from PIL import Image


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

    def inflate(self) -> List[Tuple[int, int, int]]:
        lookup = {
            ' ': (0, 0, 0),
            '!': (0, 0, 110),
            '"': (0, 0, 220),
            '#': (0, 0, 255),
            '$': (0, 70, 0),
            '%': (0, 70, 110),
            '&': (0, 70, 220),
            '\'': (0, 70, 255),
            '(': (0, 140, 0),
            ')': (0, 140, 110),
            '*': (0, 140, 220),
            '+': (0, 140, 255),
            ',': (0, 210, 0),
            '-': (0, 210, 110),
            '.': (0, 210, 220),
            '/': (0, 210, 255),
            ':': (0, 255, 0),
            ';': (0, 255, 110),
            '<': (0, 255, 220),
            '=': (0, 255, 255),
            '>': (85, 0, 0),
            '?': (85, 0, 110),
            '@': (85, 0, 220),
            'A': (85, 0, 255),
            'B': (85, 70, 0),
            'C': (85, 70, 110),
            'D': (85, 70, 220),
            'E': (85, 70, 255),
            'F': (85, 140, 0),
            'G': (85, 140, 110),
            'H': (85, 140, 220),
            'I': (85, 140, 255),
            'J': (85, 210, 0),
            'K': (85, 210, 110),
            'L': (85, 210, 220),
            'M': (85, 210, 255),
            'N': (85, 255, 0),
            'O': (85, 255, 110),
            'P': (85, 255, 220),
            'Q': (85, 255, 255),
            'R': (170, 0, 0),
            'S': (170, 0, 110),
            'T': (170, 0, 220),
            'U': (170, 0, 255),
            'V': (170, 70, 0),
            'W': (170, 70, 110),
            'X': (170, 70, 220),
            'Y': (170, 70, 255),
            'Z': (170, 140, 0),
            '[': (170, 140, 110),
            '\\': (170, 140, 220),
            ']': (170, 140, 255),
            '^': (170, 210, 0),
            '_': (170, 210, 110),
            '`': (170, 210, 220),
            'a': (170, 210, 255),
            'b': (170, 255, 0),
            'c': (170, 255, 110),
            'd': (170, 255, 220),
            'e': (170, 255, 255),
            'f': (255, 0, 0),
            'g': (255, 0, 110),
            'h': (255, 0, 220),
            'i': (255, 0, 255),
            'j': (255, 70, 0),
            'k': (255, 70, 110),
            'l': (255, 70, 220),
            'm': (255, 70, 255),
            'n': (255, 140, 0),
            'o': (255, 140, 110),
            'p': (255, 140, 220),
            'q': (255, 140, 255),
            'r': (255, 210, 0),
            's': (255, 210, 110),
            't': (255, 210, 220),
            'u': (255, 210, 255),
            'v': (255, 255, 0),
            'w': (255, 255, 110),
            'x': (255, 255, 220),
            'y': (255, 255, 255),
            'z': (191, 191, 191),
            '{': (128, 128, 128),
            '|': (64, 64, 64),
            '}': (0, 0, 0)
        }
        try:
            r, g, b = lookup[self.ascii]
        except KeyError:
            r, g, b = 0, 0, 0
        return [(r, g, b)] * self.length

    def __str__(self):
        return f"{self.length if self.length > 1 else ''}{self.ascii}"

    def __repr__(self):
        return str(self)


def combinelists(lists: List[List[Any]]):
    rlist = []
    for l in lists:
        rlist += l
    return rlist


def main(path_to_ml, path_to_bmp):
    lines = []
    pixlist = []
    with open(path_to_ml, 'r') as fin:
        lines = fin.readlines()
    lines = [line.strip('\n') for line in lines]

    width = None

    for line in lines:
        if line == '401ML110M':
            print('hey')
        thiswidth = 0
        thisasciirun = ''
        i = 0
        while i < len(line):
            c = line[i]
            thisasciirun += c
            while c.isdigit():
                i += 1
                c = line[i]
                thisasciirun += c
            ar = AsciiRun(thisasciirun)
            thiswidth += ar.length
            pixlist += ar.inflate()
            thisasciirun = ''
            i += 1

        if width and width != thiswidth:
            print(f"Uneven image width line {line}! Exiting.")
            exit(-1)
        else:
            width = thiswidth

    height = len(lines)

    print(width, height)
    print(len(pixlist))

    img = Image.new('RGB', (width, height))
    img.putdata(pixlist)

    if path_to_bmp is None:
        path_to_bmp = path_to_ml + '.bmp'
    img.save(path_to_bmp)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Convert a Moonlapse-compatible map data file to a bitmap file.")
    parser.add_argument('-i', metavar='--path_to_ml_file', type=str, required=True,
                        help='the path on your system to the Moonlapse-compatible map data file to convert')
    parser.add_argument('-o', metavar='--path_to_output_file', type=str,
                        help='the path on your system to the output file, defaults to same as input with .bmp appended')
    args = parser.parse_args()
    main(args.i, args.o)