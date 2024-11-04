CHAR: tuple[str]    = tuple(octet.to_bytes().decode("ascii") for octet in range(128))
UPALPHA: tuple[str] = tuple(filter(str.isupper, CHAR))
LOALPHA: tuple[str] = tuple(filter(str.islower, CHAR))
ALPHA: tuple[str]   = UPALPHA + LOALPHA
DIGIT: tuple[str]   = tuple(map(str, range(10)))
CTL: tuple[str]     = CHAR[0:32] + CHAR[127]
CR: str             = '\r'
LF: str             = '\n'
SP: str             = ' '
HT: str             = '\t'
DQ: str             = '"'
CRLF: str           = CR + LF