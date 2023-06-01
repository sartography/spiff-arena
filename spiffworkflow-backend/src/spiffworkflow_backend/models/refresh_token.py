from dataclasses import dataclass

from sqlalchemy import ForeignKey

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db

# from sqlalchemy.orm import relationship

# from spiffworkflow_backend.models.user import UserModel


@dataclass()
class RefreshTokenModel(SpiffworkflowBaseDBModel):
    __tablename__ = "refresh_token"

    id: int = db.Column(db.Integer, primary_key=True)
    user_id: int = db.Column(ForeignKey("user.id"), nullable=False, unique=True)
    token: str = db.Column(db.String(1024), nullable=False)
    # user = relationship("UserModel", back_populates="refresh_token")
