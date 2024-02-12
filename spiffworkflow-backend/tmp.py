pull_request_accepted = False
pull_request_changes_requested = False

# states: approved, commented, changes_requested
if body["action"] == "submitted":
    if body["review"]["state"] == "approved":
        pull_request_accepted = True
    elif body["review"]["state"] == "changes_requested":
        pull_request_changes_requested = True

    pull_request_url = body["pull_request"]["html_url"]

del headers
