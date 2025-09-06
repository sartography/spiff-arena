# Login permission to spiffworkflow-frontend

- Is there a permission for just accessing frontend?
  - we want to restrict access to spiffWorkflow proper to only subset of all users
  - other users that access models trigger them via API, but are not allowed to login to spiffworkflow-frontend

Backend allows for DENY:blah style permissions. Perhaps that would be appropriate here.
Normally backend permission checks are on a path basis, to see if the backend path is allowed, but this use case might have to deviate from that convention.
Definitely default to allowing access to frontend.
Frontend calls backend immediately on load just to check if backend is up. Perhaps that would be an appropriate place to run this permission check, but perhaps not.
