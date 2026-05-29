#!/usr/bin/env python3
"""Create a temporary message-start process and fire concurrent message starts.

This is intended as a live-server regression harness for message-start races.
Start Spiff first, for example with `run-spiff-arena`, then run:

    uv run python bin/load_tests/concurrent_message_starts.py --requests 50 --workers 20
"""

from __future__ import annotations

import argparse
import base64
import concurrent.futures
import json
import statistics
import time
from dataclasses import dataclass
from typing import Any

import requests

DEFAULT_BACKEND_BASE_URL = "http://localhost:7000"
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin"  # noqa: S105 - local development default
DEFAULT_REALM = "spiffworkflow"
DEFAULT_CLIENT_ID = "spiffworkflow-backend"
DEFAULT_CLIENT_SECRET = "JXeQExm0JhQPLumgHtIIqf52bDalHz0q"  # noqa: S105


BPMN_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions
  xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
  xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
  xmlns:spiffworkflow="http://spiffworkflow.org/bpmn/schema/1.0/core"
  id="Definitions_{process_id}"
  targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="{process_id}" isExecutable="true">
    <bpmn:startEvent id="message_start_event" name="Concurrent message start">
      <bpmn:outgoing>Flow_start_to_end</bpmn:outgoing>
      <bpmn:messageEventDefinition id="MessageEventDefinition_start" messageRef="Message_start" />
    </bpmn:startEvent>
    <bpmn:sequenceFlow id="Flow_start_to_end" sourceRef="message_start_event" targetRef="Event_done" />
    <bpmn:endEvent id="Event_done">
      <bpmn:incoming>Flow_start_to_end</bpmn:incoming>
    </bpmn:endEvent>
  </bpmn:process>
  <bpmn:message id="Message_start" name="{message_name}">
    <bpmn:extensionElements>
      <spiffworkflow:messageVariable>payload</spiffworkflow:messageVariable>
    </bpmn:extensionElements>
  </bpmn:message>
  <bpmndi:BPMNDiagram id="BPMNDiagram_1">
    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="{process_id}">
      <bpmndi:BPMNShape id="StartEvent_di" bpmnElement="message_start_event">
        <dc:Bounds x="180" y="160" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="EndEvent_di" bpmnElement="Event_done">
        <dc:Bounds x="390" y="160" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="Flow_start_to_end_di" bpmnElement="Flow_start_to_end">
        <di:waypoint x="216" y="178" />
        <di:waypoint x="390" y="178" />
      </bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>
