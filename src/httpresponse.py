import dataclasses
import os.path
import mimetypes
import gzip
import email.utils
import time
import socket

from http import HTTPStatus, HTTPMethod

from pformat import PP_Repr
from httpheaders import HTTPHeaders
from httprequest import HTTPRequest


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
class HTTPResponse(PP_Repr):
    status: HTTPStatus = HTTPStatus.OK
    headers: HTTPHeaders = dataclasses.field(default_factory=HTTPHeaders)
    querry_params: dict[str, str] = dataclasses.field(default_factory=dict)

    head: bytes = dataclasses.field(init=False)
    body: bytes = dataclasses.field(init=False)

    gzip: bool = True

    @staticmethod
    def generate_response(request: HTTPRequest, _gzip: bool = True) -> "HTTPResponse":
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
                
                response.headers["Connection"] = "keep-alive"
                response.headers["Content-Type"] = mimetypes.guess_type(request.target)[0]
                
                if response.gzip:
                    response.headers["Content-Encoding"] = "gzip"

                    body = gzip.compress(file_data)
                    response.headers["Content-Length"] = len(body)
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

                    response.headers["Content-Range"] = f"bytes={start}-{end}/{len(file_data)}"
                    response.headers["Content-Length"] = end - start + 1
                else:
                    body = file_data
                    response.headers["Content-Length"] = len(body)
                

                head = f"HTTP/{request.version[0]}.{request.version[1]} {response.status.value} {response.status.name}\r\n".encode()

                response.headers["Date"] = email.utils.formatdate(time.time(), localtime=True)
                if file_stat is not None:
                    response.headers["Last-Modified"] = email.utils.formatdate(file_stat.st_mtime, localtime=True)

                for header_name, header_value in response.headers.get_headers().items():
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
