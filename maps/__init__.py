from typing import *

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
