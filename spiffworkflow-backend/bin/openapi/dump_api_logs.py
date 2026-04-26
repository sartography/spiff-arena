#!/usr/bin/env python3
"""
Script to dump API logs from the database into structured files for AI processing
to improve OpenAPI spec generation.

Usage:
    uv run dump_api_logs.py [--output-dir logs_dump] [--limit N] [--chunk-size N]
"""

import argparse
import hashlib
import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from typing import Any

import mysql.connector


def connect_to_db():
    """Connect to the MySQL database using environment variables."""
    db_host = os.environ.get("DB_HOST", "localhost")
    db_user = os.environ.get("DB_USER", "root")
    db_name = os.environ.get("DB_NAME", "spiffworkflow_backend_local_development")
    db_password = os.environ.get("DB_PASSWORD", "")

    try:
        connection = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name,
            autocommit=True,
            use_unicode=True,
            charset="utf8mb4",
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error connecting to database: {err}")
        print("Suggestions:")
        print("- Make sure MySQL is running")
        print(f"- Verify database exists: {db_name}")
        print("- Check MySQL server sort_buffer_size if you get memory errors")
        print("- Ensure DB_PASSWORD, DB_HOST, DB_USER, DB_NAME environment variables are set correctly")
        sys.exit(1)


def normalize_endpoint(endpoint: str) -> str:
    """
    Normalize endpoint by replacing dynamic path parameters with placeholders.
    This helps group similar endpoints together.
    """
    import re

    # Replace UUIDs with {id}
    endpoint = re.sub(r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "/{id}", endpoint)

    # Replace numeric IDs with {id}
    endpoint = re.sub(r"/\d+(?=/|$)", "/{id}", endpoint)

    # Replace other common patterns
    endpoint = re.sub(r"/[^/]+\.(png|jpg|jpeg|gif|svg|css|js)(?:\?.*)?$", "/{file}", endpoint)

    return endpoint


def get_unique_request_signature(method: str, endpoint: str, query_params: Any) -> str:
    """Generate a unique signature for a request type."""
    normalized_endpoint = normalize_endpoint(endpoint)

    # Parse query_params if it's a string
    if isinstance(query_params, str):
        try:
            query_params = json.loads(query_params) if query_params else {}
        except json.JSONDecodeError:
            query_params = {}
    elif query_params is None:
        query_params = {}

    # Create a signature based on method, normalized endpoint, and query param keys
    query_keys = sorted(query_params.keys()) if query_params else []
    signature_data = {"method": method, "endpoint": normalized_endpoint, "query_param_keys": query_keys}

    signature_str = json.dumps(signature_data, sort_keys=True)
    return hashlib.sha256(signature_str.encode()).hexdigest()[:8]


def sanitize_json_data(data: Any) -> Any:
    """
    Sanitize JSON data by removing or masking sensitive information.
    """
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            if key.lower() in ["password", "token", "secret", "key", "auth", "authorization"]:
                sanitized[key] = "[REDACTED]"
            elif key.lower().endswith("_token") or key.lower().endswith("_key"):
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = sanitize_json_data(value)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_json_data(item) for item in data]
    else:
        return data


def fetch_api_logs(connection, limit: int = None, chunk_size: int = 1000) -> list[dict]:
    """Fetch API logs from the database in chunks to avoid memory issues."""
    cursor = connection.cursor(dictionary=True)
    all_results = []

    # Get total count first
    count_query = "SELECT COUNT(*) as total FROM api_log"
    cursor.execute(count_query)
    total_count = cursor.fetchone()["total"]

    if limit and limit < total_count:
        total_count = limit

    print(f"Total records to process: {total_count}")

    # Fetch data in chunks without ORDER BY to avoid sort buffer issues
    offset = 0
    while offset < total_count:
        current_limit = min(chunk_size, total_count - offset)

        query = """
            SELECT id, created_at, method, endpoint, request_body, response_body,
                   status_code, process_instance_id, duration_ms, query_params
            FROM api_log
            LIMIT %s OFFSET %s
        """

        try:
            cursor.execute(query, (current_limit, offset))
            chunk_results = cursor.fetchall()

            if not chunk_results:
                break

            all_results.extend(chunk_results)
            offset += chunk_size

            print(f"Processed {len(all_results)}/{total_count} records...")

        except mysql.connector.Error as err:
            print(f"Error fetching chunk at offset {offset}: {err}")
            if "sort buffer" in str(err).lower():
                print("Try reducing --chunk-size to a smaller value (e.g., --chunk-size 500)")
            break

    cursor.close()
    return all_results


def group_logs_by_request_type(logs: list[dict]) -> dict[str, list[dict]]:
    """Group logs by unique request type signature."""
    grouped = defaultdict(list)

    for log in logs:
        method = log["method"]
        endpoint = log["endpoint"]
        query_params = log["query_params"]

        signature = get_unique_request_signature(method, endpoint, query_params)

        # Add normalized endpoint for reference
        log["normalized_endpoint"] = normalize_endpoint(endpoint)
        log["signature"] = signature

        # Parse JSON fields if they're strings
        for field in ["query_params", "request_body", "response_body"]:
            if isinstance(log[field], str) and log[field]:
                try:
                    log[field] = json.loads(log[field])
                except json.JSONDecodeError:
                    log[field] = log[field]  # Keep as string if not valid JSON
            elif log[field] is None:
                log[field] = {}

        # Sanitize sensitive data
        if log["request_body"]:
            log["request_body"] = sanitize_json_data(log["request_body"])
        if log["response_body"]:
            log["response_body"] = sanitize_json_data(log["response_body"])

        grouped[signature].append(log)

    return dict(grouped)


