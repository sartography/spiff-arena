import base64
import json
import os, os.path
import socket
import urllib.request

SOCK = "/tmp/event_stream.sock"

if os.path.exists(SOCK):
    os.remove(SOCK)

AUTH = base64.b64encode(f"elastic:{os.environ['ELASTIC_PASSWORD']}".encode('ascii'))
    
REQ = urllib.request.Request("http://localhost:9200/event-index/_doc",
    headers={
        "Authorization": f"Basic {AUTH}",
        "Content-type": "application/json",
    })

exit(0)
    
server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
server.bind(SOCK)

while True:
    server.listen(1)
    client_sock, addr = server.accept()
    with client_sock:
        with client_sock.makefile() as fh:
            line = fh.readline()
            while line:
                print(line.strip())
                line = fh.readline()

print("socket closed")
