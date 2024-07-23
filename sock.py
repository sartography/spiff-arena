import json
import os, os.path
import socket
import subprocess

HOST = os.environ.get('SPIFFWORKFLOW_BACKEND_EVENT_STREAM_HOST')
PORT = int(os.environ.get('SPIFFWORKFLOW_BACKEND_EVENT_STREAM_PORT'))

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


with socket.create_server((HOST, PORT)) as sock:
    while True:
        client_sock, addr = sock.accept()
        with client_sock:
            with client_sock.makefile() as fh:
                line = fh.readline()
                while line:
                    line = line.strio()
                    print(line)
                    send_event(line)
                    line = fh.readline()
        print("socket closed")

