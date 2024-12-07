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

import httpconstants
from httpmessage  import HTTPRequest
from httphandler  import HTTPHandler

class HTTPServer:
    sock: socket.socket

    version: str

    addr: tuple[str, int]
    clients: dict[tuple[str, int], socket.socket]
    currently_handling: set[tuple[str, int]]

    handler: HTTPHandler

    running: bool

    def __init__(self: typing.Self,
                 version: str = "HTTP/1.1",
                 addr: tuple[str, int] = ("localhost", 80),
                 handler: HTTPHandler | None = None) -> None:
        self.version = version
        self.addr = addr
        self.clients = {}
        self.currently_handling = set()
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
            tuples: tuple[list[socket.socket], list, list] = select.select((self.sock, *self.clients.values()), (), (), 0.001)
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
                    if s.getpeername() in self.currently_handling:
                        continue
                    
                    threading.Thread(target=self.handle_request, args=(s,)).start()
                    self.currently_handling.add(s.getpeername())
    
    def read_head(self: typing.Self, sock: socket.socket) -> bytes:
        head: bytes = bytes()

        EOF_reached: bool = False
        while not EOF_reached:
            chunk = sock.recv(1)

            head += chunk

            if head.endswith(httpconstants.CRLF * 2):
                return head[:-2]
            elif len(chunk) == 0:
                EOF_reached = True

        else:
            if len(head) == 0:
                return head
            
            peername = sock.getpeername()
            raise httpconstants.HTTPError(f"Incomplete head recived from {peername[0]}:{peername[1]}!")
        
    def handle_request(self: typing.Self, sock: socket.socket) -> None:
        sock_peername: tuple[str, int] = sock.getpeername()
        del self.clients[sock_peername]

        request_head: bytes = self.read_head(sock)

        if len(request_head) == 0:
            self.currently_handling.remove(sock_peername)
            return sock.close()

        http_request = HTTPRequest()
        http_request.parse_request_head(request_head.decode())

        if (body_len:=http_request.headers["Content-Length"]) is not None:
            request_body: bytes = sock.recv(body_len)

            if (request_body_len:=len(request_body)) < body_len:
                raise httpconstants.HTTPError(f"Request body length ({request_body_len} byte(s)) doesn't match the header information ({body_len} byte(s))!")

            http_request.parse_request_body(request_body.decode())

        http_response = self.handler.generate_response(http_request, "gzip" in http_request.headers["Accept-Encoding"])
        print(f"[INFO]: {http_request.method} {http_request.target} {http_response.status}")

        sock.sendall(http_response.encode_head())
        sock.sendall(http_response.encode_body())

        if (conn:=getattr(http_request.headers, "Connection", None) is not None) and conn.lower() == "keep-alive":
            self.clients[sock_peername] = sock
        else:
            sock.close()

        self.currently_handling.remove(sock_peername)
        
    
    def version_to_tuple(self: typing.Self) -> tuple[int, int]:
        return tuple(map(int, self.version.split('/')[1].split('.')))
    
    def close(self: typing.Self) -> None:
        self.running = False            
        self.sock.close()

    def __enter__(self: typing.Self) -> typing.Self:
        return self
    
    def __exit__(self: typing.Self, *args) -> None:
        if self.running:
            self.close()


class HTTPSServer(HTTPServer):
    certfile: str | bytes | pathlib.Path
    keyfile: str | bytes | pathlib.Path

    def __init__(self: typing.Self,
                 version: str = "HTTP/1.1",
                 addr: tuple[str, int] = ("localhost", 443),
                 handler: HTTPHandler | None = None) -> None:
        super().__init__(version, addr, handler)
        self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

        self.ssl_context.load_default_certs(ssl.Purpose.CLIENT_AUTH)

        self.certfile = "server.crt"
        self.keyfile  = "server.key"

        self.sock = self.ssl_context.wrap_socket(self.sock, server_side=True)
    
    def set_cert(self: typing.Self, certfile: str | bytes | pathlib.Path | None = None,
                 keyfile: str | bytes | pathlib.Path | None = None) -> None:
        if certfile is not None:
            self.certfile = certfile

        if keyfile is not None:
            self.keyfile = keyfile

    def load_cert(self: typing.Self):
        self.ssl_context.load_cert_chain(self.certfile, self.keyfile)
    
    @typing.override
    def serv(self: typing.Self) -> typing.NoReturn:
        self.load_cert()

        super().serv()

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

        # http.start()
        https.start()

        while http.is_alive() or https.is_alive():
            sleep(0.1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received, exiting.")
        exit(0)