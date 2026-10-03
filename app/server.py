from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI(
    title="Tasks API",
    version="1.0.0",
    description="Небольшой REST API для управления задачами.",
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
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
    task = Task(id=next_id, **payload.model_dump())
    tasks[next_id] = task
    next_id += 1
    return task


@app.patch("/tasks/{task_id}", response_model=Task, tags=["tasks"], summary="Обновить задачу")
def update_task(task_id: int, payload: TaskUpdate) -> Task:
    task = tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    values = payload.model_dump(exclude_unset=True)
    updated = task.model_copy(update=values)
    tasks[task_id] = updated
    return updated


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["tasks"], summary="Удалить задачу")
def delete_task(task_id: int) -> None:
    if task_id not in tasks:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    del tasks[task_id]