"""


@dataclass
class MessageResult:
    index: int
    status_code: int
    elapsed_seconds: float
    process_instance_id: int | None
    process_instance_status: str | None
    error_code: str | None
    response_text: str

    @property
    def ok(self) -> bool:
        return (
            self.status_code == 200
            and self.process_instance_id is not None
            and self.process_instance_status == "complete"
            and self.error_code is None
        )


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


def create_process_group(session: requests.Session, args: argparse.Namespace, headers: dict[str, str], group_id: str) -> None:
    payload = {
        "id": group_id,
        "display_name": group_id,
        "description": "Temporary group for concurrent message-start load testing",
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
        "description": "Temporary model for concurrent message-start load testing",
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
    if response.status_code == 400 and ("already exists" in response.text or "file_already_exists" in response.text):
        return
    check_response(response, "upload BPMN", {201})


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
            "description": "Temporary model for concurrent message-start load testing",
            "fault_or_suspend_on_exception": "fault",
            "exception_notification_addresses": [],
        },
        timeout=args.timeout,
    )
    check_response(response, "set primary BPMN", {200})


def ensure_process_model(session: requests.Session, args: argparse.Namespace, headers: dict[str, str]) -> tuple[str, str]:
    suffix = args.suffix or str(int(time.time()))
    group_id = args.group_id or f"load_test/concurrent_message_starts_{suffix}"
    process_model_id = f"{group_id}/message_receiver"
    process_id = f"Process_concurrent_message_starts_{suffix}".replace("-", "_")
    message_name = args.message_name or f"concurrent_message_start_{suffix}"
    file_name = "message_start_load_test.bpmn"

    create_process_group(session, args, headers, "load_test")
    create_process_group(session, args, headers, group_id)
    create_process_model(session, args, headers, group_id, process_model_id)
    upload_bpmn(
        session,
        args,
        headers,
        process_model_id,
        file_name,
        BPMN_TEMPLATE.format(process_id=process_id, message_name=message_name),
    )
    set_primary_bpmn(session, args, headers, process_model_id, file_name, process_id)

    return group_id, message_name


def send_message(args: argparse.Namespace, headers: dict[str, str], modified_message_name: str, index: int) -> MessageResult:
    payload = {
        "request_index": index,
        "sent_at": time.time(),
        "payload": {"email": f"load-test-{index}@example.com"},
    }
    start = time.perf_counter()
    try:
        response = requests.post(
            f"{args.backend_base_url}/v1.0/messages/{modified_message_name}",
            headers=headers,
            json=payload,
            params={"execution_mode": args.execution_mode},
            timeout=args.timeout,
        )
        elapsed = time.perf_counter() - start
        try:
            data = response.json()
        except ValueError:
            data = {}

        process_instance = data.get("process_instance") if isinstance(data, dict) else None
        return MessageResult(
            index=index,
            status_code=response.status_code,
            elapsed_seconds=elapsed,
            process_instance_id=process_instance.get("id") if isinstance(process_instance, dict) else None,
            process_instance_status=process_instance.get("status") if isinstance(process_instance, dict) else None,
            error_code=data.get("error_code") if isinstance(data, dict) else None,
            response_text=response.text[:2000],
        )
    except Exception as exception:
        elapsed = time.perf_counter() - start
        return MessageResult(
            index=index,
            status_code=0,
            elapsed_seconds=elapsed,
            process_instance_id=None,
            process_instance_status=None,
            error_code=exception.__class__.__name__,
            response_text=str(exception),
        )


def run_load(args: argparse.Namespace, headers: dict[str, str], group_id: str, message_name: str) -> list[MessageResult]:
    modified_message_name = f"{modified_identifier(group_id)}:{message_name}"
    if args.warm_up:
        print(f"Warming up message '{modified_message_name}' before the concurrent phase")
        warm_up_result = send_message(args, headers, modified_message_name, -1)
        if not warm_up_result.ok:
            raise RuntimeError(f"warm-up message failed: {warm_up_result.response_text}")

    print(
        f"Firing {args.requests} message starts with {args.workers} workers against message '{modified_message_name}' "
        f"using execution_mode={args.execution_mode}"
    )
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(send_message, args, headers, modified_message_name, i) for i in range(args.requests)]
        return [future.result() for future in concurrent.futures.as_completed(futures)]


def print_summary(results: list[MessageResult]) -> None:
    successes = [r for r in results if r.ok]
    failures = [r for r in results if not r.ok]
    elapsed_values = [r.elapsed_seconds for r in results]

    print("\nConcurrent Message Start Summary")
    print(f"Total: {len(results)}")
    print(f"Successes: {len(successes)}")
    print(f"Failures: {len(failures)}")
    if elapsed_values:
        print(
            "Latency min/median/max: "
            f"{min(elapsed_values):.3f}s / {statistics.median(elapsed_values):.3f}s / {max(elapsed_values):.3f}s"
        )

    process_instance_ids = [r.process_instance_id for r in successes if r.process_instance_id is not None]
    print(f"Unique successful process instances: {len(set(process_instance_ids))}")

    if failures:
        print("\nFailures:")
        for result in sorted(failures, key=lambda r: r.index)[:20]:
            print(
                f"- request={result.index} http={result.status_code} status={result.process_instance_status} "
                f"error={result.error_code} body={result.response_text}"
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend-base-url", default=DEFAULT_BACKEND_BASE_URL)
    parser.add_argument("--requests", type=int, default=50)
    parser.add_argument("--workers", type=int, default=20)
    parser.add_argument("--execution-mode", default="synchronous", choices=["synchronous", "asynchronous"])
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--username", default=DEFAULT_USERNAME)
    parser.add_argument("--password", default=DEFAULT_PASSWORD)
    parser.add_argument("--realm", default=DEFAULT_REALM)
    parser.add_argument("--client-id", default=DEFAULT_CLIENT_ID)
    parser.add_argument("--client-secret", default=DEFAULT_CLIENT_SECRET)
    parser.add_argument("--openid-token-url")
    parser.add_argument("--authentication-identifier", default="default")
    parser.add_argument("--access-token")
    parser.add_argument("--api-key")
    parser.add_argument("--group-id", help="Use an existing or deterministic process group path")
    parser.add_argument("--message-name", help="Use an existing or deterministic message name")
    parser.add_argument("--suffix", help="Suffix for generated group/model/message identifiers")
    parser.add_argument(
        "--no-warm-up",
        action="store_false",
        dest="warm_up",
        help="Skip the single warm-up message and include cold BPMN definition persistence in the stress test",
    )
    parser.set_defaults(warm_up=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    session = requests.Session()
    access_token = None if args.api_key else get_access_token(args)
    headers = request_headers(args, access_token)

    if access_token:
        response = session.post(
            f"{args.backend_base_url}/v1.0/login_with_access_token",
            headers=headers,
            params={
                "authentication_identifier": args.authentication_identifier,
            },
            timeout=args.timeout,
        )
        check_response(response, "login_with_access_token", {200, 204, 302})

    group_id, message_name = ensure_process_model(session, args, headers)
    results = run_load(args, headers, group_id, message_name)
    print_summary(results)
    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
