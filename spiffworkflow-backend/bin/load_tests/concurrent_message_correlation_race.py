#!/usr/bin/env python3
"""Reproduce the vacuous message-correlation match race against a running backend.

A receive message instance stores the whole workflow scope's correlations in
`correlation_keys`, which can include keys established by other messages (for
example a boundary event active alongside a receive task). Its
`correlation_rules`, however, only cover the message's own correlation
properties. Vulnerable matching code treats a correlation key that none of the
receiver's rules apply to as a full match, so any send with the right message
name can be delivered to an arbitrary waiting process instance (oldest first).
The engine then rejects the mismatched delivery and the error handler marks the
innocent receiving process instance as errored.

The generated process model gives every instance two correlation keys:

- ProcessUuidKey: identifies the instance; the assessment message correlates on it.
- AwaitedEventKey: established by the same scope (like a boundary event), but the
  assessment message has no correlation property for it.

Both keys are stored on the assessment receive message instance, while its rules
only reference ProcessUuidKey. A send whose process_uuid belongs to another
instance must not match. Vulnerable code matches it anyway via AwaitedEventKey,
errors an innocent process instance, and concurrent sends cross-deliver.

Start Spiff first, for example with `run-spiff-arena`, then run from
`spiffworkflow-backend`:

    uv run python bin/load_tests/concurrent_message_correlation_race.py

Message requests are always sent with `execution_mode=synchronous`, so the test
does not depend on a Celery worker draining queued message starts.

The script exits nonzero if any process instance errors, if a message is
delivered to the wrong process instance, or if any send fails to complete its
own intended process instance.
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
DEFAULT_CLIENT_ID = "spiffworkflow-backend"
DEFAULT_CLIENT_SECRET = "JXeQExm0JhQPLumgHtIIqf52bDalHz0q"  # noqa: S105 - local development default
SYNCHRONOUS_EXECUTION_MODE = "synchronous"

DEFAULT_INSTANCES = 4
READINESS_TIMEOUT_SECONDS = 15.0
COMPLETION_TIMEOUT_SECONDS = 15.0
PROBE_SETTLE_SECONDS = 1.0
SEND_RETRIES = 2
RETRY_DELAY_SECONDS = 1.0
POLL_INTERVAL_SECONDS = 0.25
HTTP_TIMEOUT_SECONDS = 30.0

FINAL_INSTANCE_STATUSES = {"complete", "error", "terminated"}


BPMN_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions
  xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
  xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
  xmlns:spiffworkflow="http://spiffworkflow.org/bpmn/schema/1.0/core"
  id="Definitions_{process_id}"
  targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:message id="Message_start" name="{start_message_name}" />
  <bpmn:message id="Message_assessment" name="{assessment_message_name}" />
  <bpmn:message id="Message_awaited" name="{awaited_message_name}" />
  <bpmn:correlationProperty id="process_uuid_property" name="process_uuid_property">
    <bpmn:correlationPropertyRetrievalExpression messageRef="Message_start">
      <bpmn:formalExpression>process_uuid</bpmn:formalExpression>
    </bpmn:correlationPropertyRetrievalExpression>
    <bpmn:correlationPropertyRetrievalExpression messageRef="Message_assessment">
      <bpmn:formalExpression>process_uuid</bpmn:formalExpression>
    </bpmn:correlationPropertyRetrievalExpression>
  </bpmn:correlationProperty>
  <bpmn:correlationProperty id="awaited_event_property" name="awaited_event_property">
    <bpmn:correlationPropertyRetrievalExpression messageRef="Message_start">
      <bpmn:formalExpression>awaited_event</bpmn:formalExpression>
    </bpmn:correlationPropertyRetrievalExpression>
    <bpmn:correlationPropertyRetrievalExpression messageRef="Message_awaited">
      <bpmn:formalExpression>awaited_event</bpmn:formalExpression>
    </bpmn:correlationPropertyRetrievalExpression>
  </bpmn:correlationProperty>
  <bpmn:collaboration id="Collaboration_{process_id}">
    <bpmn:participant id="Participant_{process_id}" processRef="{process_id}" />
    <bpmn:correlationKey id="CorrelationKey_process_uuid" name="ProcessUuidKey">
      <bpmn:correlationPropertyRef>process_uuid_property</bpmn:correlationPropertyRef>
    </bpmn:correlationKey>
    <bpmn:correlationKey id="CorrelationKey_awaited_event" name="AwaitedEventKey">
      <bpmn:correlationPropertyRef>awaited_event_property</bpmn:correlationPropertyRef>
    </bpmn:correlationKey>
  </bpmn:collaboration>
  <bpmn:process id="{process_id}" isExecutable="true">
    <bpmn:startEvent id="Start_event_{suffix}" name="Start">
      <bpmn:outgoing>Flow_start_to_receive</bpmn:outgoing>
      <bpmn:messageEventDefinition id="MessageEventDefinition_start" messageRef="Message_start" />
    </bpmn:startEvent>
    <bpmn:receiveTask id="Task_assessment_{suffix}" name="Wait for assessment" messageRef="Message_assessment"
      spiffworkflow:isMatchingCorrelation="true">
      <bpmn:incoming>Flow_start_to_receive</bpmn:incoming>
      <bpmn:outgoing>Flow_receive_to_end</bpmn:outgoing>
    </bpmn:receiveTask>
    <bpmn:boundaryEvent id="Boundary_awaited_{suffix}" name="Awaited event" attachedToRef="Task_assessment_{suffix}">
      <bpmn:messageEventDefinition id="MessageEventDefinition_boundary" messageRef="Message_awaited" />
      <bpmn:outgoing>Flow_boundary_to_end</bpmn:outgoing>
    </bpmn:boundaryEvent>
    <bpmn:endEvent id="End_done_{suffix}">
      <bpmn:incoming>Flow_receive_to_end</bpmn:incoming>
      <bpmn:incoming>Flow_boundary_to_end</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow_start_to_receive" sourceRef="Start_event_{suffix}" targetRef="Task_assessment_{suffix}" />
    <bpmn:sequenceFlow id="Flow_receive_to_end" sourceRef="Task_assessment_{suffix}" targetRef="End_done_{suffix}" />
    <bpmn:sequenceFlow id="Flow_boundary_to_end" sourceRef="Boundary_awaited_{suffix}" targetRef="End_done_{suffix}" />
  </bpmn:process>
  <bpmndi:BPMNDiagram id="BPMNDiagram_1">
    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Collaboration_{process_id}">
      <bpmndi:BPMNShape id="Participant_1_di" bpmnElement="Participant_{process_id}" isHorizontal="true">
        <dc:Bounds x="160" y="80" width="620" height="250" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Start_event_di" bpmnElement="Start_event_{suffix}">
        <dc:Bounds x="220" y="180" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Task_assessment_di" bpmnElement="Task_assessment_{suffix}">
        <dc:Bounds x="340" y="157" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Boundary_awaited_di" bpmnElement="Boundary_awaited_{suffix}">
        <dc:Bounds x="372" y="219" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="End_done_di" bpmnElement="End_done_{suffix}">
        <dc:Bounds x="540" y="180" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="Flow_start_to_receive_di" bpmnElement="Flow_start_to_receive">
        <di:waypoint x="256" y="198" />
        <di:waypoint x="340" y="197" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_receive_to_end_di" bpmnElement="Flow_receive_to_end">
        <di:waypoint x="440" y="197" />
        <di:waypoint x="540" y="198" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_boundary_to_end_di" bpmnElement="Flow_boundary_to_end">
        <di:waypoint x="390" y="255" />
        <di:waypoint x="558" y="255" />
        <di:waypoint x="558" y="216" />
      </bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>
"""


