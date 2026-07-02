#!/usr/bin/env python3
"""Stress the BPMN process-definition relationship race against a live backend.

Start Spiff first, then run from spiffworkflow-backend:

    uv run python bin/load_tests/process_definition_relationship_race.py

The script creates a temporary process model containing a call activity, then
fires concurrent cold process-instance creates at the existing backend. Vulnerable
code can return failures from duplicate `bpmn_process_definition_relationship`
inserts. Fixed code should create every process instance successfully.
"""

from __future__ import annotations

import argparse
import base64
import concurrent.futures
import json
import statistics
import time
import uuid
from dataclasses import dataclass
from typing import Any

import requests

DEFAULT_BACKEND_BASE_URL = "http://localhost:7000"
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin"  # noqa: S105 - local development default
DEFAULT_CLIENT_ID = "spiffworkflow-backend"
DEFAULT_CLIENT_SECRET = "JXeQExm0JhQPLumgHtIIqf52bDalHz0q"  # noqa: S105


PARENT_BPMN_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions
  xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
  xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
  id="Definitions_{parent_process_id}"
  targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="{parent_process_id}" name="Relationship Race Parent" isExecutable="true">
    <bpmn:startEvent id="StartEvent_parent">
      <bpmn:outgoing>Flow_start_to_call</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:sequenceFlow id="Flow_start_to_call" sourceRef="StartEvent_parent" targetRef="Activity_call_child" />
    <bpmn:callActivity id="Activity_call_child" name="Call child" calledElement="{child_process_id}">
      <bpmn:incoming>Flow_start_to_call</bpmn:incoming>
      <bpmn:outgoing>Flow_call_to_end</bpmn:outgoing>
    </bpmn:callActivity>
    <bpmn:endEvent id="EndEvent_parent">
      <bpmn:incoming>Flow_call_to_end</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow_call_to_end" sourceRef="Activity_call_child" targetRef="EndEvent_parent" />
  </bpmn:process>
  <bpmndi:BPMNDiagram id="BPMNDiagram_parent">
    <bpmndi:BPMNPlane id="BPMNPlane_parent" bpmnElement="{parent_process_id}">
      <bpmndi:BPMNShape id="StartEvent_parent_di" bpmnElement="StartEvent_parent">
        <dc:Bounds x="180" y="160" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Activity_call_child_di" bpmnElement="Activity_call_child">
        <dc:Bounds x="270" y="138" width="120" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="EndEvent_parent_di" bpmnElement="EndEvent_parent">
        <dc:Bounds x="450" y="160" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="Flow_start_to_call_di" bpmnElement="Flow_start_to_call">
        <di:waypoint x="216" y="178" />
        <di:waypoint x="270" y="178" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_call_to_end_di" bpmnElement="Flow_call_to_end">
        <di:waypoint x="390" y="178" />
        <di:waypoint x="450" y="178" />
      </bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>
"""


CHILD_BPMN_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions
  xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
  xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
  id="Definitions_{child_process_id}"
  targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="{child_process_id}" name="Relationship Race Child" isExecutable="true">
    <bpmn:startEvent id="StartEvent_child">
      <bpmn:outgoing>Flow_child_start_to_end</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:endEvent id="EndEvent_child">
      <bpmn:incoming>Flow_child_start_to_end</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow_child_start_to_end" sourceRef="StartEvent_child" targetRef="EndEvent_child" />
  </bpmn:process>
  <bpmndi:BPMNDiagram id="BPMNDiagram_child">
    <bpmndi:BPMNPlane id="BPMNPlane_child" bpmnElement="{child_process_id}">
      <bpmndi:BPMNShape id="StartEvent_child_di" bpmnElement="StartEvent_child">
        <dc:Bounds x="180" y="160" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="EndEvent_child_di" bpmnElement="EndEvent_child">
        <dc:Bounds x="360" y="160" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="Flow_child_start_to_end_di" bpmnElement="Flow_child_start_to_end">
        <di:waypoint x="216" y="178" />
        <di:waypoint x="360" y="178" />
      </bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>
"""


@dataclass
class CreateResult:
    index: int
    status_code: int
    elapsed_seconds: float
    process_instance_id: int | None
    error_code: str | None
    response_text: str

    @property
    def ok(self) -> bool:
        return self.status_code == 201 and self.process_instance_id is not None and self.error_code is None


def modified_identifier(identifier: str) -> str:
    return identifier.replace("/", ":")


