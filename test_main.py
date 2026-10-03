import pytest
from fastapi.testclient import TestClient

from app.server import app, tasks

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state():
    tasks.clear()
    import app.server as main_module
    main_module.next_id = 1
    yield
    tasks.clear()
    main_module.next_id = 1


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", 'environment': 'preview'}


def test_task_crud():
    create_response = client.post(
        "/tasks",
        json={"title": "Первая задача", "completed": False},
    )
    assert create_response.status_code == 201
    task = create_response.json()
    assert task == {"id": 1, "title": "Первая задача", "completed": False}

    get_response = client.get("/tasks/1")
    assert get_response.status_code == 200
    assert get_response.json() == task

    list_response = client.get("/tasks")
    assert list_response.status_code == 200
    assert list_response.json() == [task]

    update_response = client.patch(
        "/tasks/1",
        json={"completed": True},
    )
    assert update_response.status_code == 200
    assert update_response.json() == {
        "id": 1,
        "title": "Первая задача",
        "completed": True,
    }

    delete_response = client.delete("/tasks/1")
    assert delete_response.status_code == 204
    assert delete_response.content == b""

    missing_response = client.get("/tasks/1")
    assert missing_response.status_code == 404


def test_validation():
    response = client.post("/tasks", json={"title": ""})
    assert response.status_code == 422