@dataclass
class SendResult:
    index: int
    process_uuid: str
    intended_process_instance_id: int
    status_code: int
    elapsed_seconds: float
    delivered_process_instance_id: int | None = None
    error_code: str | None = None
    response_text: str = ""

    @property
    def ok(self) -> bool:
        return self.status_code == 200 and self.delivered_process_instance_id == self.intended_process_instance_id


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

    basic_auth = base64.b64encode(f"{DEFAULT_CLIENT_ID}:{DEFAULT_CLIENT_SECRET}".encode("ascii")).decode("utf-8")
    response = requests.post(
        f"{args.backend_base_url}/openid/token",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {basic_auth}",
        },
        data={
            "grant_type": "password",
            "code": f"{DEFAULT_USERNAME}:this_is_not_secure_do_not_use_in_production",
            "username": DEFAULT_USERNAME,
            "password": DEFAULT_PASSWORD,
            "client_id": DEFAULT_CLIENT_ID,
        },
        timeout=HTTP_TIMEOUT_SECONDS,
    )
    data = check_response(response, "token request", {200})
    token = data.get("access_token")
    if not isinstance(token, str) or not token:
        raise RuntimeError(f"token response did not include access_token: {json.dumps(data, indent=2)}")
    return token


def request_headers(args: argparse.Namespace, access_token: str | None) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if args.api_key:
        headers["Spiffworkflow-Api-Key"] = args.api_key
    elif access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    return headers


