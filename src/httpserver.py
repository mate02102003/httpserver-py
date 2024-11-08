import socket
import select
import sys
import ssl

from httprequest import HTTPRequest
from httpresponse import HTTPResponse

def handle_request(sock: socket.socket) -> None:
    try:
        request = sock.recv(1024 * 64).decode()
    except:
        return sock.close()

    if request:
        http_request = HTTPRequest()
        http_request.parse_request(request)
        print("[INFO]:", http_request.method.name, http_request.target, f"HTTP/{http_request.version[0]}.{http_request.version[1]}")
        response = HTTPResponse.generate_response(http_request, "gzip" in http_request.headers["Accept-Encoding"])
        sock.sendall(response.encode_head())
        print("[INFO]:", response.head.decode().splitlines()[0])
        sock.sendall(response.encode_body())
        if (conn:=getattr(http_request.headers, "Connection", None) is not None) and conn.lower() != "keep-alive":
            sock.close()
    
    return


def main(running: list[bool]) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as http_server, socket.socket(socket.AF_INET, socket.SOCK_STREAM) as https_server:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

        ssl_context.load_default_certs(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain("server.crt", "server.key")

        https_server = ssl_context.wrap_socket(https_server, server_side=True)

        http_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        https_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

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

        http_server.bind((addr, http_port))
        http_server.listen()
        https_server.bind((addr, https_port))
        https_server.listen()

        print(f"[INFO]: HTTP Server listening on: {addr}:{http_port}")
        print(f"[INFO]: HTTPS Server listening on: {addr}:{https_port}")

        inputs = [http_server, https_server]

        while running[0]:
            readable, _, _ = select.select(inputs, [], [], 0.01)
            readable: list[socket.socket] = readable

            for sock in readable:
                if sock is http_server or sock is https_server:
                    try:
                        client, _ = sock.accept()
                        inputs.append(client)
                    except ConnectionError:
                        pass
                    except ssl.SSLError:
                        pass
                else:
                    try:
                        handle_request(sock)
                    except ConnectionError:
                        sock.close()
                        inputs.remove(sock)
                        continue
                    except ssl.SSLError:
                        sock.close()
                        inputs.remove(sock)
                        continue

                    if sock._closed:
                        inputs.remove(sock)

        

if __name__ == "__main__":
    running: list[bool] = [True]
    try:
        main(running)
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received, exiting.")
        running[0] = False
        exit(0)