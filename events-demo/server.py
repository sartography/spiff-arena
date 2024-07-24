import json
import os, os.path
import socket
import subprocess
import sys

HOST = os.environ.get('SPIFFWORKFLOW_EVENT_STREAM_HOST')
PORT = int(os.environ.get('SPIFFWORKFLOW_EVENT_STREAM_PORT'))

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
    try:
        res = None
        res = subprocess.run(CURL_TEMPLATE + [event], stdout=subprocess.PIPE).stdout()
        print(json.dumps(json.loads(res)))
    except:
        print(f"ERROR: Invalid Response: {event} - {res}", file=sys.stderr)


with socket.create_server((HOST, PORT)) as sock:
    while True:
        client_sock, addr = sock.accept()
        with client_sock:
            with client_sock.makefile() as fh:
                line = fh.readline()
                while line:
                    line = line.strip()
                    try:
                        print(line)
                        json.loads(line)
                        send_event(line)
                    except Exception as e:
                        print(f"ERROR: Invalid Request: {line} - {e}", file=sys.stderr)
                    line = fh.readline()

