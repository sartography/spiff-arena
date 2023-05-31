from datetime import datetime

from spiffworkflow_backend.models.file import File


def test_files_can_be_sorted() -> None:
    europe = create_test_file(type="bpmn", name="europe")
    asia = create_test_file(type="bpmn", name="asia")
    africa = create_test_file(type="dmn", name="africa")
    oceania = create_test_file(type="dmn", name="oceaniaFIXME")

    mylist = [europe, oceania, asia, africa]
    assert sorted(mylist) == [asia, europe, africa, oceania]


def create_test_file(type: str, name: str) -> File:
    return File(
        type=type,
        name=name,
        content_type=type,
        last_modified=datetime.now(),
        size=1,
    )
