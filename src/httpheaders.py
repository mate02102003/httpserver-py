import dataclasses
import typing

from pformat import PP_Repr

@dataclasses.dataclass(repr=False)
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

    def __getitem__(self: typing.Self, __key: str) -> str | None:
        for header_group in dataclasses.fields(self):
            if __key in getattr(self, header_group.name):
                return getattr(self, header_group.name)[__key]
    
    def __setitem__(self: typing.Self, __key: str, __value: str) -> str | None:
        for header_group in dataclasses.fields(self):
            if __key in getattr(self, header_group.name):
                getattr(self, header_group.name)[__key] = __value
                return
        
        self.other_headers[__key] = __value
    
    def get_headers(self:typing.Self) -> dict[str, str]:
        headers: dict[str, str] = dict()

        for header_group in dataclasses.fields(self):
            header_group_dict: dict[str, str | None] = getattr(self, header_group.name)
            for header_name, value in header_group_dict.items():
                if value is not None:
                    headers[header_name] = value
        
        return headers