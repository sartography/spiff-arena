import base64
import json
import os, os.path
import socket
import urllib.parse, urllib.request

SOCK = "/tmp/event_stream.sock"

if os.path.exists(SOCK):
    os.remove(SOCK)

AUTH = base64.b64encode(f"elastic:{os.environ['ELASTIC_PASSWORD']}".encode('ascii'))
    
REQ = urllib.request.Request("http://localhost:9200/event-index/_doc",
    headers={
        "Authorization": f"Basic {AUTH}",
        "Content-type": "application/json",
    },
    method="POST")

T = {"specversion": "1.0", "type": "spiff", "id": "740fe40c-2c70-4643-bc42-1ae999a85948", "source": "spiffworkflow.org", "timestamp": 1721241492.540756, "data": {"message": "State change to COMPLETED", "userid": 1, "username": "admin@spiffworkflow.org", "process_instance_id": None, "process_model_identifier": "site-administration/onboarding", "workflow_spec": "Process_109on5e", "task_spec": "End", "task_id": "b949bea8-39ae-4ab7-8268-e14422617a97", "task_type": "SimpleBpmnTask"}}
data = urllib.parse.urlencode(T).encode()

res = urllib.request.urlopen(REQ, data=data).read()
print(res)

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
                event_data = json.loads(line.strip())
                print(line.strip())
                line = fh.readline()

print("socket closed")
