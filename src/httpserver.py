import socket
import os
import os.path
import gzip
import mimetypes
import select
import dataclasses
import urllib.parse
import email.utils
import time
import sys

from http import HTTPStatus, HTTPMethod

from ppformat import PP_Repr

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
 
@dataclasses.dataclass
class HTTPHeaders(PP_Repr):
    authentication_headers: dict[str, str | None]           = dataclasses.field(default_factory=lambda: {"WWW-Authenticate": None, "Authorization": None, "Proxy-Authenticate": None, "Proxy-Authorization": None}, init=False)
    caching_headers: dict[str, str | None]                  = dataclasses.field(default_factory=lambda: {"Age": None, "Cache-Control": None, "Clear-Site-Data": None, "Expires": None, "No-Vary-Search": None}, init=False)
    conditionals_headers: dict[str, str | None]             = dataclasses.field(default_factory=lambda: {"Last-Modified": None, "ETag": None, "If-Match": None, "If-None-Match": None, "If-Modified-Since": None, "If-Unmodified-Since": None, "Vary": None}, init=False)
    connection_management_headers: dict[str, str | None]    = dataclasses.field(default_factory=lambda: {"Connection": None, "Keep-Alive": None}, init=False)
    content_negotiation_headers: dict[str, str | None]      = dataclasses.field(default_factory=lambda: {"Accept": None, "Accept-Encoding": None, "Accept-Language": None, "Accept-Patch": None, "Accept-Post": None}, init=False)
    controls_headers: dict[str, str | None]                 = dataclasses.field(default_factory=lambda: {"Expect": None, "Max-Forwards": None}, init=False)
    cookies_headers: dict[str, str | None]                  = dataclasses.field(default_factory=lambda: {"Cookie": None, "Set-Cookie": None}, init=False)
    cors_headers: dict[str, str | None]                     = dataclasses.field(default_factory=lambda: {"Access-Control-Allow-Credentials": None, "Access-Control-Allow-Headers": None, "Access-Control-Allow-Methods": None, "Access-Control-Allow-Origin": None, "Access-Control-Expose-Headers": None, "Access-Control-Max-Age": None, "Access-Control-Request-Headers": None, "Access-Control-Request-Method": None, "Origin": None, "Timing-Allow-Origin": None}, init=False)
    downloads_headers: dict[str, str | None]                = dataclasses.field(default_factory=lambda: {"Content-Disposition": None}, init=False)
    integrity_digests_headers: dict[str, str | None]        = dataclasses.field(default_factory=lambda: {"Content-Digest": None, "Repr-Digest": None, "Want-Content-Digest": None, "Want-Repr-Digest": None}, init=False)
    message_body_information_headers: dict[str, str | None] = dataclasses.field(default_factory=lambda: {"Content-Length": None, "Content-Type": None, "Content-Encoding": None, "Content-Language": None, "Content-Location": None}, init=False)
    proxies_headers: dict[str, str | None]                  = dataclasses.field(default_factory=lambda: {"Forwarded": None, "Via": None}, init=False)
    range_requests_headers: dict[str, str | None]           = dataclasses.field(default_factory=lambda: {"Accept-Ranges": None, "Range": None, "If-Range": None, "Content-Range": None}, init=False)
    redirects_headers: dict[str, str | None]                = dataclasses.field(default_factory=lambda: {"Location": None, "Refresh": None}, init=False)
    request_context_headers: dict[str, str | None]          = dataclasses.field(default_factory=lambda: {"From": None, "Host": None, "Referer": None, "Referrer-Policy": None, "User-Agent": None}, init=False)
    response_context_headers: dict[str, str | None]         = dataclasses.field(default_factory=lambda: {"Allow": None, "Server": None}, init=False)
    security_headers: dict[str, str | None]                 = dataclasses.field(default_factory=lambda: {"Cross-Origin-Embedder-Policy": None, "Cross-Origin-Opener-Policy": None, "Cross-Origin-Resource-Policy": None, "Content-Security-Policy": None, "Content-Security-Policy-Report-Only": None, "Permissions-Policy": None, "Reporting-Endpoints": None, "Strict-Transport-Security": None, "Upgrade-Insecure-Requests": None, "X-Content-Type-Options": None, "X-Frame-Options": None, "X-Permitted-Cross-Domain-Policies": None, "X-Powered-By": None, "X-XSS-Protection": None}, init=False)
    fetch_metadata_request_headers: dict[str, str | None]   = dataclasses.field(default_factory=lambda: {"Sec-Fetch-Site": None, "Sec-Fetch-Mode": None, "Sec-Fetch-User": None, "Sec-Fetch-Dest": None, "Sec-Purpose": None, "Service-Worker-Navigation-Preload": None}, init=False)
    server_sent_events_headers: dict[str, str | None]       = dataclasses.field(default_factory=lambda: {"Report-To": None}, init=False)
    transfer_coding_headers: dict[str, str | None]          = dataclasses.field(default_factory=lambda: {"Transfer-Encoding": None, "TE": None, "Trailer": None}, init=False)
    websockets_headers: dict[str, str | None]               = dataclasses.field(default_factory=lambda: {"Sec-WebSocket-Accept": None}, init=False)
    other_headers: dict[str, str | None]                    = dataclasses.field(default_factory=lambda: {}, init=False)

