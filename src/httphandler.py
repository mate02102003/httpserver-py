import dataclasses
import mimetypes
import gzip
import typing
import os
import os.path

from http import HTTPStatus, HTTPMethod

from httpmessage import HTTPRequest, HTTPResponse
from httpconstants import NOT_FOUND_PAGE, NOT_FOUND_PAGE_PATH
from httputil import optional

@dataclasses.dataclass
class HTTPHandler:
    @classmethod
    def generate_response(cls: type[typing.Self], request: HTTPRequest, _gzip: bool = True) -> HTTPResponse:
        response = HTTPResponse(gzip=_gzip)

        match request.method:
            case HTTPMethod.GET:
                cls.GET(response, request)
            case HTTPMethod.POST:
                cls.POST()
            case HTTPMethod.HEAD:
                cls.HEAD()
            case HTTPMethod.OPTIONS:
                cls.OPTIONS()
        
        return response
    
    @staticmethod
    def GET(response: HTTPResponse, request: HTTPRequest) -> None:
        if request.target.endswith("/"):
            request.target += "index.html"
        
        request.target = request.target.lstrip('/')
        response.headers["Content-Type"] = mimetypes.guess_type(request.target)[0]

        if not os.path.exists(request.target) or (request.target.endswith("not_found.html") and response.headers["Content-Type"] == "text/html"):
            response.status = HTTPStatus.NOT_FOUND

            if os.path.exists(NOT_FOUND_PAGE_PATH):
                with open(NOT_FOUND_PAGE_PATH, "br") as file:
                    file_data = file.read()
            else:
                file_data = NOT_FOUND_PAGE.encode()
            
            file_stat = None
        else:
            response.status = HTTPStatus.OK
            with open(request.target, "rb") as file:
                file_data = file.read()
                file_stat = os.fstat(file.fileno())
        
        response.headers["Connection"] = "keep-alive"
        
        if response.gzip:
            response.headers["Content-Encoding"] = "gzip"

            body = gzip.compress(file_data)
            response.headers["Content-Length"] = len(body)
        # elif request.headers.range_requests_headers["Range"].startswith("bytes"):
            # ranges = request.headers.range_requests_headers["Range"].split(";")

            # r = ranges[0]

            # ittr = map(int, r.split("=")[1].split("-"))

            # start = next(ittr)
            # try:
                # end = next(ittr)
            # except ValueError:
                # end = len(file_data) - 1

            # body = file_data[start : start+1024 if end == len(file_data) - 1 else end+1]

            # response.status = HTTPStatus.PARTIAL_CONTENT

            # response.headers["Content-Range"] = f"bytes={start}-{end}/{len(file_data)}"
            # response.headers["Content-Length"] = end - start + 1
        else:
            body = file_data
            response.headers["Content-Length"] = len(body)
        
        response.construct_head(request, file_stat)
        response.body = body
    
    @classmethod
    @optional
    def POST(cls: type[typing.Self]):
        pass

    @classmethod
    @optional
    def HEAD(cls: type[typing.Self]):
        pass

    @classmethod
    @optional
    def OPTIONS(cls: type[typing.Self]):
        pass
