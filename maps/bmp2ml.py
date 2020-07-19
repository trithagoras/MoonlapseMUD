import argparse
from PIL import Image
import io
import math


class AsciiRun:
    """
    A strip of a length of colours (84) possible represented as ascii characters of 32 (' ') and 96 ('`') excluding
    digits.
    """
    def __init__(self, ascii: chr, length: int):
        self.ascii = ascii
        self.length = length

    def __str__(self):
        return f"{self.length if self.length > 1 else ''}{self.ascii}"

    def __repr__(self):
        return str(self)


def rgb2ascii(r, g, b) -> str:
    lookup = {
        (0, 0, 0): ' ',
        (0, 0, 110): '!',
        (0, 0, 220): '"',
        (0, 0, 255): '#',
        (0, 70, 0): '$',
        (0, 70, 110): '%',
        (0, 70, 220): '&',
        (0, 70, 255): '\'',
        (0, 140, 0): '(',
        (0, 140, 110): ')',
        (0, 140, 220): '*',
        (0, 140, 255): '+',
        (0, 210, 0): ',',
        (0, 210, 110): '-',
        (0, 210, 220): '.',
        (0, 210, 255): '/',
        (0, 255, 0): ':',
        (0, 255, 110): ';',
        (0, 255, 220): '<',
        (0, 255, 255): '=',
        (85, 0, 0): '>',
        (85, 0, 110): '?',
        (85, 0, 220): '@',
        (85, 0, 255): 'A',
        (85, 70, 0): 'B',
        (85, 70, 110): 'C',
        (85, 70, 220): 'D',
        (85, 70, 255): 'E',
        (85, 140, 0): 'F',
        (85, 140, 110): 'G',
        (85, 140, 220): 'H',
        (85, 140, 255): 'I',
        (85, 210, 0): 'J',
        (85, 210, 110): 'K',
        (85, 210, 220): 'L',
        (85, 210, 255): 'M',
        (85, 255, 0): 'N',
        (85, 255, 110): 'O',
        (85, 255, 220): 'P',
        (85, 255, 255): 'Q',
        (170, 0, 0): 'R',
        (170, 0, 110): 'S',
        (170, 0, 220): 'T',
        (170, 0, 255): 'U',
        (170, 70, 0): 'V',
        (170, 70, 110): 'W',
        (170, 70, 220): 'X',
        (170, 70, 255): 'Y',
        (170, 140, 0): 'Z',
        (170, 140, 110): '[',
        (170, 140, 220): '\\',
        (170, 140, 255): ']',
        (170, 210, 0): '^',
        (170, 210, 110): '_',
        (170, 210, 220): '`',
        (170, 210, 255): 'a',
        (170, 255, 0): 'b',
        (170, 255, 110): 'c',
        (170, 255, 220): 'd',
        (170, 255, 255): 'e',
        (255, 0, 0): 'f',
        (255, 0, 110): 'g',
        (255, 0, 220): 'h',
        (255, 0, 255): 'i',
        (255, 70, 0): 'j',
        (255, 70, 110): 'k',
        (255, 70, 220): 'l',
        (255, 70, 255): 'm',
        (255, 140, 0): 'n',
        (255, 140, 110): 'o',
        (255, 140, 220): 'p',
        (255, 140, 255): 'q',
        (255, 210, 0): 'r',
        (255, 210, 110): 's',
        (255, 210, 220): 't',
        (255, 210, 255): 'u',
        (255, 255, 0): 'v',
        (255, 255, 110): 'w',
        (255, 255, 220): 'x',
        (255, 255, 255): 'y',
        (191, 191, 191): 'z',
        (128, 128, 128): '{',
        (64, 64, 64): '|',
        (0, 0, 0): '}'
    }
    return lookup[(r, g, b)]


def main(path_to_img: str, path_to_out: str):
    img = Image.open(path_to_img).convert('RGB')
    pix = img.load()
    lines = []
    for y in range(img.size[1]):
        asciiruns = []
        for x in range(img.size[0]):
            r, g, b = pix[(x, y)]
            if not (r == g == b in (191, 128, 64, 0)):
                r = min(math.ceil(r / 85) * 85, 255)
                g = min(math.ceil(g / 70) * 70, 255)
                b = min(math.ceil(b / 110) * 110, 255)

            ascii = rgb2ascii(r, g, b)
            if asciiruns and asciiruns[-1].ascii == ascii:
                asciiruns[-1].length += 1
            else:
                asciiruns.append(AsciiRun(ascii, 1))
        lines.append(''.join(str(hr) for hr in asciiruns) + '\n')

    # Write out the resulting file
    if not path_to_out:
        path_to_out = path_to_img + '.ml'
    with io.open(path_to_out, 'w', encoding='utf-8') as fout:
        fout.writelines(lines)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Convert a 4-bit colour bitmap file to Moonlapse-compatible map data.")
    parser.add_argument('-i', metavar='--path_to_img', type=str, required=True,
                        help='the path on your system to the image to convert')
    parser.add_argument('-o', metavar='--path_to_output_file', type=str,
                        help='the path on your system to the output file, defaults to same as input with .ml appended')
    args = parser.parse_args()
    main(args.i, args.o)