def create_process_group(args: argparse.Namespace, headers: dict[str, str], group_id: str) -> None:
    payload = {
        "id": group_id,
        "display_name": group_id,
        "description": "Temporary group for message correlation race load testing",
        "display_order": 0,
        "admin": False,
    }
    response = requests.post(
        f"{args.backend_base_url}/v1.0/process-groups", headers=headers, json=payload, timeout=HTTP_TIMEOUT_SECONDS
    )
    if response.status_code == 400 and "already_exists" in response.text:
        return
    check_response(response, "create process group", {201})


def create_process_model(args: argparse.Namespace, headers: dict[str, str], group_id: str, process_model_id: str) -> None:
    payload = {
        "id": process_model_id,
        "display_name": process_model_id,
        "description": "Temporary model for message correlation race load testing",
        "fault_or_suspend_on_exception": "fault",
        "exception_notification_addresses": [],
    }
    response = requests.post(
        f"{args.backend_base_url}/v1.0/process-models/{modified_identifier(group_id)}",
        headers=headers,
        json=payload,
        timeout=HTTP_TIMEOUT_SECONDS,
    )
    if response.status_code == 400 and "already_exists" in response.text:
        return
    check_response(response, "create process model", {201})


def upload_bpmn(
    args: argparse.Namespace, headers: dict[str, str], process_model_id: str, file_name: str, bpmn: str
) -> None:
    upload_headers = {k: v for k, v in headers.items() if k.lower() != "content-type"}
    response = requests.post(
        f"{args.backend_base_url}/v1.0/process-models/{modified_identifier(process_model_id)}/files",
        headers=upload_headers,
        files={"file": (file_name, bpmn.encode("utf-8"), "text/xml")},
        timeout=HTTP_TIMEOUT_SECONDS,
    )
    if response.status_code == 400 and ("already exists" in response.text or "file_already_exists" in response.text):
        return
    check_response(response, "upload BPMN", {201})


def set_primary_bpmn(
    args: argparse.Namespace, headers: dict[str, str], process_model_id: str, file_name: str, process_id: str
) -> None:
    response = requests.put(
        f"{args.backend_base_url}/v1.0/process-models/{modified_identifier(process_model_id)}",
        headers=headers,
        json={
            "primary_file_name": file_name,
            "primary_process_id": process_id,
            "display_name": process_model_id,
            "description": "Temporary model for message correlation race load testing",
            "fault_or_suspend_on_exception": "fault",
            "exception_notification_addresses": [],
        },
        timeout=HTTP_TIMEOUT_SECONDS,
    )
    check_response(response, "set primary BPMN", {200})


@dataclass
class ModelNames:
    group_id: str
    process_id: str
    start_message_name: str
    assessment_message_name: str
    awaited_message_name: str


def ensure_process_model(args: argparse.Namespace, headers: dict[str, str]) -> ModelNames:
    suffix = str(int(time.time()))
    group_id = f"load_test/concurrent_message_correlation_race_{suffix}"
    process_model_id = f"{group_id}/message_receiver"
    process_id = f"Process_message_correlation_race_{suffix}".replace("-", "_")
    names = ModelNames(
        group_id=group_id,
        process_id=process_id,
        start_message_name=f"assessment_start_{suffix}",
        assessment_message_name=f"assessment_outcome_{suffix}",
        awaited_message_name=f"awaited_event_{suffix}",
    )
    file_name = "message_correlation_race_load_test.bpmn"

    create_process_group(args, headers, "load_test")
    create_process_group(args, headers, group_id)
    create_process_model(args, headers, group_id, process_model_id)
    upload_bpmn(
        args,
        headers,
        process_model_id,
        file_name,
        BPMN_TEMPLATE.format(
            process_id=process_id,
            suffix=suffix,
            start_message_name=names.start_message_name,
            assessment_message_name=names.assessment_message_name,
            awaited_message_name=names.awaited_message_name,
        ),
    )
    set_primary_bpmn(args, headers, process_model_id, file_name, process_id)

    return names


