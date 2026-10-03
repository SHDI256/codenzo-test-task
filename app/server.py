from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

app = FastAPI(
    title="Tasks API",
    version="1.0.0",
    description="REST API для управления задачами.",
)


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    completed: bool = False


class Task(TaskCreate):
    id: int


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    completed: bool | None = None


tasks = {}
next_id = 1


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home():
    return HTMLResponse(
        content="""
<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tasks</title>

<style>
* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f3f4f6;
    color: #111827;
}

.wrap {
    max-width: 760px;
    margin: 40px auto;
    padding: 0 16px;
}

.box {
    background: #ffffff;
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
    margin-bottom: 16px;
}

h1 {
    margin: 0 0 8px;
}

p {
    color: #6b7280;
}

.form {
    display: flex;
    gap: 10px;
}

.form input {
    flex: 1;
    min-width: 0;
    padding: 12px;
    border: 1px solid #d1d5db;
    border-radius: 10px;
    font-size: 16px;
}

.form button {
    padding: 12px 18px;
}

.task {
    display: flex;
    align-items: center;
    gap: 12px;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 12px;
    margin-bottom: 10px;
}

.task .title {
    flex: 1;
    word-break: break-word;
}

.done {
    text-decoration: line-through;
    color: #9ca3af;
}

.actions {
    display: flex;
    gap: 8px;
}

.actions button {
    border: 0;
    border-radius: 8px;
    padding: 8px 12px;
    cursor: pointer;
}

.edit {
    background: #f59e0b;
    color: #ffffff;
}

.delete {
    background: #ef4444;
    color: #ffffff;
}

.empty {
    text-align: center;
    color: #9ca3af;
    padding: 20px;
}

.stats {
    margin-top: 12px;
    color: #6b7280;
    font-size: 14px;
}

.error {
    color: #b91c1c;
}

@media (max-width: 600px) {
    .form {
        flex-direction: column;
    }

    .task {
        align-items: flex-start;
        flex-wrap: wrap;
    }

    .actions {
        width: 100%;
        margin-left: 32px;
    }

    .actions button {
        flex: 1;
    }
}
</style>
</head>

<body>
<div class="wrap">

    <div class="box">
        <h1>Менеджер задач</h1>
        <p>Создавай, редактируй, отмечай и удаляй задачи.</p>

        <form id="form" class="form">
            <input
                id="title"
                maxlength="200"
                minlength="1"
                placeholder="Новая задача"
                required
            >
            <button type="submit">Добавить</button>
        </form>
    </div>

    <div class="box">
        <div id="list"></div>
        <div id="stats" class="stats"></div>
    </div>

</div>

<script>
const form = document.getElementById("form");
const title = document.getElementById("title");
const list = document.getElementById("list");
const stats = document.getElementById("stats");

async function api(url, options = {}) {
    const response = await fetch(url, options);

    if (!response.ok) {
        let detail = "Ошибка запроса";

        try {
            const data = await response.json();

            if (data.detail) {
                if (Array.isArray(data.detail)) {
                    detail = data.detail
                        .map(item => item.msg || String(item))
                        .join(", ");
                } else {
                    detail = data.detail;
                }
            }
        } catch (error) {
        }

        throw new Error(detail);
    }

    if (response.status === 204) {
        return null;
    }

    return response.json();
}

function makeButton(text, className, handler) {
    const button = document.createElement("button");

    button.type = "button";
    button.className = className;
    button.textContent = text;

    button.addEventListener("click", handler);

    return button;
}

function render(tasks) {
    list.innerHTML = "";

    if (tasks.length === 0) {
        const empty = document.createElement("div");

        empty.className = "empty";
        empty.textContent = "Задач пока нет";

        list.appendChild(empty);

        stats.textContent = "";

        return;
    }

    let completedCount = 0;

    for (const task of tasks) {
        if (task.completed) {
            completedCount++;
        }

        const row = document.createElement("div");
        row.className = "task";

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.checked = task.completed;

        checkbox.addEventListener("change", () => {
            updateTask(task.id, {
                completed: checkbox.checked
            });
        });

        const text = document.createElement("div");

        text.className = "title";

        if (task.completed) {
            text.classList.add("done");
        }

        text.textContent = task.title;

        const actions = document.createElement("div");
        actions.className = "actions";

        const editButton = makeButton(
            "Изменить",
            "edit",
            () => editTask(task)
        );

        const deleteButton = makeButton(
            "Удалить",
            "delete",
            () => deleteTask(task.id)
        );

        actions.appendChild(editButton);
        actions.appendChild(deleteButton);

        row.appendChild(checkbox);
        row.appendChild(text);
        row.appendChild(actions);

        list.appendChild(row);
    }

    stats.textContent =
        "Всего: " +
        tasks.length +
        " | Выполнено: " +
        completedCount;
}

async function loadTasks() {
    try {
        const tasks = await api("/tasks");

        render(tasks);
    } catch (error) {
        list.innerHTML = "";

        const errorElement = document.createElement("div");

        errorElement.className = "error";
        errorElement.textContent = error.message;

        list.appendChild(errorElement);
    }
}

form.addEventListener("submit", async event => {
    event.preventDefault();

    const value = title.value.trim();

    if (!value) {
        return;
    }

    try {
        await api("/tasks", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                title: value,
                completed: false
            })
        });

        title.value = "";

        await loadTasks();

        title.focus();
    } catch (error) {
        alert(error.message);
    }
});

async function updateTask(id, data) {
    try {
        await api("/tasks/" + id, {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        });

        await loadTasks();
    } catch (error) {
        alert(error.message);
        await loadTasks();
    }
}

async function editTask(task) {
    const value = prompt(
        "Новое название задачи:",
        task.title
    );

    if (value === null) {
        return;
    }

    const newTitle = value.trim();

    if (!newTitle) {
        alert("Название задачи не может быть пустым");
        return;
    }

    await updateTask(task.id, {
        title: newTitle
    });
}

async function deleteTask(id) {
    if (!confirm("Удалить задачу?")) {
        return;
    }

    try {
        await api("/tasks/" + id, {
            method: "DELETE"
        });

        await loadTasks();
    } catch (error) {
        alert(error.message);
    }
}

loadTasks();
</script>

</body>
</html>
"""
    )


@app.get("/health", tags=["system"], summary="Проверка состояния сервера")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": "preview"}


@app.get("/tasks", response_model=list[Task], tags=["tasks"], summary="Получить список задач")
def list_tasks() -> list[Task]:
    return list(tasks.values())


@app.get("/tasks/{task_id}", response_model=Task, tags=["tasks"], summary="Получить задачу")
def get_task(task_id: int) -> Task:
    task = tasks.get(task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task


@app.post(
    "/tasks",
    response_model=Task,
    status_code=status.HTTP_201_CREATED,
    tags=["tasks"],
    summary="Создать задачу",
)
def create_task(payload: TaskCreate) -> Task:
    global next_id

    task = Task(
        id=next_id,
        **payload.model_dump()
    )

    tasks[next_id] = task
    next_id += 1

    return task


@app.patch(
    "/tasks/{task_id}",
    response_model=Task,
    tags=["tasks"],
    summary="Обновить задачу"
)
def update_task(task_id: int, payload: TaskUpdate) -> Task:
    task = tasks.get(task_id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    values = payload.model_dump(exclude_unset=True)
    updated = task.model_copy(update=values)

    tasks[task_id] = updated

    return updated


@app.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["tasks"],
    summary="Удалить задачу"
)
def delete_task(task_id: int) -> None:
    if task_id not in tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    del tasks[task_id]