def write_summary_file(output_dir: str, grouped_logs: dict[str, list[dict]]):
    """Write a summary file with all unique request types."""
    summary = {"generated_at": datetime.now().isoformat(), "total_unique_request_types": len(grouped_logs), "request_types": []}

    for signature, logs in grouped_logs.items():
        first_log = logs[0]
        request_type = {
            "signature": signature,
            "method": first_log["method"],
            "original_endpoint": first_log["endpoint"],
            "normalized_endpoint": first_log["normalized_endpoint"],
            "total_requests": len(logs),
            "status_codes": list({log["status_code"] for log in logs}),
            "has_request_body": any(log["request_body"] for log in logs),
            "has_response_body": any(log["response_body"] for log in logs),
            "sample_query_params": first_log["query_params"],
            "file_name": f"{signature}.json",
        }
        summary["request_types"].append(request_type)

    # Sort by method and endpoint for easier reading
    summary["request_types"].sort(key=lambda x: (x["method"], x["normalized_endpoint"]))

    with open(os.path.join(output_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"Summary written to {os.path.join(output_dir, 'summary.json')}")


def write_individual_files(output_dir: str, grouped_logs: dict[str, list[dict]]):
    """Write individual files for each unique request type."""
    for signature, logs in grouped_logs.items():
        first_log = logs[0]

        # Create structured data for this request type
        request_type_data = {
            "signature": signature,
            "method": first_log["method"],
            "original_endpoint": first_log["endpoint"],
            "normalized_endpoint": first_log["normalized_endpoint"],
            "total_examples": len(logs),
            "status_codes": list({log["status_code"] for log in logs}),
            "examples": [],
        }

        # Add examples (limit to avoid huge files)
        max_examples = min(50, len(logs))  # Limit to 50 examples per request type

        for log in logs[:max_examples]:
            example = {
                "id": log["id"],
                "timestamp": log["created_at"].isoformat() if log["created_at"] else None,
                "status_code": log["status_code"],
                "duration_ms": log["duration_ms"],
                "process_instance_id": log["process_instance_id"],
                "query_params": log["query_params"],
                "request_body": log["request_body"],
                "response_body": log["response_body"],
            }
            request_type_data["examples"].append(example)

        # Create schemas from the examples for OpenAPI generation
        request_type_data["inferred_schemas"] = {
            "request_body_examples": [ex["request_body"] for ex in request_type_data["examples"] if ex["request_body"]],
            "response_body_examples": [ex["response_body"] for ex in request_type_data["examples"] if ex["response_body"]],
            "query_param_examples": [ex["query_params"] for ex in request_type_data["examples"] if ex["query_params"]],
        }

        file_path = os.path.join(output_dir, f"{signature}.json")
        try:
            with open(file_path, "w") as f:
                json.dump(request_type_data, f, indent=2, default=str)
            print(f"Request type {first_log['method']} {first_log['normalized_endpoint']} -> {file_path}")
        except Exception as e:
            print(f"ERROR writing {file_path}: {e}")
            print(f"Problematic data keys: {list(request_type_data.keys())}")
            # Write a minimal version to help debug
            minimal_data = {
                "signature": request_type_data.get("signature"),
                "method": request_type_data.get("method"),
                "endpoint": request_type_data.get("normalized_endpoint"),
                "error": str(e),
            }
            with open(file_path, "w") as f:
                json.dump(minimal_data, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Dump API logs for OpenAPI spec improvement")
    parser.add_argument("--output-dir", default="api_logs_dump", help="Output directory for dumped files")
    parser.add_argument("--limit", type=int, help="Limit number of records to process")
    parser.add_argument("--chunk-size", type=int, default=1000, help="Number of records to process at once (default: 1000)")

    args = parser.parse_args()

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    print("Connecting to database...")
    connection = connect_to_db()

    print("Fetching API logs..." + (f" (limit: {args.limit})" if args.limit else ""))
    logs = fetch_api_logs(connection, args.limit, args.chunk_size)
    print(f"Fetched {len(logs)} log entries")

    print("Grouping logs by request type...")
    grouped_logs = group_logs_by_request_type(logs)
    print(f"Found {len(grouped_logs)} unique request types")

    print("Writing summary file...")
    write_summary_file(args.output_dir, grouped_logs)

    print("Writing individual request type files...")
    write_individual_files(args.output_dir, grouped_logs)

    print(f"\nDump completed! Files written to: {args.output_dir}")
    print("- summary.json: Overview of all request types")
    print("- *.json: Individual files for each unique request type")
    print("\nYou can now process these files with AI to improve your OpenAPI spec!")

    connection.close()


if __name__ == "__main__":
    main()