def post_message(
    args: argparse.Namespace,
    headers: dict[str, str],
    modified_message_name: str,
    payload: dict[str, Any],
) -> tuple[int, dict[str, Any], float]:
    start = time.perf_counter()
    try:
        response = requests.post(
            f"{args.backend_base_url}/v1.0/messages/{modified_message_name}",
            headers=headers,
            json=payload,
            params={"execution_mode": SYNCHRONOUS_EXECUTION_MODE},
            timeout=HTTP_TIMEOUT_SECONDS,
        )
    except Exception as exception:
        return 0, {"error_code": exception.__class__.__name__, "detail": str(exception)}, time.perf_counter() - start
    elapsed = time.perf_counter() - start
    try:
        data = response.json()
    except ValueError:
        data = {"raw_response": response.text}
    return response.status_code, data, elapsed


def start_one_instance(
    args: argparse.Namespace, headers: dict[str, str], modified_start_message_name: str, index: int
) -> tuple[int | None, str]:
    """Start one process instance via the message start. Returns (instance_id, error_detail)."""
    status_code, data, _elapsed = post_message(
        args,
        headers,
        modified_start_message_name,
        {"process_uuid": f"proc-{index}", "awaited_event": f"evt-{index}"},
    )
    process_instance = data.get("process_instance") if isinstance(data, dict) else None
    instance_id = process_instance.get("id") if isinstance(process_instance, dict) else None
    if status_code != 200 or instance_id is None:
        return None, json.dumps(data)[:500]
    return instance_id, ""


def fetch_message_instances(args: argparse.Namespace, headers: dict[str, str], instance_id: int) -> list[dict[str, Any]]:
    try:
        response = requests.get(
            f"{args.backend_base_url}/v1.0/messages",
            headers=headers,
            params={"process_instance_id": instance_id, "per_page": 100},
            timeout=HTTP_TIMEOUT_SECONDS,
        )
    except requests.RequestException:
        return []
    if response.status_code != 200:
        return []
    try:
        return response.json().get("results", [])  # type: ignore[no-any-return]
    except ValueError:
        return []


def wait_for_ready_receivers(
    args: argparse.Namespace, headers: dict[str, str], assessment_message_name: str, instance_ids: list[int]
) -> list[int]:
    """Poll until each instance has a ready receive message instance for the assessment message."""
    pending = set(instance_ids)
    deadline = time.monotonic() + args.readiness_timeout
    while pending and time.monotonic() < deadline:
        for instance_id in sorted(pending):
            has_ready_receiver = any(
                message.get("message_type") == "receive"
                and message.get("status") == "ready"
                and message.get("name") == assessment_message_name
                for message in fetch_message_instances(args, headers, instance_id)
            )
            if has_ready_receiver:
                pending.discard(instance_id)
        if pending:
            time.sleep(POLL_INTERVAL_SECONDS)
    return sorted(pending)


def discover_uuid_mapping(
    args: argparse.Namespace, headers: dict[str, str], assessment_message_name: str, instance_ids: list[int]
) -> tuple[dict[int, str], list[int]]:
    """Read each instance's expected ProcessUuidKey correlation from its ready assessment receiver.

    Returns the discovered instance id -> process_uuid mapping and the ids without a usable receiver.
    """
    mapping: dict[int, str] = {}
    unusable: list[int] = []
    for instance_id in instance_ids:
        assessment_receivers = [
            message
            for message in fetch_message_instances(args, headers, instance_id)
            if message.get("message_type") == "receive"
            and message.get("status") == "ready"
            and message.get("name") == assessment_message_name
        ]
        if len(assessment_receivers) != 1:
            unusable.append(instance_id)
            continue
        correlation_keys = assessment_receivers[0].get("correlation_keys") or {}
        process_uuid = (correlation_keys.get("ProcessUuidKey") or {}).get("process_uuid_property")
        if not isinstance(process_uuid, str):
            unusable.append(instance_id)
            continue
        mapping[instance_id] = process_uuid
    return mapping, unusable