def check_response(response: requests.Response, context: str, expected_statuses: set[int]) -> dict[str, Any]:
    try:
        data = response.json()
    except ValueError:
        data = {"raw_response": response.text}

    if response.status_code not in expected_statuses:
        raise RuntimeError(f"{context} failed with HTTP {response.status_code}: {json.dumps(data, indent=2)}")
    if isinstance(data, dict) and data.get("error_code"):
        raise RuntimeError(f"{context} failed: {json.dumps(data, indent=2)}")
    return data if isinstance(data, dict) else {"response": data}


def get_access_token(args: argparse.Namespace) -> str:
    if args.access_token:
        if not isinstance(args.access_token, str):
            raise RuntimeError("--access-token must be a string")
        return args.access_token

    token_url = args.openid_token_url or f"{args.backend_base_url}/openid/token"
    basic_auth = base64.b64encode(f"{args.client_id}:{args.client_secret}".encode("ascii")).decode("utf-8")
    response = requests.post(
        token_url,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {basic_auth}",
        },
        data={
            "grant_type": "password",
            "code": f"{args.username}:this_is_not_secure_do_not_use_in_production",
            "username": args.username,
            "password": args.password,
            "client_id": args.client_id,
        },
        timeout=args.timeout,
    )
    data = check_response(response, "token request", {200})
    token = data.get("access_token")
    if not isinstance(token, str) or not token:
        raise RuntimeError(f"token response did not include access_token: {json.dumps(data, indent=2)}")
    return token


def request_headers(args: argparse.Namespace, access_token: str | None = None) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if args.api_key:
        headers["Spiffworkflow-Api-Key"] = args.api_key
    elif access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    return headers


def login_with_access_token(session: requests.Session, args: argparse.Namespace, headers: dict[str, str]) -> None:
    response = session.post(
        f"{args.backend_base_url}/v1.0/login_with_access_token",
        headers=headers,
        params={"authentication_identifier": args.authentication_identifier},
        timeout=args.timeout,
    )
    check_response(response, "login_with_access_token", {200, 204, 302})


def create_process_group(session: requests.Session, args: argparse.Namespace, headers: dict[str, str], group_id: str) -> None:
    payload = {
        "id": group_id,
        "display_name": group_id,
        "description": "Temporary group for BPMN relationship race load testing",
        "display_order": 0,
        "admin": False,
    }
    response = session.post(f"{args.backend_base_url}/v1.0/process-groups", headers=headers, json=payload, timeout=args.timeout)
    if response.status_code == 400 and "already_exists" in response.text:
        return
    check_response(response, "create process group", {201})


def create_process_model(
    session: requests.Session,
    args: argparse.Namespace,
    headers: dict[str, str],
    group_id: str,
    process_model_id: str,
) -> None:
    payload = {
        "id": process_model_id,
        "display_name": process_model_id,
        "description": "Temporary model for BPMN relationship race load testing",
        "fault_or_suspend_on_exception": "fault",
        "exception_notification_addresses": [],
    }
    response = session.post(
        f"{args.backend_base_url}/v1.0/process-models/{modified_identifier(group_id)}",
        headers=headers,
        json=payload,
        timeout=args.timeout,
    )
    if response.status_code == 400 and "already_exists" in response.text:
        return
    check_response(response, "create process model", {201})


def upload_bpmn(
    session: requests.Session,
    args: argparse.Namespace,
    headers: dict[str, str],
    process_model_id: str,
    file_name: str,
    bpmn: str,
) -> None:
    upload_headers = {k: v for k, v in headers.items() if k.lower() != "content-type"}
    response = session.post(
        f"{args.backend_base_url}/v1.0/process-models/{modified_identifier(process_model_id)}/files",
        headers=upload_headers,
        files={"file": (file_name, bpmn.encode("utf-8"), "text/xml")},
        timeout=args.timeout,
    )
    check_response(response, f"upload {file_name}", {201})


def set_primary_bpmn(
    session: requests.Session,
    args: argparse.Namespace,
    headers: dict[str, str],
    process_model_id: str,
    file_name: str,
    process_id: str,
) -> None:
    response = session.put(
        f"{args.backend_base_url}/v1.0/process-models/{modified_identifier(process_model_id)}",
        headers=headers,
        json={
            "primary_file_name": file_name,
            "primary_process_id": process_id,
            "display_name": process_model_id,
            "description": "Temporary model for BPMN relationship race load testing",
            "fault_or_suspend_on_exception": "fault",
            "exception_notification_addresses": [],
        },
        timeout=args.timeout,
    )
    check_response(response, "set primary BPMN", {200})


