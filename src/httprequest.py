import dataclasses
import urllib.parse

from http import HTTPMethod

from pformat import PP_Repr
from httpheaders import HTTPHeaders

@dataclasses.dataclass(repr=False)
class HTTPRequest(PP_Repr):
    method: HTTPMethod   = dataclasses.field(init=False)
    target: str          = dataclasses.field(init=False)
    version: str         = dataclasses.field(default="HTTP/1.1")
    headers: HTTPHeaders = dataclasses.field(default_factory=HTTPHeaders)
    body: str            = dataclasses.field(default="\r\n")

    @staticmethod
    def parse_request(request: str) -> "HTTPRequest":
        http_request = HTTPRequest()

        request_line, *rest = request.splitlines()

        headers, http_request.body = rest[:rest.index("")], "\r\n".join(rest[rest.index(""):])

        method, http_request.target, http_request.version = request_line.split()
        http_request.method = HTTPMethod(method)
        http_request.target = urllib.parse.unquote(http_request.target)

        for line in headers:
            header_name, header_content = line.split(':', maxsplit=1)
            http_request.headers[header_name] = header_content.strip()  

        return http_request
