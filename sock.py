import json
import os, os.path
import socket
import subprocess

SOCK = "/tmp/event_stream.sock"

if os.path.exists(SOCK):
    os.remove(SOCK)

AUTH = f"elastic:{os.environ['ELASTIC_PASSWORD']}"

CURL_TEMPLATE = [
    "curl",
    "-u",
    AUTH,
    "-s",
    "http://localhost:9200/my_index/_doc",
    "-XPOST",
    "-H",
    "Content-Type: application/json",
    "-d",
]

def send_event(event):
    res = subprocess.run(CURL_TEMPLATE + [event], stdout=subprocess.PIPE)
    print(json.dumps(json.loads(res.stdout)))

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
                send_event(line.strip())
                line = fh.readline()

print("socket closed")
