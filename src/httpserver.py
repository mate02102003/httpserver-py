from __future__ import annotations

import socket
import select
import sys
import ssl
import typing
import threading

if typing.TYPE_CHECKING:
    import pathlib

from time import sleep

from httprequest  import HTTPRequest
from httphandler  import HTTPHandler

class HTTPServer:
    sock: socket.socket

    version: str

    addr: tuple[str, int]
    clients: dict[tuple[str, int], socket.socket]

    handler: HTTPHandler

    running: bool

    def __init__(self: typing.Self, version: str = "HTTP/1.1", addr: tuple[str, int] = ("localhost", 42069), handler: HTTPHandler | None = None) -> None:
        self.version = version
        self.addr = addr
        self.clients = {}
        self.handler = handler if handler is not None else HTTPHandler()
        self.running = False

        if self.version_to_tuple() >= (2, 0):
            raise NotImplementedError("HTTP version 2 and 3 are not supported yet by this libary!")
        else:
            socket_kind = socket.SOCK_STREAM
        
        self.sock = socket.socket(socket.AF_INET, socket_kind)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(self.addr)
    
    def serv(self: typing.Self) -> typing.NoReturn:
        self.sock.listen()
        print(f"[INFO]: HTTP Server listening on: {self.addr[0]}:{self.addr[1]}")

        self.running = True

        while self.running:
            tuples: tuple[list[socket.socket], list, list] = select.select((self.sock, *self.clients.values()), (), (), 0.1)
            inputs: list[socket.socket] = tuples[0]

            for s in inputs:
                if s is self.sock:
                    try:
                        sock, addr = self.sock.accept()
                        self.clients[addr] = sock
                    except ConnectionError:
                        pass
                    except ssl.SSLError:
                        pass
                    except OSError:
                        pass
                else:
                    self.handle_request(s)
    
    def handle_request(self: typing.Self, sock: socket.socket) -> None:
        request: bytes = bytes()
        while len(chunk:=sock.recv(1024)) == 1024:
            request += chunk
        request += chunk

        if len(request) == 0:
            del self.clients[sock.getpeername()]
            sock.close()
            return

        http_request = HTTPRequest()
        http_request.parse_request(request)

        http_response = self.handler.generate_response(http_request, "gzip" in http_request.headers["Accept-Encoding"])
        print(f"[INFO]: {http_request.method} {http_request.target} {http_response.status}")

        sock.sendall(http_response.encode_head())
        sock.sendall(http_response.encode_body())

        if (conn:=getattr(http_request.headers, "Connection", None) is not None) and conn.lower() != "keep-alive":
            del self.clients[sock.getpeername()]
            sock.close()
    
    def version_to_tuple(self: typing.Self) -> tuple[int, int]:
        return tuple(map(int, self.version.split('/')[1].split('.')))

    def __enter__(self: typing.Self) -> typing.Self:
        return self
    
    def __exit__(self: typing.Self, *args) -> None:
        self.running = False
        self.sock.close()


class HTTPSServer(HTTPServer):
    def __init__(self: typing.Self, version: str = "HTTP/1.1", addr: tuple[str, int] = ("localhost", 42069), handler: HTTPHandler | None = None) -> None:
        super().__init__(version, addr, handler)
        self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

        self.ssl_context.load_default_certs(ssl.Purpose.CLIENT_AUTH)

        self.sock = self.ssl_context.wrap_socket(self.sock, server_side=True)
    
    def load_cert(self: typing.Self, certfile: str | bytes | pathlib.Path = "server.crt", keyfile: str | bytes | pathlib.Path = "server.key"):
        self.ssl_context.load_cert_chain(certfile, keyfile)

def main() -> None:
    addr = ""
    if len(sys.argv) > 1:
        http_port = int(sys.argv[1])
        if len(sys.argv) > 2:
            https_port = int(sys.argv[2])
        else:
            https_port = 443
    else:
        http_port = 80
        https_port = 443
    
    with HTTPServer(addr=(addr, http_port)) as http_server, HTTPSServer(addr=(addr, https_port)) as https_server:
        http = threading.Thread(target=http_server.serv)
        https = threading.Thread(target=https_server.serv)

        http.start()
        https.start()

        https_server.load_cert()

        while http.is_alive() or https.is_alive():
            sleep(0.1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received, exiting.")
        exit(0)