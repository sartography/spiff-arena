#!/usr/bin/env python3
import concurrent.futures
import json
import os
import subprocess
import sys


def get_access_token(script_dir, username="admin", password="admin", realm_name="spiffworkflow"):
    """
    Get access token once
    """
    get_token_cmd = f"{script_dir}/get_token {username} {password} {realm_name}"
    return subprocess.check_output(get_token_cmd, shell=True, text=True).strip()


def run_curl_command(message_identifier, access_token, backend_base_url):
    """
    Execute the curl command for load testing

    :return: Tuple of (success, result)
    """
    try:
        # Login command
        login_cmd = f"curl --silent -X POST '{backend_base_url}/v1.0/login_with_access_token?access_token={access_token}' -H 'Authorization: Bearer {access_token}' >/dev/null"
        subprocess.run(login_cmd, shell=True, check=True)

        # Message sending command
        message_cmd = f"curl --silent -X POST '{backend_base_url}/v1.0/messages/{message_identifier}?execution_mode=asynchronous' -H 'Authorization: Bearer {access_token}' -d '{{\"payload\": {{\"email\": \"HEY@example.com\"}}}}' -H 'Content-type: application/json'"
        result = subprocess.check_output(message_cmd, shell=True, text=True)

        # Check for errors
        try:
            error_code = json.loads(result).get("error_code")
            if error_code is not None and error_code != "null":
                return False, result
        except json.JSONDecodeError:
            pass

        return True, result

    except subprocess.CalledProcessError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)


def load_test(message_identifier, num_requests=10, max_workers=5, username="admin", password="admin", realm_name="spiffworkflow"):
    """
    Perform load testing with concurrent requests and failure logging
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_base_url = os.environ.get("BACKEND_BASE_URL", "http://localhost:7000")

    # Get access token once
    access_token = get_access_token(script_dir, username, password, realm_name)

    successful_requests = 0
    failed_requests = 0
    failure_log = []

    # Use ThreadPoolExecutor for I/O-bound tasks like network requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Create futures for all requests
        futures = [
            executor.submit(run_curl_command, message_identifier, access_token, backend_base_url) for _ in range(num_requests)
        ]

        # Collect and process results
        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            success, result = future.result()
            if success:
                successful_requests += 1
                print(f"Request {i}: Success")
            else:
                failed_requests += 1
                failure_log.append({"request_number": i, "error_message": result})
                print(f"Request {i}: Failure")

    # Log failures to a file if any exist
    if failure_log:
        filename = "failure_log.json"
        with open(filename, "w") as f:
            json.dump(failure_log, f, indent=2)
        print(f"\nFailure details logged to {filename}")

    # Print summary
    print("\nLoad Test Summary:")
    print(f"Total Requests: {num_requests}")
    print(f"Successful Requests: {successful_requests}")
    print(f"Failed Requests: {failed_requests}")
    print(f"Success Rate: {successful_requests/num_requests*100:.2f}%")


def main():
    # Parse command-line arguments
    if len(sys.argv) < 2:
        print("Usage: python load_test.py <message_identifier> [num_requests] [max_workers] [username] [password] [realm_name]")
        sys.exit(1)

    message_identifier = sys.argv[1]
    num_requests = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    max_workers = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    username = sys.argv[4] if len(sys.argv) > 4 else "admin"
    password = sys.argv[5] if len(sys.argv) > 5 else "admin"
    realm_name = sys.argv[6] if len(sys.argv) > 6 else "spiffworkflow"

    load_test(message_identifier, num_requests, max_workers, username, password, realm_name)


if __name__ == "__main__":
    main()