def ensure_process_model(session: requests.Session, args: argparse.Namespace, headers: dict[str, str]) -> str:
    suffix = args.suffix or uuid.uuid4().hex
    group_id = args.group_id or f"load_test/process_definition_relationship_race_{suffix}"
    process_model_id = f"{group_id}/call_activity_parent"
    parent_process_id = f"Process_parent_{suffix}"
    child_process_id = f"Process_child_{suffix}"

    create_process_group(session, args, headers, "load_test")
    create_process_group(session, args, headers, group_id)
    create_process_model(session, args, headers, group_id, process_model_id)
    upload_bpmn(
        session,
        args,
        headers,
        process_model_id,
        "callable_child.bpmn",
        CHILD_BPMN_TEMPLATE.format(child_process_id=child_process_id),
    )
    upload_bpmn(
        session,
        args,
        headers,
        process_model_id,
        "call_activity_parent.bpmn",
        PARENT_BPMN_TEMPLATE.format(parent_process_id=parent_process_id, child_process_id=child_process_id),
    )
    set_primary_bpmn(session, args, headers, process_model_id, "call_activity_parent.bpmn", parent_process_id)
    return process_model_id


def create_process_instance(args: argparse.Namespace, headers: dict[str, str], process_model_id: str, index: int) -> CreateResult:
    start = time.perf_counter()
    try:
        response = requests.post(
            f"{args.backend_base_url}/v1.0/process-instances/{modified_identifier(process_model_id)}",
            headers=headers,
            timeout=args.timeout,
        )
        elapsed = time.perf_counter() - start
        try:
            data = response.json()
        except ValueError:
            data = {}
        return CreateResult(
            index=index,
            status_code=response.status_code,
            elapsed_seconds=elapsed,
            process_instance_id=data.get("id") if isinstance(data, dict) else None,
            error_code=data.get("error_code") if isinstance(data, dict) else None,
            response_text=response.text[:2000],
        )
    except Exception as exception:
        elapsed = time.perf_counter() - start
        return CreateResult(
            index=index,
            status_code=0,
            elapsed_seconds=elapsed,
            process_instance_id=None,
            error_code=exception.__class__.__name__,
            response_text=str(exception),
        )


def run_load(args: argparse.Namespace, headers: dict[str, str], process_model_id: str) -> list[CreateResult]:
    print(
        f"Creating {args.requests} process instances with {args.workers} workers against "
        f"{args.backend_base_url}/v1.0/process-instances/{modified_identifier(process_model_id)}"
    )
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(create_process_instance, args, headers, process_model_id, i) for i in range(args.requests)]
        return [future.result() for future in concurrent.futures.as_completed(futures)]


def print_summary(results: list[CreateResult]) -> None:
    successes = [result for result in results if result.ok]
    failures = [result for result in results if not result.ok]
    elapsed_values = [result.elapsed_seconds for result in results]

    print("\nBPMN Process Definition Relationship Race Summary")
    print(f"Total: {len(results)}")
    print(f"Successes: {len(successes)}")
    print(f"Failures: {len(failures)}")
    if elapsed_values:
        print(
            "Latency min/median/max: "
            f"{min(elapsed_values):.3f}s / {statistics.median(elapsed_values):.3f}s / {max(elapsed_values):.3f}s"
        )

    if failures:
        print("\nFailures:")
        for result in sorted(failures, key=lambda item: item.index)[:20]:
            print(
                f"- request={result.index} http={result.status_code} error={result.error_code} "
                f"body={result.response_text}"
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend-base-url", default=DEFAULT_BACKEND_BASE_URL)
    parser.add_argument("--requests", type=int, default=20)
    parser.add_argument("--workers", type=int, default=20)
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--username", default=DEFAULT_USERNAME)
    parser.add_argument("--password", default=DEFAULT_PASSWORD)
    parser.add_argument("--client-id", default=DEFAULT_CLIENT_ID)
    parser.add_argument("--client-secret", default=DEFAULT_CLIENT_SECRET)
    parser.add_argument("--openid-token-url")
    parser.add_argument("--authentication-identifier", default="default")
    parser.add_argument("--access-token")
    parser.add_argument("--api-key")
    parser.add_argument("--group-id", help="Use an existing or deterministic process group path")
    parser.add_argument("--suffix", help="Suffix for generated group/model/process identifiers")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    session = requests.Session()
    access_token = None if args.api_key else get_access_token(args)
    headers = request_headers(args, access_token)

    if access_token:
        login_with_access_token(session, args, headers)

    process_model_id = ensure_process_model(session, args, headers)
    results = run_load(args, headers, process_model_id)
    print_summary(results)
    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
