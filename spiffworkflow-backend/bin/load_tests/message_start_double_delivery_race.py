#!/usr/bin/env python3
"""Reproduce message-start double-delivery races against a live backend.

This targets the failure shape where POST /messages returns 200 for a message-start
process, then the just-started process instance is later marked error with:

    SpiffWorkflow.exceptions.WorkflowException: This process is not waiting for <message_name>

Start Spiff first, for example with `run-spiff-arena`, then run:

    uv run python bin/load_tests/message_start_double_delivery_race.py --requests 200 --workers 40
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
    <bpmn:startEvent id="Start_message" name="Check payment failed">
      <bpmn:outgoing>Flow_start_to_wait</bpmn:outgoing>
      <bpmn:messageEventDefinition id="MessageEventDefinition_start" messageRef="Message_start" />
    </bpmn:startEvent>
    <bpmn:manualTask id="Task_wait" name="Wait after message start">
      <bpmn:incoming>Flow_start_to_wait</bpmn:incoming>
      <bpmn:outgoing>Flow_wait_to_end</bpmn:outgoing>
    </bpmn:manualTask>
    <bpmn:endEvent id="Event_done">
      <bpmn:incoming>Flow_wait_to_end</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow_start_to_wait" sourceRef="Start_message" targetRef="Task_wait" />
    <bpmn:sequenceFlow id="Flow_wait_to_end" sourceRef="Task_wait" targetRef="Event_done" />
  </bpmn:process>
  <bpmn:message id="Message_start" name="{message_name}">
    <bpmn:extensionElements>
      <spiffworkflow:messageVariable>payload</spiffworkflow:messageVariable>
    </bpmn:extensionElements>
  </bpmn:message>
  <bpmndi:BPMNDiagram id="BPMNDiagram_1">
    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="{process_id}">
      <bpmndi:BPMNShape id="StartEvent_di" bpmnElement="Start_message">
        <dc:Bounds x="180" y="160" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="ManualTask_di" bpmnElement="Task_wait">
        <dc:Bounds x="300" y="138" width="120" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="EndEvent_di" bpmnElement="Event_done">
        <dc:Bounds x="510" y="160" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="Flow_start_to_wait_di" bpmnElement="Flow_start_to_wait">
        <di:waypoint x="216" y="178" />
        <di:waypoint x="300" y="178" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_wait_to_end_di" bpmnElement="Flow_wait_to_end">
        <di:waypoint x="420" y="178" />
        <di:waypoint x="510" y="178" />
      </bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>
"""


@dataclass
class MessageResult:
    index: int
    batch: int
    status_code: int
    elapsed_seconds: float
    process_instance_id: int | None
    process_instance_status: str | None
    error_code: str | None
    response_text: str

    @property
    def accepted(self) -> bool:
        return self.status_code == 200 and self.process_instance_id is not None and self.error_code is None


@dataclass
class ProcessInstanceStatusResult:
    process_instance_id: int
    status_code: int
    status: str | None
    error_code: str | None
    response_text: str

    @property
    def ok(self) -> bool:
        return self.status_code == 200 and self.status != "error" and self.error_code is None


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


def login_with_access_token(
    session: requests.Session,
    args: argparse.Namespace,
    headers: dict[str, str],
    access_token: str,
) -> None:
    params = {
        "authentication_identifier": args.authentication_identifier,
    }
    response = session.post(
        f"{args.backend_base_url}/v1.0/login_with_access_token",
        headers=headers,
        params=params,
        timeout=args.timeout,
    )

    if response.status_code == 400 and "access_token" in response.text:
        response = session.post(
            f"{args.backend_base_url}/v1.0/login_with_access_token",
            headers=headers,
            params={**params, "access_token": access_token},
            timeout=args.timeout,
        )

    check_response(response, "login_with_access_token", {200, 204, 302})


def create_process_group(session: requests.Session, args: argparse.Namespace, headers: dict[str, str], group_id: str) -> None:
    payload = {
        "id": group_id,
        "display_name": group_id,
        "description": "Temporary group for message-start double-delivery race testing",
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
        "description": "Temporary model for message-start double-delivery race testing",
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
            "description": "Temporary model for message-start double-delivery race testing",
            "fault_or_suspend_on_exception": "fault",
            "exception_notification_addresses": [],
        },
        timeout=args.timeout,
    )
    check_response(response, "set primary BPMN", {200})


def ensure_process_model(session: requests.Session, args: argparse.Namespace, headers: dict[str, str]) -> tuple[str, str, str]:
    suffix = args.suffix or str(int(time.time()))
    group_id = args.group_id or f"load_test/message_start_double_delivery_{suffix}"
    process_model_id = f"{group_id}/message_start_waiter"
    process_id = f"Process_message_start_double_delivery_{suffix}".replace("-", "_")
    message_name = args.message_name or f"check_payment_failed_v2_request_{suffix}"
    file_name = "message_start_double_delivery_race.bpmn"

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

    return group_id, process_model_id, message_name


def send_message(
    args: argparse.Namespace,
    headers: dict[str, str],
    modified_message_name: str,
    batch: int,
    index: int,
) -> MessageResult:
    payload = {"booking_id": args.booking_id}
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
            batch=batch,
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
            batch=batch,
            status_code=0,
            elapsed_seconds=elapsed,
            process_instance_id=None,
            process_instance_status=None,
            error_code=exception.__class__.__name__,
            response_text=str(exception),
        )


