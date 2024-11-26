import dataclasses
import os
import email.utils
import time
import typing

from http import HTTPStatus

from pformat import PP_Repr
from httpheaders import HTTPHeaders
from httprequest import HTTPRequest


@dataclasses.dataclass
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
