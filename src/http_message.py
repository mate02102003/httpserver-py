import dataclasses
import os
import time
import urllib.parse
import email.utils
import typing

from http import HTTPMethod, HTTPStatus

from pformat import PP_Repr
from http_constants import CRLF
from http_headers import HTTPHeaders

@dataclasses.dataclass(repr=False)
class HTTPRequest(PP_Repr):
    method: HTTPMethod           = dataclasses.field(init=False)
    target: str                  = dataclasses.field(init=False)
    query_params: dict[str, str] = dataclasses.field(init=False)
    version: tuple[int, int]     = dataclasses.field(default=(1, 1))
    headers: HTTPHeaders         = dataclasses.field(default_factory=HTTPHeaders)
    body: bytes                  = dataclasses.field(default=CRLF)

    def parse_request(self: typing.Self, request: bytes) -> None:
        request_lines = request.splitlines()

        head_end = request_lines.index(b'')

        request_head, self.body = CRLF.join(request_lines[:head_end]), CRLF.join(request_lines[head_end:])
        self.parse_request_head(request_head.decode())


    def parse_request_head(self: typing.Self, request_head: str) -> None:
        request_line, *headers = request_head.splitlines()

        method, target_and_params, version = request_line.split()
        try:
            target, params = target_and_params.split("?")
        except ValueError:
            target = target_and_params
            params = ""
        target = target.split("#")[0]

        self.method       = HTTPMethod(method)
        self.target       = urllib.parse.unquote(target)
        self.query_params = dict(tuple(param.split("=")) for param in params.split("&")) if len(params) != 0 else dict()
        self.version      = tuple(map(int, version.split("/")[1].split(".")))

        for line in headers:
            header_name, header_content = line.split(':', maxsplit=1)
            self.headers[header_name] = header_content.strip()
    
    def parse_request_body(self: typing.Self, request_body: bytes) -> None:
        self.body = request_body

@dataclasses.dataclass(repr=False)
class HTTPResponse(PP_Repr):
    status: HTTPStatus            = dataclasses.field(init=False)
    headers: HTTPHeaders          = dataclasses.field(default_factory=HTTPHeaders)

    head: bytes                   = dataclasses.field(init=False)
    body: bytes                   = dataclasses.field(init=False)

    gzip: bool                    = dataclasses.field(default=True)

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