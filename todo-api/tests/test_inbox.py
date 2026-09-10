from todo_api.inbox.service import _attach_body


def test_attach_body_adds_todo_and_comment() -> None:
    body = _attach_body(
        {"description": "d", "todos": [{"id": "t1", "text": "old", "done": True}]},
        {"title": "Call vendor", "body": {"description": "They owe us a quote"}},
    )
    assert body["description"] == "d"
    assert [todo["text"] for todo in body["todos"]] == ["old", "Call vendor"]
    assert body["todos"][1]["done"] is False
    assert [comment["text"] for comment in body["comments"]] == ["They owe us a quote"]
    assert body["comments"][0]["at"]


def test_attach_body_without_description_adds_only_a_todo() -> None:
    body = _attach_body({}, {"title": "Call vendor", "body": {}})
    assert [todo["text"] for todo in body["todos"]] == ["Call vendor"]
    assert body["comments"] == []
