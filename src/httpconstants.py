from typing import Final

OCTET: Final[tuple[bytes]] = tuple(octet.to_bytes() for octet in range(256))
CHAR: Final[tuple[str]]    = tuple(map(lambda b: b.decode("ascii"), OCTET[:128]))
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
HEX: Final[tuple[str]]     = "A" , "B" , "C" , "D" , "E" , "F" , "a" , "b" , "c" , "d" , "e" , "f" , *DIGIT