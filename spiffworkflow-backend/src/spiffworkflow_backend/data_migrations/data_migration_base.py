from __future__ import annotations

import abc
from typing import Any

from flask import current_app
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel


class DataMigrationBase(metaclass=abc.ABCMeta):
    """Abstract class to describe what is required for data migration."""

    @classmethod
    def __subclasshook__(cls, subclass: Any) -> bool:
        return (
            hasattr(subclass, "run")
            and callable(subclass.run)
            and hasattr(subclass, "version")
            and callable(subclass.version)
            and NotImplemented
        )

    @classmethod
    @abc.abstractmethod
    def version(cls) -> str:
        """Returns the version number for the migration.

        NOTE: These versions should be string forms of integers.
        This is because eventually we will store them as integers on the process instance serializer version column.
        """
        raise NotImplementedError("method must be implemented on subclass: version")

    @classmethod
    @abc.abstractmethod
    def run(cls, process_instance: ProcessInstanceModel) -> None:
        raise NotImplementedError("method must be implemented on subclass: run")

    @classmethod
    def should_raise_on_error(cls) -> bool:
        return current_app.config.get("ENV_IDENTIFIER") in ["unit_testing", "local_development"]
