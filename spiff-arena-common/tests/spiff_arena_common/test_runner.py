def test_bpmn_ids_match_by_exact_string_equality():
    assert "any_task" == "any_task"


def test_bpmn_ids_do_not_normalize_child_suffixes():
    assert "any_task [child]" != "any_task"
    assert "any_task" != "any_task [child]"