def fetch_process_instance_status(
    args: argparse.Namespace,
    headers: dict[str, str],
    process_model_id: str,
    process_instance_id: int,
) -> ProcessInstanceStatusResult:
    try:
        response = requests.get(
            f"{args.backend_base_url}/v1.0/process-instances/{modified_identifier(process_model_id)}/{process_instance_id}",
            headers=headers,
            timeout=args.timeout,
        )
        try:
            data = response.json()
        except ValueError:
            data = {}

        return ProcessInstanceStatusResult(
            process_instance_id=process_instance_id,
            status_code=response.status_code,
            status=data.get("status") if isinstance(data, dict) else None,
            error_code=data.get("error_code") if isinstance(data, dict) else None,
            response_text=response.text[:2000],
        )
    except Exception as exception:
        return ProcessInstanceStatusResult(
            process_instance_id=process_instance_id,
            status_code=0,
            status=None,
            error_code=exception.__class__.__name__,
            response_text=str(exception),
        )


def run_load(args: argparse.Namespace, headers: dict[str, str], group_id: str, message_name: str) -> list[MessageResult]:
    modified_message_name = f"{modified_identifier(group_id)}:{message_name}"
    print(
        f"Firing {args.batches} batch(es) of {args.requests} message starts with {args.workers} workers "
        f"against message '{modified_message_name}' using execution_mode={args.execution_mode} "
        f"and booking_id={args.booking_id}"
    )

    results: list[MessageResult] = []
    for batch in range(args.batches):
        if batch > 0 and args.batch_delay_seconds > 0:
            time.sleep(args.batch_delay_seconds)
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = [
                executor.submit(send_message, args, headers, modified_message_name, batch, index)
                for index in range(args.requests)
            ]
            results.extend(future.result() for future in concurrent.futures.as_completed(futures))
    return results


def fetch_final_statuses(
    args: argparse.Namespace,
    headers: dict[str, str],
    process_model_id: str,
    results: list[MessageResult],
) -> list[ProcessInstanceStatusResult]:
    process_instance_ids = sorted({result.process_instance_id for result in results if result.process_instance_id is not None})
    if not process_instance_ids:
        return []

    if args.settle_seconds > 0:
        print(f"Waiting {args.settle_seconds:.1f}s before re-fetching process instances")
        time.sleep(args.settle_seconds)

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(args.workers, len(process_instance_ids))) as executor:
        futures = [
            executor.submit(fetch_process_instance_status, args, headers, process_model_id, process_instance_id)
            for process_instance_id in process_instance_ids
        ]
        return [future.result() for future in concurrent.futures.as_completed(futures)]


def print_summary(results: list[MessageResult], final_statuses: list[ProcessInstanceStatusResult]) -> None:
    accepted = [r for r in results if r.accepted]
    rejected = [r for r in results if not r.accepted]
    elapsed_values = [r.elapsed_seconds for r in results]
    process_instance_ids = [r.process_instance_id for r in accepted if r.process_instance_id is not None]
    final_status_counts: dict[str, int] = {}
    for status_result in final_statuses:
        status_key = status_result.status or f"http_{status_result.status_code}"
        final_status_counts[status_key] = final_status_counts.get(status_key, 0) + 1

    print("\nMessage Start Double-Delivery Race Summary")
    print(f"Total POSTs: {len(results)}")
    print(f"Accepted POSTs: {len(accepted)}")
    print(f"Rejected POSTs: {len(rejected)}")
    print(f"Unique returned process instances: {len(set(process_instance_ids))}")
    if elapsed_values:
        print(
            "POST latency min/median/max: "
            f"{min(elapsed_values):.3f}s / {statistics.median(elapsed_values):.3f}s / {max(elapsed_values):.3f}s"
        )
    if final_status_counts:
        print(f"Final process-instance statuses: {final_status_counts}")

    errored_after_accept = [s for s in final_statuses if s.status == "error"]
    bad_final_fetches = [s for s in final_statuses if not s.ok and s.status != "error"]

    if rejected:
        print("\nRejected or failed POSTs:")
        for result in sorted(rejected, key=lambda r: (r.batch, r.index))[:20]:
            print(
                f"- batch={result.batch} request={result.index} http={result.status_code} "
                f"status={result.process_instance_status} error={result.error_code} body={result.response_text}"
            )

    if errored_after_accept:
        print("\nProcess instances that were accepted and later became error:")
        for status_result in sorted(errored_after_accept, key=lambda r: r.process_instance_id)[:20]:
            print(f"- {status_result.process_instance_id}")

    if bad_final_fetches:
        print("\nProcess instances that could not be re-fetched cleanly:")
        for status_result in sorted(bad_final_fetches, key=lambda r: r.process_instance_id)[:20]:
            print(
                f"- process_instance={status_result.process_instance_id} http={status_result.status_code} "
                f"status={status_result.status} error={status_result.error_code} body={status_result.response_text}"
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend-base-url", default=DEFAULT_BACKEND_BASE_URL)
    parser.add_argument("--requests", type=int, default=200, help="Number of message POSTs per batch")
    parser.add_argument("--workers", type=int, default=40)
    parser.add_argument("--batches", type=int, default=1)
    parser.add_argument("--batch-delay-seconds", type=float, default=0)
    parser.add_argument("--settle-seconds", type=float, default=12)
    parser.add_argument("--booking-id", type=int, default=786556518)
    parser.add_argument("--execution-mode", default="asynchronous", choices=["synchronous", "asynchronous"])
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
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    session = requests.Session()
    access_token = None if args.api_key else get_access_token(args)
    headers = request_headers(args, access_token)

    if access_token:
        login_with_access_token(session, args, headers, access_token)

    group_id, process_model_id, message_name = ensure_process_model(session, args, headers)
    results = run_load(args, headers, group_id, message_name)
    final_statuses = fetch_final_statuses(args, headers, process_model_id, results)
    print_summary(results, final_statuses)

    accepted_ok = all(result.accepted for result in results)
    final_statuses_ok = all(status_result.ok for status_result in final_statuses)
    return 0 if accepted_ok and final_statuses_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
