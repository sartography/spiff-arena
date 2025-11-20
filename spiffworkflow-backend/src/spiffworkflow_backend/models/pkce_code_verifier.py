from dataclasses import dataclass

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


@dataclass
class PkceCodeVerifierModel(SpiffworkflowBaseDBModel):
    """
    In the OAuth PKCE flow, the first request to the auth server ("give me an auth code") sends a one-time code challenge.
    The next request ("give me an access token") needs to send a one-time code verifier based on that challenge.
    (This ensures the client that requested the auth code is the same one requesting the access token with that auth code.)
    We store such code verifiers here.
    """

    __tablename__ = "pkce_code_verifier"

    id: int = db.Column(db.Integer, primary_key=True)
    pkce_id: str = db.Column(db.String(512), nullable=False, unique=True)  # Unique per-login PKCE lookup key
    code_verifier: str = db.Column(db.String(512), nullable=False)

    # In case there are accumulated entries, use created_at_in_seconds to determine outdated entries
    created_at_in_seconds: int = db.Column(db.Integer, nullable=False)