class HTTPRequest:
    method: HTTPMethod | None = None
    target: str = "/index.html"
    version: str = "HTTP/1.0"
    headers: HTTPHeaders
    body: str = "\r\n"

    @staticmethod
    def parse_request(request: str) -> "HTTPRequest":
        http_request = HTTPRequest()

        http_request.headers = HTTPHeaders()
        http_request.headers.format_join = "\n"
        http_request.headers.format_indent = 12

        request_line, *rest = request.splitlines()
        headers, http_request.body = rest[:rest.index("")], "\r\n".join(rest[rest.index(""):])
        http_request.method, http_request.target, http_request.version = request_line.split()
        http_request.target = urllib.parse.unquote(http_request.target)
        for line in headers:
            header_name, header_content = line.split(':', maxsplit=1)

            for header_type in [getattr(http_request.headers, h) for h in dir(http_request.headers) if not h.startswith("_") and getattr(PP_Repr, h, None) is None]:
                header_type: dict[str, str | None]

                if header_type.get(header_name, False) is None:
                    header_type[header_name] = header_content.strip()  

        return http_request
    
    def __repr__(self) -> str:
        return f"HTTPRequest(\n\thead: {self.method} {self.target} {self.version}\n\theaders: {self.headers}\n\tbody: {self.body}\n)\n"

@dataclasses.dataclass
class HTTPResponse(PP_Repr):
    status: HTTPStatus = HTTPStatus.OK
    headers: HTTPHeaders = dataclasses.field(default_factory=HTTPHeaders)
    querry_params: dict[str, str] = dataclasses.field(default_factory=dict)

    head: bytes = dataclasses.field(init=False)
    body: bytes = dataclasses.field(init=False)

    gzip: bool = True

    @staticmethod
    def generate_response(request: "HTTPRequest", _gzip: bool = True) -> "HTTPResponse":
        response = HTTPResponse(gzip=_gzip)

        match request.method:
            case HTTPMethod.GET:
                if request.target.endswith("/"):
                    request.target += "index.html"
                
                request.target = request.target.lstrip('/')

                if not os.path.exists(request.target) or request.target.endswith("not_found.html"):
                    response.status = HTTPStatus.NOT_FOUND

                    if os.path.exists(NOT_FOUND_PAGE_PATH):
                        with open(NOT_FOUND_PAGE_PATH, "br") as file:
                            file_data = file.read()
                    else:
                        file_data = NOT_FOUND_PAGE.encode()
                    
                    file_stat = None
                else:
                    with open(request.target, "rb") as file:
                        file_data = file.read()
                        file_stat = os.fstat(file.fileno())
                
                response.headers.connection_management_headers["Connection"] = "keep-alive"
                response.headers.message_body_information_headers["Content-Type"] = mimetypes.guess_type(request.target)[0]
                
                if response.gzip:
                    response.headers.message_body_information_headers["Content-Encoding"] = "gzip"

                    body = gzip.compress(file_data)
                    response.headers.message_body_information_headers["Content-Length"] = len(body)
                elif request.headers.range_requests_headers["Range"].startswith("bytes"):
                    ranges = request.headers.range_requests_headers["Range"].split(";")

                    r = ranges[0]

                    ittr = map(int, r.split("=")[1].split("-"))

                    start = next(ittr)
                    try:
                        end = next(ittr)
                    except ValueError:
                        end = len(file_data) - 1

                    body = file_data[start : start+1024 if end == len(file_data) - 1 else end+1]

                    response.status = HTTPStatus.PARTIAL_CONTENT

                    response.headers.range_requests_headers["Content-Range"] = f"bytes={start}-{end}/{len(file_data)}"
                    response.headers.message_body_information_headers["Content-Length"] = end - start + 1
                else:
                    body = file_data
                    response.headers.message_body_information_headers["Content-Length"] = len(body)
                

                head = f"{request.version} {response.status.value} {response.status.name}\r\n".encode()

                response.headers.other_headers["Date"] = email.utils.formatdate(time.time(), localtime=True)
                if file_stat is not None:
                    response.headers.conditionals_headers["Last-Modified"] = email.utils.formatdate(file_stat.st_mtime, localtime=True)

                for header_dict_name in filter(lambda s: "headers" in s, dir(response.headers)):
                    for header_name, header_value in getattr(response.headers, header_dict_name).items():
                        if header_value is not None:
                            head += f"{header_name}: {header_value}\r\n".encode()


                response.head = head
                response.body = body

                return response

            case HTTPMethod.POST:
                pass
            case HTTPMethod.HEAD:
                pass
            case HTTPMethod.OPTIONS:
                pass
    
    def send_head(self, sock: socket.socket) -> None:
        sock.sendall(self.head)
        sock.sendall(b"\r\n")
    
    def send_body(self, sock: socket.socket) -> int:
        sock.sendall(self.body)
        
        


def handle_request(sock: socket.socket) -> None:
    try:
        request = sock.recv(1024 * 64).decode()
    except:
        return sock.close()

    if request:
        http_request = HTTPRequest.parse_request(request)
        print(request)
        response = HTTPResponse.generate_response(http_request, "gzip" in http_request.headers.content_negotiation_headers["Accept-Encoding"])
        response.send_head(sock)
        print(response.head.decode())
        response.send_body(sock)
        if len(response.body) <= 16:
            print(response.body)
        else:
            print(response.body[:16], f"... ({len(response.body) - 16} more bytes)\n")
    else:
        return sock.close()


def main() -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    addr, port = "", int(sys.argv[1])

    server.bind((addr, port))
    server.listen()

    print(f"Server listening on: {addr}:{port}")

    inputs = [server]

    while True:
        readable, _, _ = select.select(inputs, [], [], 0.01)
        readable: list[socket.socket] = readable

        for sock in readable:
            if sock is server:
                client, _ = server.accept()
                inputs.append(client)
            else:
                handle_request(sock)

                if sock._closed:
                    inputs.remove(sock)

        

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received, exiting.")
        exit(0)