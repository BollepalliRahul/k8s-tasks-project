import os
import time
from contextlib import asynccontextmanager

import psycopg2
from fastapi import FastAPI
from pydantic import BaseModel


def get_conn():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "tasks"),
        user=os.getenv("POSTGRES_USER", "tasks_user"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
    )


def init_db():
    # Retry because Postgres may still be starting up
    for _ in range(30):
        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute(
                "CREATE TABLE IF NOT EXISTS tasks ("
                "id SERIAL PRIMARY KEY, title TEXT NOT NULL, done BOOLEAN DEFAULT FALSE)"
            )
            conn.commit()
            conn.close()
            return
        except psycopg2.OperationalError:
            time.sleep(2)
    raise RuntimeError("Could not connect to Postgres")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)


class TaskIn(BaseModel):
    title: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, title, done FROM tasks ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "done": r[2]} for r in rows]


@app.post("/tasks")
def create_task(task: TaskIn):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO tasks (title) VALUES (%s) RETURNING id", (task.title,))
    new_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return {"id": new_id, "title": task.title, "done": False}