def fetch_process_instance_status(args: argparse.Namespace, headers: dict[str, str], instance_id: int) -> str | None:
    try:
        response = requests.get(
            f"{args.backend_base_url}/v1.0/process-instances/find-by-id/{instance_id}",
            headers=headers,
            timeout=HTTP_TIMEOUT_SECONDS,
        )
    except requests.RequestException:
        return None
    if response.status_code != 200:
        return None
    try:
        return response.json().get("process_instance", {}).get("status")  # type: ignore[no-any-return]
    except ValueError:
        return None


def fetch_all_instance_statuses(
    args: argparse.Namespace, headers: dict[str, str], instance_ids: list[int]
) -> dict[int, str | None]:
    return {instance_id: fetch_process_instance_status(args, headers, instance_id) for instance_id in instance_ids}


def poll_instance_statuses(
    args: argparse.Namespace, headers: dict[str, str], instance_ids: list[int]
) -> dict[int, str | None]:
    statuses: dict[int, str | None] = dict.fromkeys(instance_ids)
    pending = set(instance_ids)
    deadline = time.monotonic() + args.completion_timeout
    while pending and time.monotonic() < deadline:
        for instance_id in sorted(pending):
            statuses[instance_id] = fetch_process_instance_status(args, headers, instance_id)
            if statuses[instance_id] in FINAL_INSTANCE_STATUSES:
                pending.discard(instance_id)
        if pending:
            time.sleep(POLL_INTERVAL_SECONDS)
    return statuses


def run_mismatch_probe(
    args: argparse.Namespace,
    headers: dict[str, str],
    modified_assessment_message_name: str,
    instance_ids: list[int],
) -> tuple[bool, list[str]]:
    """Send a message whose process_uuid matches no instance.

    Correct code must reject it without touching any waiting process instance.
    Vulnerable code claims the oldest receiver, the engine rejects the delivery,
    and the innocent receiving instance is marked as errored.
    """
    problems: list[str] = []
    status_code, data, _elapsed = post_message(
        args, headers, modified_assessment_message_name, {"process_uuid": "proc-no-such-instance"}
    )
    error_code = data.get("error_code") if isinstance(data, dict) else None
    detail = data.get("detail") if isinstance(data, dict) else ""

    if 200 <= status_code < 300:
        problems.append(f"mismatch probe unexpectedly succeeded with HTTP {status_code}: {json.dumps(data)[:500]}")
    elif status_code != 400:
        problems.append(f"mismatch probe returned unexpected HTTP {status_code}: {json.dumps(data)[:500]}")
    elif error_code == "workflow_error" and "not waiting for" in str(detail):
        problems.append(
            "mismatch probe hit the vacuous-match signature (engine rejected a delivery the API matcher accepted): "
            f"{detail}"
        )

    # Error marking happens synchronously with the rejected POST, so a short settle is enough.
    time.sleep(args.probe_settle_seconds)
    statuses = fetch_all_instance_statuses(args, headers, instance_ids)
    errored = {instance_id: status for instance_id, status in statuses.items() if status == "error"}
    if errored:
        problems.append(f"innocent process instances errored during mismatch probe: {sorted(errored)}")
    unreadable = {instance_id: status for instance_id, status in statuses.items() if status is None}
    if unreadable:
        print(f"Could not read statuses during mismatch probe (ignored): {sorted(unreadable)}")
    unexpected = {
        instance_id: status
        for instance_id, status in statuses.items()
        if status is not None and status not in {"waiting", "complete"}
    }
    if unexpected:
        problems.append(f"unexpected instance statuses after mismatch probe: {unexpected}")
    return not problems, problems


def send_with_retries(
    args: argparse.Namespace, headers: dict[str, str], modified_message_name: str, payload: dict[str, Any]
) -> tuple[int, dict[str, Any], float]:
    """Send a message, retrying briefly if the background scheduler holds the instance lock."""
    status_code, data, elapsed = post_message(args, headers, modified_message_name, payload)
    attempt = 1
    while (
        status_code == 400
        and isinstance(data, dict)
        and data.get("error_code") == "message_not_accepted"
        and attempt < args.send_retries
    ):
        attempt += 1
        time.sleep(args.retry_delay_seconds)
        status_code, data, elapsed = post_message(args, headers, modified_message_name, payload)
    return status_code, data, elapsed


