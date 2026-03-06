#!/usr/bin/env python3
"""
Script to extract all relevant information for a single operation from an OpenAPI spec.
Includes operation details, parameters, request/response schemas, and referenced entities.
"""

import os
import sys
from typing import Any

import yaml


def load_openapi_spec(filepath: str) -> dict:
    """Load the OpenAPI specification from a YAML file."""
    with open(filepath) as f:
        return yaml.safe_load(f)


def resolve_ref(spec: dict, ref: str) -> dict:
    """Resolve a $ref reference to its actual schema definition."""
    if not ref.startswith("#/"):
        raise ValueError(f"Only local references are supported: {ref}")

    parts = ref.split("/")[1:]  # Remove the leading '#'
    current = spec
    for part in parts:
        current = current[part]
    return current


def extract_schema_refs(obj: Any, refs: set[str]) -> None:
    """Recursively extract all $ref references from an object."""
    if isinstance(obj, dict):
        if "$ref" in obj:
            refs.add(obj["$ref"])
        for value in obj.values():
            extract_schema_refs(value, refs)
    elif isinstance(obj, list):
        for item in obj:
            extract_schema_refs(item, refs)


def get_all_referenced_schemas(spec: dict, initial_refs: set[str]) -> dict[str, dict]:
    """
    Get all schemas referenced directly or indirectly from the initial set of refs.
    Returns a dictionary mapping schema names to their definitions.
    """
    schemas = {}
    to_process = set(initial_refs)
    processed = set()

    while to_process:
        ref = to_process.pop()
        if ref in processed:
            continue
        processed.add(ref)

        # Extract schema name from ref
        if ref.startswith("#/components/schemas/"):
            schema_name = ref.split("/")[-1]
            schema_def = resolve_ref(spec, ref)
            schemas[schema_name] = schema_def

            # Find any nested refs in this schema
            nested_refs = set()
            extract_schema_refs(schema_def, nested_refs)
            to_process.update(nested_refs - processed)

    return schemas


def get_all_operation_ids(spec: dict) -> list[str]:
    """
    Get all operation IDs from the spec.
    Returns a list of operation IDs.
    """
    operation_ids = []
    for _path, path_item in spec.get("paths", {}).items():
        for method, operation in path_item.items():
            if method in ["get", "post", "put", "delete", "patch", "options", "head"]:
                if isinstance(operation, dict) and "operationId" in operation:
                    operation_ids.append(operation["operationId"])
    return operation_ids


def find_matching_operation_ids(spec: dict, search_term: str) -> list[str]:
    """
    Find all operation IDs that match the search term.

    Matching priority:
    1. Exact match of full operation ID
    2. Exact match of last segment (after last dot)
    3. Partial match anywhere in operation ID

    Returns a list of matching operation IDs.
    """
    all_ids = get_all_operation_ids(spec)

    # Check for exact match first
    if search_term in all_ids:
        return [search_term]

    # Check for exact match of last segment
    last_segment_matches = []
    for op_id in all_ids:
        last_segment = op_id.split(".")[-1]
        if last_segment == search_term:
            last_segment_matches.append(op_id)

    if len(last_segment_matches) == 1:
        return last_segment_matches
    elif len(last_segment_matches) > 1:
        # Multiple last segment matches - return them for disambiguation
        return last_segment_matches

    # Fall back to partial matching
    partial_matches = [op_id for op_id in all_ids if search_term in op_id]
    return partial_matches


def find_operation(spec: dict, operation_id: str) -> tuple:
    """
    Find an operation by its operationId.
    Returns (path, method, operation_details) or (None, None, None) if not found.
    """
    for path, path_item in spec.get("paths", {}).items():
        for method, operation in path_item.items():
            if method in ["get", "post", "put", "delete", "patch", "options", "head"]:
                if isinstance(operation, dict) and operation.get("operationId") == operation_id:
                    return path, method, operation
    return None, None, None


def extract_operation_info(spec: dict, operation_id: str) -> dict:
    """
    Extract all relevant information for a single operation.
    """
    path, method, operation = find_operation(spec, operation_id)

    if not operation:
        return {"error": f"Operation '{operation_id}' not found in the specification"}

    # Collect all schema references
    refs = set()

    # Extract refs from parameters
    if "parameters" in operation:
        extract_schema_refs(operation["parameters"], refs)

    # Extract refs from path-level parameters
    path_item = spec["paths"][path]
    if "parameters" in path_item:
        extract_schema_refs(path_item["parameters"], refs)

    # Extract refs from request body
    if "requestBody" in operation:
        extract_schema_refs(operation["requestBody"], refs)

    # Extract refs from responses
    if "responses" in operation:
        extract_schema_refs(operation["responses"], refs)

    # Get all referenced schemas (including nested ones)
    schemas = get_all_referenced_schemas(spec, refs)

    # Build the result
    result = {
        "operation_id": operation_id,
        "path": path,
        "method": method.upper(),
        "summary": operation.get("summary", ""),
        "description": operation.get("description", ""),
        "tags": operation.get("tags", []),
        "parameters": [],
        "request_body": None,
        "responses": {},
        "schemas": schemas,
    }

    # Process path-level parameters
    path_params = path_item.get("parameters", [])

    # Process operation-level parameters
    operation_params = operation.get("parameters", [])

    # Combine and deduplicate parameters
    all_params = path_params + operation_params
    for param in all_params:
        param_info = {
            "name": param.get("name"),
            "in": param.get("in"),
            "required": param.get("required", False),
            "description": param.get("description", ""),
            "schema": param.get("schema", {}),
        }
        result["parameters"].append(param_info)

    # Process request body
    if "requestBody" in operation:
        req_body = operation["requestBody"]
        result["request_body"] = {
            "required": req_body.get("required", False),
            "description": req_body.get("description", ""),
            "content": req_body.get("content", {}),
        }

    # Process responses
    for status_code, response in operation.get("responses", {}).items():
        result["responses"][status_code] = {
            "description": response.get("description", ""),
            "content": response.get("content", {}),
        }

    return result


