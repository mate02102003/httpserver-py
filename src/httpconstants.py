from typing import Final

CHAR: Final[tuple[str]]    = tuple(octet.to_bytes().decode("ascii") for octet in range(128))
UPALPHA: Final[tuple[str]] = tuple(filter(str.isupper, CHAR))
LOALPHA: Final[tuple[str]] = tuple(filter(str.islower, CHAR))
ALPHA: Final[tuple[str]]   = UPALPHA + LOALPHA
DIGIT: Final[tuple[str]]   = tuple(map(str, range(10)))
CTL: Final[tuple[str]]     = CHAR[0:32] + (CHAR[127],)
CR: Final[str]             = '\r'
LF: Final[str]             = '\n'
SP: Final[str]             = ' '
HT: Final[str]             = '\t'
DQ: Final[str]             = '"'
CRLF: Final[str]           = CR + LF