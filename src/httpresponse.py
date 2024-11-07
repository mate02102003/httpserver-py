import dataclasses
import os
import os.path
import mimetypes
import gzip
import email.utils
import time
import typing

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
    status: HTTPStatus            = dataclasses.field(init=False)
    headers: HTTPHeaders          = dataclasses.field(default_factory=HTTPHeaders)

    head: bytes                   = dataclasses.field(init=False)
    body: bytes                   = dataclasses.field(init=False)

    gzip: bool                    = dataclasses.field(default=True)

    @staticmethod
    def generate_response(request: HTTPRequest, _gzip: bool = True) -> "HTTPResponse":
        response = HTTPResponse(gzip=_gzip)

        match request.method:
            case HTTPMethod.GET:
                return response.GET(request)

            case HTTPMethod.POST:
                pass
            case HTTPMethod.HEAD:
                pass
            case HTTPMethod.OPTIONS:
                pass
    
    def GET(self: typing.Self, request: HTTPRequest) -> typing.Self:
        if request.target.endswith("/"):
            request.target += "index.html"
        
        request.target = request.target.lstrip('/')
        self.headers["Content-Type"] = mimetypes.guess_type(request.target)[0]

        if not os.path.exists(request.target) or (request.target.endswith("not_found.html") and self.headers["Content-Type"] == "text/html"):
            self.status = HTTPStatus.NOT_FOUND

            if os.path.exists(NOT_FOUND_PAGE_PATH):
                with open(NOT_FOUND_PAGE_PATH, "br") as file:
                    file_data = file.read()
            else:
                file_data = NOT_FOUND_PAGE.encode()
            
            file_stat = None
        else:
            self.status = HTTPStatus.OK
            with open(request.target, "rb") as file:
                file_data = file.read()
                file_stat = os.fstat(file.fileno())
        
        self.headers["Connection"] = "keep-alive"
        
        if self.gzip:
            self.headers["Content-Encoding"] = "gzip"

            body = gzip.compress(file_data)
            self.headers["Content-Length"] = len(body)
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

            self.status = HTTPStatus.PARTIAL_CONTENT

            self.headers["Content-Range"] = f"bytes={start}-{end}/{len(file_data)}"
            self.headers["Content-Length"] = end - start + 1
        else:
            body = file_data
            self.headers["Content-Length"] = len(body)
        
        self.construct_head(request, file_stat)
        self.body = body

        return self
    
    def construct_head(self: typing.Self, request: HTTPRequest, file_stat: os.stat_result | None) -> None:
        head = f"HTTP/{request.version[0]}.{request.version[1]} {self.status.value} {self.status.name}\r\n".encode()

        self.headers["Date"] = email.utils.formatdate(time.time(), localtime=True)
        if file_stat is not None:
            self.headers["Last-Modified"] = email.utils.formatdate(file_stat.st_mtime, localtime=True)

        for header_name, header_value in self.headers.get_headers().items():
            head += f"{header_name}: {header_value}\r\n".encode()

        self.head = head

    def encode_head(self: typing.Self) -> bytes:
        return self.head + b"\r\n"
    
    def encode_body(self: typing.Self) -> bytes:
        return self.body