def run_concurrent_delivery(
    args: argparse.Namespace,
    headers: dict[str, str],
    modified_assessment_message_name: str,
    instance_to_uuid: dict[int, str],
) -> tuple[list[SendResult], float]:
    """Fire one correctly-correlated send per instance, concurrently."""
    batch = sorted(
        (index, instance_id, process_uuid)
        for index, (instance_id, process_uuid) in enumerate(instance_to_uuid.items())
    )
    started_at = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(batch)) as executor:
        futures = {
            executor.submit(send_with_retries, args, headers, modified_assessment_message_name, {"process_uuid": uuid}): (
                index,
                intended_instance_id,
                uuid,
            )
            for (index, intended_instance_id, uuid) in batch
        }
        results = []
        for future in concurrent.futures.as_completed(futures):
            index, intended_instance_id, uuid = futures[future]
            status_code, data, elapsed = future.result()
            process_instance = data.get("process_instance") if isinstance(data, dict) else None
            results.append(
                SendResult(
                    index=index,
                    process_uuid=uuid,
                    intended_process_instance_id=intended_instance_id,
                    status_code=status_code,
                    elapsed_seconds=elapsed,
                    delivered_process_instance_id=(
                        process_instance.get("id") if isinstance(process_instance, dict) else None
                    ),
                    error_code=data.get("error_code") if isinstance(data, dict) else None,
                    response_text=json.dumps(data)[:500],
                )
            )
    batch_elapsed_seconds = time.perf_counter() - started_at
    results.sort(key=lambda result: result.index)
    return results, batch_elapsed_seconds


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def print_summary(results: list[SendResult], batch_elapsed_seconds: float, statuses: dict[int, str | None]) -> bool:
    successes = [result for result in results if result.ok]
    failures = [result for result in results if not result.ok]

    print("\nConcurrent Message Correlation Race Summary")
    print(f"Sends: {len(results)}")
    print(f"Delivered to the intended process instance: {len(successes)}")
    print(f"Failures: {len(failures)}")
    elapsed_values = [result.elapsed_seconds for result in results]
    if elapsed_values:
        print(
            "HTTP latency min/p50/p95/max: "
            f"{min(elapsed_values):.3f}s / {statistics.median(elapsed_values):.3f}s / "
            f"{percentile(elapsed_values, 0.95):.3f}s / {max(elapsed_values):.3f}s"
        )
        print(f"Concurrent request batch wall time: {batch_elapsed_seconds:.3f}s")

    errored = {instance_id: status for instance_id, status in statuses.items() if status == "error"}
    incomplete = {instance_id: status for instance_id, status in statuses.items() if status != "complete"}
    print(f"Process instances complete: {len(statuses) - len(incomplete)} / {len(statuses)}")
    if errored:
        print(f"Errored process instances: {sorted(errored)}")

    if failures:
        print("\nFailures:")
        for result in failures:
            print(
                f"- send={result.index} uuid={result.process_uuid} http={result.status_code} "
                f"intended_instance={result.intended_process_instance_id} "
                f"delivered_instance={result.delivered_process_instance_id} error={result.error_code} "
                f"body={result.response_text}"
            )

    return not failures and not errored and not incomplete


