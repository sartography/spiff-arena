import json
import time
from hashlib import sha256
from hmac import HMAC
from urllib.parse import urljoin
from urllib.parse import urlsplit

import requests
from flask import current_app

from spiffworkflow_backend.exceptions.api_error import ApiError


class FilestoreClientService:
    @classmethod
    def ensure_project(cls, payload: dict) -> dict:
        return cls._post("/v1/arena/projects/ensure", payload, "Could not sync process model files to Files")

    @classmethod
    def sync_file(
        cls,
        process_group_id: str,
        project_name: str,
        path: str,
        content_type: str | None = None,
    ) -> dict:
        payload: dict = {
            "arena_process_group_id": process_group_id,
            "name": project_name,
            "file": {
                "path": path,
            },
        }
        if content_type:
            payload["file"]["content_type"] = content_type

        return cls._post("/v1/arena/projects/files", payload, "Could not sync Arena file to Files")

    @classmethod
    def _post(cls, path: str, payload: dict, error_message: str) -> dict:
        url = cls._url(path)
        body = json.dumps(payload)
        response = requests.post(url, data=body, headers=cls._headers("POST", url, body), timeout=30)
        if response.status_code != 200:
            raise ApiError(
                error_code="filestore_sync_failed",
                message=f"{error_message}: {response.status_code}",
                status_code=502,
            )
        return response.json()

    @classmethod
    def tenant_id(cls) -> str:
        return current_app.config.get("SPIFFWORKFLOW_BACKEND_FILESTORE_TENANT_ID") or current_app.config["ENV_IDENTIFIER"]

    @classmethod
    def _url(cls, path: str) -> str:
        base_url = current_app.config.get("SPIFFWORKFLOW_BACKEND_FILESTORE_URL")
        if not base_url:
            raise ApiError(
                error_code="filestore_not_configured",
                message="SPIFFWORKFLOW_BACKEND_FILESTORE_URL is not configured",
                status_code=501,
            )
        return urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))

    @classmethod
    def _headers(cls, method: str, url: str, body: str) -> dict[str, str]:
        tenant_id = cls.tenant_id()
        headers = {"Content-Type": "application/json", "SpiffWorkflow-Tenant": tenant_id}
        secret = cls._secret()
        timestamp = str(int(time.time()))
        headers["SpiffWorkflow-Timestamp"] = timestamp
        headers["SpiffWorkflow-Signature"] = cls._signature(secret, method, cls._path(url), tenant_id, timestamp, body)
        return headers

    @classmethod
    def _secret(cls) -> str:
        secret = current_app.config.get("SPIFFWORKFLOW_BACKEND_FILESTORE_SHARED_SECRET")
        if not secret:
            raise ApiError(
                error_code="filestore_shared_secret_not_configured",
                message="SPIFFWORKFLOW_BACKEND_FILESTORE_SHARED_SECRET is not configured",
                status_code=501,
            )
        return secret

    @staticmethod
    def _signature(secret: str, method: str, path: str, tenant_id: str, timestamp: str, body: str) -> str:
        canonical = "\n".join([method.upper(), path, tenant_id, timestamp, sha256(body.encode()).hexdigest()])
        signature = HMAC(key=secret.encode(), msg=canonical.encode(), digestmod=sha256).hexdigest()
        return f"sha256={signature}"

    @staticmethod
    def _path(url: str) -> str:
        parsed = urlsplit(url)
        path = parsed.path
        if path.startswith("/api/"):
            path = path[4:]
        return path + (f"?{parsed.query}" if parsed.query else "")
