import enum


class SpiffEnum(enum.Enum):
    @classmethod
    def list(cls) -> list[str]:
        return [el.value for el in cls]


class ProcessInstanceExecutionMode(SpiffEnum):
    asynchronous = "asynchronous"
    synchronous = "synchronous"
