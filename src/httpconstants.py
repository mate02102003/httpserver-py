from typing import Final, Literal

OCTET: Final[tuple[bytes]]   = tuple(octet.to_bytes() for octet in range(256))
CHAR: Final[tuple[bytes]]    = OCTET[:128]
UPALPHA: Final[tuple[bytes]] = tuple(filter(bytes.isupper, CHAR))
LOALPHA: Final[tuple[bytes]] = tuple(filter(bytes.islower, CHAR))
ALPHA: Final[tuple[bytes]]   = UPALPHA + LOALPHA
DIGIT: Final[tuple[bytes]]   = tuple((i.to_bytes() for i in range(10)))
CTL: Final[tuple[bytes]]     = CHAR[0:32] + (CHAR[127],)
CR: Literal[b'\r']           = b'\r'
LF: Literal[b'\n']           = b'\n'
SP: Literal[b' ']            = b' '
HT: Literal[b'\t']           = b'\t'
DQ: Literal[b'\"']           = b'"'
CRLF: Literal[b'\r\n']       = CR + LF
HEX: Final[tuple[bytes]]     = b'A' , b'B' , b'C' , b'D' , b'E' , b'F' , b'a' , b'b' , b'c' , b'd' , b'e' , b'f' , *DIGIT

class HTTPError(Exception):
    pass

NOT_FOUND_PAGE_PATH = "not_found.html"
NOT_FOUND_PAGE = """
                 <!DOCTYPE html>
                 <html lang="en">
                 <head>
                     <meta charset="UTF-8">
                     <meta name="viewport" content="width=device-width, initial-scale=1.0">
                     <title>Not found</title>
                     <link rel="icon" type="image/x-icon" href="/favicon.ico">
                 </head>
                 <body>
                     <h1>404 not found!</h1>
                 </body>
                 </html>
                 """