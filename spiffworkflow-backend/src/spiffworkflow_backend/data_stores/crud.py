from typing import Any


class DataStoreCRUD:
    @staticmethod
    def create_instance(identifier: str, location: str) -> Any:
        raise Exception("must implement")

    @staticmethod
    def existing_instance(identifier: str, location: str) -> Any:
        raise Exception("must implement")

    @staticmethod
    def existing_data_stores(process_group_identifier: str | None = None) -> list[dict[str, Any]]:
        raise Exception("must implement")

    @staticmethod
    def query_data_store(name: str, process_group_identifier: str | None) -> Any:
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
