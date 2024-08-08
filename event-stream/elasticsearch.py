from datetime import datetime
from datetime import timezone
import json
import os, os.path
import socket
import sys
import urllib.request

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


def init_urllib():
    password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(
        None,
        ELASTICSEARCH_URL,
        ELASTICSEARCH_USERNAME,
        ELASTICSEARCH_PASSWORD,
    )
    auth_handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
    opener = urllib.request.build_opener(auth_handler)
    urllib.request.install_opener(opener)

def send_event(event):
    if 'timestamp' in event:
        timestamp_value = event['timestamp']
        # if timestamp is an integer or a float (any numeric type), convert to a iso8601 string so that elastic will index it as a date
        if isinstance(timestamp_value, (int, float)):
            utc_time = datetime.fromtimestamp(timestamp_value, tz=timezone.utc)
            event['timestamp'] = utc_time.isoformat()

    try:
        post_body = json.dumps(event).encode("utf-8")
        request = urllib.request.Request(ELASTICSEARCH_URL)
        request.add_header("Content-Type", "application/json")
        request.add_header("Content-Length", len(post_body))
        response = urllib.request.urlopen(request, post_body).read()
        print(response.decode("utf-8"))
    except Exception as e:
        print(f"ERROR: Failed to send event: {e}", file=sys.stderr)
        

with socket.create_server((HOST, PORT)) as sock:
    init_urllib()
    while True:
        client_sock, addr = sock.accept()
        with client_sock, client_sock.makefile() as fh:
                line = fh.readline()
                while line:
                    line = line.strip()
                    print(line)
                    
                    try:
                        request = json.loads(line)

                        if request["action"] == "add_event":
                            event = request["event"]
                            send_event(event)
                        else:
                            print(f"ERROR: Unknown action: {request['action']} - {line}", file=sys.stderr)
                            
                    except Exception as e:
                        print(f"ERROR: Invalid Request: {e} - {line}", file=sys.stderr)
                    line = fh.readline()