def print_operation_info(info: dict) -> None:
    """Pretty print the operation information."""
    if "error" in info:
        print(f"Error: {info['error']}")
        return

    print("=" * 80)
    print(f"Operation: {info['operation_id']}")
    print("=" * 80)
    print(f"Path: {info['path']}")
    print(f"Method: {info['method']}")
    print(f"Summary: {info['summary']}")
    if info["description"]:
        print(f"Description: {info['description']}")
    print(f"Tags: {', '.join(info['tags'])}")

    print("\n" + "-" * 80)
    print("PARAMETERS")
    print("-" * 80)
    if info["parameters"]:
        for param in info["parameters"]:
            required = " (required)" if param["required"] else ""
            print(f"  {param['name']} [{param['in']}]{required}")
            if param["description"]:
                print(f"    Description: {param['description']}")
            print(f"    Schema: {param['schema']}")
    else:
        print("  None")

    print("\n" + "-" * 80)
    print("REQUEST BODY")
    print("-" * 80)
    if info["request_body"]:
        req = info["request_body"]
        required = " (required)" if req["required"] else ""
        print(f"  Required: {required}")
        if req["description"]:
            print(f"  Description: {req['description']}")
        print(f"  Content Types: {', '.join(req['content'].keys())}")
        for content_type, content in req["content"].items():
            print(f"    {content_type}:")
            if "schema" in content:
                print(f"      Schema: {content['schema']}")
    else:
        print("  None")

    print("\n" + "-" * 80)
    print("RESPONSES")
    print("-" * 80)
    for status_code, response in info["responses"].items():
        print(f"  {status_code}: {response['description']}")
        if response["content"]:
            print(f"    Content Types: {', '.join(response['content'].keys())}")
            for content_type, content in response["content"].items():
                print(f"      {content_type}:")
                if "schema" in content:
                    print(f"        Schema: {content['schema']}")

    print("\n" + "-" * 80)
    print("REFERENCED SCHEMAS")
    print("-" * 80)
    if info["schemas"]:
        for schema_name, schema_def in sorted(info["schemas"].items()):
            print(f"\n  {schema_name}:")
            print(f"    {yaml.dump(schema_def, default_flow_style=False, indent=6)}")
    else:
        print("  None")

    print("\n" + "=" * 80)


def get_default_spec_path() -> str:
    """
    Determine the default path to api.yml relative to this script.
    Assumes the script is in bin/openapi/ and api.yml is in src/spiffworkflow_backend/api.yml
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up two levels from bin/openapi/ to the project root
    bin_dir = os.path.dirname(script_dir)
    project_root = os.path.dirname(bin_dir)
    # Construct path to api.yml
    api_path = os.path.join(project_root, "src", "spiffworkflow_backend", "api.yml")
    return api_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_operation_info.py <operation_id> [api_spec.yml] [--save]")
        print("\nExample: python extract_operation_info.py process_instance_create")
        print("         python extract_operation_info.py process_instance_create custom_api.yml")
        print("         python extract_operation_info.py process_instance_create --save")
        print("\nIf api_spec.yml is not provided, defaults to ../src/spiffworkflow_backend/api.yml")
        print("\nNote: You can provide a partial operation ID. If it matches exactly one operation,")
        print("      that operation will be used. If multiple operations match, they will be listed.")
        sys.exit(1)

    search_term = sys.argv[1]

    # Determine spec file path
    spec_file = None
    save_output = False

    # Check remaining arguments
    for arg in sys.argv[2:]:
        if arg == "--save":
            save_output = True
        elif spec_file is None and not arg.startswith("--"):
            spec_file = arg

    # Use default if no spec file provided
    if spec_file is None:
        spec_file = get_default_spec_path()
        print(f"Using default spec file: {spec_file}\n")

    try:
        spec = load_openapi_spec(spec_file)

        # Try to find matching operation IDs
        matching_ids = find_matching_operation_ids(spec, search_term)

        if len(matching_ids) == 0:
            print(f"Error: No operations found matching '{search_term}'")
            sys.exit(1)
        elif len(matching_ids) > 1:
            print(f"Error: Multiple operations match '{search_term}':")
            for op_id in sorted(matching_ids):
                print(f"  - {op_id}")
            print("\nPlease be more specific.")
            sys.exit(1)
        else:
            # Exactly one match - use it
            operation_id = matching_ids[0]
            if operation_id != search_term:
                print(f"Found matching operation: {operation_id}\n")

            info = extract_operation_info(spec, operation_id)
            print_operation_info(info)

            # Optionally save to a file
            if save_output:
                output_file = f"{operation_id}_info.yml"
                with open(output_file, "w") as f:
                    yaml.dump(info, f, default_flow_style=False, sort_keys=False)
                print(f"\nInformation saved to: {output_file}")

    except FileNotFoundError:
        print(f"Error: File '{spec_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