def print_readiness_diagnostics(
    args: argparse.Namespace, headers: dict[str, str], assessment_message_name: str, not_ready: list[int]
) -> None:
    print(
        f"\nProcess instances without a ready '{assessment_message_name}' receiver "
        f"after {args.readiness_timeout:.0f}s: {not_ready}"
    )
    statuses = fetch_all_instance_statuses(args, headers, not_ready)
    for instance_id in not_ready:
        print(f"- instance {instance_id}: status={statuses.get(instance_id)!r}")
        message_instances = fetch_message_instances(args, headers, instance_id)
        if not message_instances:
            print("  no message instances found for this process instance")
        for message in message_instances:
            print(
                f"  message {message.get('id')}: name={message.get('name')!r} "
                f"type={message.get('message_type')} status={message.get('status')}"
            )
    if statuses and all(statuses.get(instance_id) == "not_started" for instance_id in not_ready):
        print(
            "\nAll instances are still 'not_started': the backend queued them for background execution but "
            "nothing is draining the queue. If Celery or asynchronous execution is enabled, make sure a worker "
            "is running; otherwise check the backend logs for start failures."
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend-base-url", default=DEFAULT_BACKEND_BASE_URL)
    parser.add_argument(
        "--instances", type=int, default=DEFAULT_INSTANCES, help=f"Number of process instances (default {DEFAULT_INSTANCES})"
    )
    parser.add_argument("--api-key", help="Authenticate with a Spiffworkflow API key instead of the local admin user")
    parser.add_argument("--access-token", help="Authenticate with an OpenID access token instead of the local admin user")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.readiness_timeout = READINESS_TIMEOUT_SECONDS
    args.completion_timeout = COMPLETION_TIMEOUT_SECONDS
    args.probe_settle_seconds = PROBE_SETTLE_SECONDS
    args.send_retries = SEND_RETRIES
    args.retry_delay_seconds = RETRY_DELAY_SECONDS
    if args.instances < 1:
        raise SystemExit("--instances must be at least 1")

    session = requests.Session()
    access_token = None if args.api_key else get_access_token(args)
    headers = request_headers(args, access_token)

    if access_token:
        response = session.post(
            f"{args.backend_base_url}/v1.0/login_with_access_token",
            headers=headers,
            params={"authentication_identifier": "default"},
            timeout=HTTP_TIMEOUT_SECONDS,
        )
        check_response(response, "login_with_access_token", {200, 204, 302})

    names = ensure_process_model(args, headers)
    modified_start_message_name = f"{modified_identifier(names.group_id)}:{names.start_message_name}"
    modified_assessment_message_name = f"{modified_identifier(names.group_id)}:{names.assessment_message_name}"
    print(f"Starting {args.instances} instances against message '{modified_start_message_name}'...")

    # Starts are sent one at a time: each start is consumed by the new instance before the
    # next one begins. Firing starts concurrently is a separate pre-existing race (start
    # receivers match on name alone until their correlations exist) and would only muddy
    # the correlation race this script targets.
    start_results = [
        start_one_instance(args, headers, modified_start_message_name, index) for index in range(args.instances)
    ]

    failed_starts = [(index, detail) for index, (_instance_id, detail) in enumerate(start_results) if detail]
    if failed_starts:
        print("\nFailed to start process instances:")
        for index, detail in failed_starts:
            print(f"- start={index} uuid=proc-{index} detail={detail}")
        return 1

    instance_ids = [instance_id for instance_id, _detail in start_results if instance_id is not None]
    print(f"Started process instances: {instance_ids}")

    not_ready = wait_for_ready_receivers(args, headers, names.assessment_message_name, instance_ids)
    if not_ready:
        print_readiness_diagnostics(args, headers, names.assessment_message_name, not_ready)
        return 1

    # Derive the instance -> process_uuid mapping from each receiver's stored scope
    # correlations instead of trusting the start responses, so the delivery assertions
    # check the real invariant: a send must reach the instance whose scope holds its uuid.
    instance_to_uuid, unusable = discover_uuid_mapping(args, headers, names.assessment_message_name, instance_ids)
    if unusable:
        print(f"\nProcess instances without a usable assessment receiver correlation: {unusable}")
        return 1
    if len(set(instance_to_uuid.values())) != len(instance_to_uuid):
        print(f"\nDuplicate process_uuid correlations across receivers: {instance_to_uuid}")
        return 1
    print(f"Discovered correlations: {instance_to_uuid}")

    print(
        f"\nFiring {len(instance_to_uuid)} correctly-correlated sends against message '{modified_assessment_message_name}'..."
    )
    results, batch_elapsed_seconds = run_concurrent_delivery(
        args, headers, modified_assessment_message_name, instance_to_uuid
    )
    statuses = poll_instance_statuses(args, headers, instance_ids)
    all_ok = print_summary(results, batch_elapsed_seconds, statuses)

    if not all_ok:
        print(
            "\nFAILED: concurrent sends were delivered to the wrong process instances, errored innocent instances, "
            "or failed to complete every process instance."
        )
        return 1

    print("\nAll sends were delivered to their intended process instances and every instance completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
