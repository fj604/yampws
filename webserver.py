import usocket as socket
import utime
import gc
import network


DOC_ROOT_PREFIX = ""
PORT = const(80)
BIND_IP = "0.0.0.0"


HTTP_VERSION = b"HTTP/1.0"
HTTP_RESPONSE = {
    200: b"OK",
    400: b"Bad Request",
    404: b"Not Found",
    405: b"Method Not Allowed",
    500: b"Server Error",
    501: b"Not Implemented"
}


DOC_TYPES = {
    "html": b"text/html",
    "jpg":  b"image/jpeg",
    "jpeg": b"image/jpeg",
    "gif":  b"image/gif",
    "ico":  b"image/x-icon",
    "png":  b"image/png",
    "txt":  b"text/plain",
    "css":  b"text/css",
    "bin":  b"application/octet-stream",
    "js" :  b"text/javascript"
}


PATH_REWRITE = {
    "/": "/index.html"
}


def test(method, path, query, body):
    if query == None:
        query = ""
    if body:
        body_items = body.split("&")
        body = "\r\n".join(body_items)
    response = query + "_" + str(utime.ticks_ms()) + "\r\n"
    response += "Body:\r\n" + body
    response += "Free mem: " + str(gc.mem_free())
    return (200, {"Content-Type" : "text/plain"}, response)



def response_status(status_code):
    return HTTP_VERSION + " " + bytearray(str(status_code)) + b" " + HTTP_RESPONSE[status_code] + b"\r\n"


def error_page(status):
    return bytearray("<html><body><h1>{} {}</h1></body></html>".format(str(status), HTTP_RESPONSE[status].decode()))


def header_bytes(headers):
    h_bytes = b""
    for key, value in headers.items():
        h_bytes += bytearray(key) + b": " + bytearray(value)
    return h_bytes + b"\r\n"


def respond_to_request(method, uri, headers, body=None, handlers=None):
    path = None
    query = None
    uri_parts = uri.split("?")
    path = uri_parts[0]
    print("Path:", path)
    if path in PATH_REWRITE:
        path = PATH_REWRITE[path]
        print("Rewrite path:", path)
    path_parts = path.split(".")
    if len(uri_parts) > 1:
        uri_parts = uri_parts[1].split("#")
        query = uri_parts[0]
        print("Query:", query)
    if path in handlers:
        response = handlers[path](method, path, query, body)
        status = response[0]
        headers = response[1]
        content = response[2]
    else:
        if method in("GET", "HEAD"):
            if len(path_parts) > 1:
                extension = path_parts[-1]
            else:
                extension = None
            try:
                infile = open(path, "r")
                if method == "GET":
                    content = infile.read()
                else:
                    content = ""
                if extension in DOC_TYPES:
                    content_type = DOC_TYPES[extension]
                else:
                    content_type = b"text/plain"
                status = 200
            except OSError:
                status = 404
        else:
            status = 501
    if status != 200:
        content_type = b"text/html"
        content = error_page(status)
        headers = {"Content-Type: " : content_type}
    return response_status(status) + header_bytes(headers) + b"\r\n" + content


def trim(line):
    if len(line) > 1:
        line = line[:-2]
    return line


def process_http_request(client_stream, handlers):
    req = None
    try:
        req = client_stream.readline()
        req = trim(req)
        print("Request:")
        print(req)
    except OSError as error:
        print("Error receiving request:", error)
    if req:
        request = req.decode().split(" ")
        method = request[0].strip()
        uri = request[1].strip()
        print("Method:", method)
        print("URI:", uri)
        headers = {}
        print(req)
        while True:
            h = client_stream.readline()
            h = trim(h)
            if h == b"" or h == b"\r\n":
                break
            else:
                h_item = h.decode().split(":")
                h_key = h_item.pop(0).strip()
                h_value = ":".join(h_item).strip()
                headers[h_key] = h_value
            print(h)
        print("Headers:",headers)
        headers_lower = {h_key.lower():h_value for h_key, h_value in headers.items()}
        if "content-length" in headers_lower:
            content_length = int(headers_lower["content-length"])
            body = client_stream.read(content_length).decode()
        else:
            body = None
        print("Body:", body)
        response = respond_to_request(method, uri, headers, body=body, handlers=handlers)
        try:
            client_stream.write(response)
        except OSError as error:
            print("Error sending response:", error)
        print()


def start(micropython_optimize=True, port=PORT, handlers=None):
    s = socket.socket()

    # Binding to all interfaces - server will be accessible to other hosts!
    ai = socket.getaddrinfo(BIND_IP, port)
    print("Bind address info:", ai)
    addr = ai[0][-1]

    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(5)
    print("Listening, connect your browser to http://<this_host>:{}/".format(port))

    while True:
        res = s.accept()
        client_sock = res[0]
        client_addr = res[1]
        print("Client address:", client_addr)
        print("Client socket:", client_sock)

        if not micropython_optimize:
            # To read line-oriented protocol (like HTTP) from a socket (and
            # avoid short read problem), it must be wrapped in a stream (aka
            # file-like) object. That's how you do it in CPython:
            client_stream = client_sock.makefile("rwb")
        else:
            # .. but MicroPython socket objects support stream interface
            # directly, so calling .makefile() method is not required. If
            # you develop application which will run only on MicroPython,
            # especially on a resource-constrained embedded device, you
            # may take this shortcut to save resources.
            client_stream = client_sock
            process_http_request(client_stream, handlers)
            client_stream.close()
            if not micropython_optimize:
                client_sock.close()
