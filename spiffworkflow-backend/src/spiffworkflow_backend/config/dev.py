"""Dev."""
from os import environ

GIT_MERGE_BRANCH = environ.get("GIT_MERGE_BRANCH", default="staging")
GIT_USERNAME = environ.get("GIT_USERNAME", default="sartography-automated-committer")
GIT_USER_EMAIL = environ.get(
    "GIT_USER_EMAIL", default="sartography-automated-committer@users.noreply.github.com"
)
