import json
import os, os.path
import socket
import subprocess
import sys

HOST = os.environ["SPIFFWORKFLOW_EVENT_STREAM_HOST"]
PORT = int(os.environ["SPIFFWORKFLOW_EVENT_STREAM_PORT"])

ELASTICSEARCH_HOST = os.environ["SPIFFWORKFLOW_EVENT_STREAM_ELASTICSEARCH_HOST"]
ELASTICSEARCH_PORT = int(os.environ["SPIFFWORKFLOW_EVENT_STREAM_ELASTICSEARCH_PORT"])

ELASTICSEARCH_USERNAME = os.environ["SPIFFWORKFLOW_EVENT_STREAM_ELASTICSEARCH_USERNAME"]
ELASTICSEARCH_PASSWORD = os.environ["SPIFFWORKFLOW_EVENT_STREAM_ELASTICSEARCH_PASSWORD"]

ELASTICSEARCH_INDEX = os.environ.get(
    "SPIFFWORKFLOW_EVENT_STREAM_ELASTICSEARCH_INDEX",
    "spiffworkflow_event_stream"
)

ELASTICSEARCH_USE_HTTPS = os.environ.get(
    "SPIFFWORKFLOW_EVENT_STREAM_ELASTICSEARCH_USE_HTTPS",
    "true"
) != "false"

ELASTICSEARCH_PROTOCOL = "https" if ELASTICSEARCH_USE_HTTPS else "http"
ELASTICSEARCH_URL = f"{ELASTICSEARCH_PROTOCOL}://" \
    f"{ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}/" \
    f"{ELASTICSEARCH_INDEX}/_doc"

CURL_TEMPLATE = [
    "curl",
    "-u",
    f"{ELASTICSEARCH_USERNAME}:{ELASTICSEARCH_PASSWORD}",
    "-s",
    ELASTICSEARCH_URL,
    "-XPOST",
    "-H",
    "Content-Type: application/json",
    "-d",
]

def send_event(event):
    try:
        res = subprocess.run(CURL_TEMPLATE + [event], stdout=subprocess.PIPE)
        print(json.dumps(json.loads(res.stdout)))
    except Exception as e:
        print(f"ERROR: Invalid Response: {e} - {res}", file=sys.stderr)


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
                        print(f"ERROR: Invalid Request: {e} - {line}", file=sys.stderr)
                    line = fh.readline()

