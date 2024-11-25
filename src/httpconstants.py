from typing import Final

OCTET: Final[tuple[bytes]]   = tuple(octet.to_bytes() for octet in range(256))
CHAR: Final[tuple[bytes]]    = OCTET[:128]
UPALPHA: Final[tuple[bytes]] = tuple(filter(bytes.isupper, CHAR))
LOALPHA: Final[tuple[bytes]] = tuple(filter(bytes.islower, CHAR))
ALPHA: Final[tuple[bytes]]   = UPALPHA + LOALPHA
DIGIT: Final[tuple[bytes]]   = tuple((i.to_bytes() for i in range(10)))
CTL: Final[tuple[bytes]]     = CHAR[0:32] + (CHAR[127],)
CR: Final[bytes]             = b'\r'
LF: Final[bytes]             = b'\n'
SP: Final[bytes]             = b' '
HT: Final[bytes]             = b'\t'
DQ: Final[bytes]             = b'"'
CRLF: Final[bytes]           = CR + LF
HEX: Final[tuple[bytes]]     = b'A' , b'B' , b'C' , b'D' , b'E' , b'F' , b'a' , b'b' , b'c' , b'd' , b'e' , b'f' , *DIGIT