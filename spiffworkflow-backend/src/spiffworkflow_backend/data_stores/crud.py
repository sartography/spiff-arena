from typing import Any


class DataStoreCRUD:
    @staticmethod
    def create_instance(name: str, identifier: str, location: str, schema: dict[str, Any], description: str | None) -> None:
        raise Exception("must implement")

    @staticmethod
    def existing_data_stores() -> list[dict[str, Any]]:
        raise Exception("must implement")

    @staticmethod
    def query_data_store(name: str) -> Any:
        raise Exception("must implement")

    @staticmethod
    def build_response_item(model: Any) -> dict[str, Any]:
        raise Exception("must implement")

    @staticmethod
    def create_record(name: str, data: dict[str, Any]) -> None:
        raise Exception("must implement")

    @staticmethod
    def update_record(name: str, data: dict[str, Any]) -> None:
        raise Exception("must implement")

    @staticmethod
    def delete_record(name: str, data: dict[str, Any]) -> None:
        raise Exception("must implement")
