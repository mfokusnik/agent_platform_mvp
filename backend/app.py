from fastapi import FastAPI, Body, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse
from sqlmodel import SQLModel, Session, select
from typing import Optional, Dict, List
import pathlib, json, asyncio
from agent.models import Project, StepLog, ChatMessage, ProjectTask, WorkSchedule
from agent.runner import bootstrap_project, agent_step, chat_message
from agent.runner_utils import engine, set_status, log
from agent.scheduler import schedule_loop
from agent.rag import build_context_markdown

app = FastAPI(title="Agent Studio v5 (RU)")
SQLModel.metadata.create_all(engine)

ws_clients: Dict[int, List[WebSocket]] = {}

@app.on_event("startup")
async def on_start():
    asyncio.create_task(schedule_loop(engine))

@app.get("/")
def root():
    return {"ok": True, "message": "Agent Studio v5 (RU)"}

@app.post("/projects")
def create_project(name: str = Body(...), description: str = Body(""), tech_stack: str = Body(""), repo_url: Optional[str] = Body(None)):
    with Session(engine) as s:
        p = bootstrap_project(s, name, description, tech_stack, repo_url)
        return {"ok": True, "project_id": p.id, "workspace": p.workspace_path}

@app.get("/projects/{pid}")
def get_project(pid: int):
    with Session(engine) as s:
        p = s.get(Project, pid)
        if not p: raise HTTPException(404, "Проект не найден")
        return {"ok": True, "project": {"id": p.id, "name": p.name, "status": p.status, "tech_stack": p.tech_stack, "workspace": p.workspace_path}}

@app.post("/projects/{pid}/run")
def run_step(pid: int, task: str = Body(...)):
    with Session(engine) as s:
        if not s.get(Project, pid): raise HTTPException(404, "Проект не найден")
        agent_step(s, pid, task)
        return {"ok": True}

# ---- Chat (WS + history) ----
@app.websocket("/ws/{pid}")
async def ws_chat(ws: WebSocket, pid: int):
    await ws.accept()
    ws_clients.setdefault(pid, []).append(ws)
    try:
        while True:
            data = await ws.receive_text()
            with Session(engine) as s:
                p = s.get(Project, pid)
                if not p: 
                    await ws.send_text("Ошибка: проект не найден"); 
                    continue
                reply = chat_message(s, pid, data)
                await ws.send_text(reply)
    except WebSocketDisconnect:
        ws_clients[pid].remove(ws)

@app.get("/projects/{pid}/chat/history")
def chat_history(pid: int):
    with Session(engine) as s:
        p = s.get(Project, pid)
        if not p: raise HTTPException(404, "Проект не найден")
        msgs = s.exec(select(ChatMessage).where(ChatMessage.project_id==pid).order_by(ChatMessage.ts)).all()
        return {"ok": True, "messages": [{"ts":m.ts.isoformat(),"role":m.role,"content":m.content} for m in msgs]}

# ---- Tasks ----
@app.get("/projects/{pid}/tasks")
def list_tasks(pid: int):
    with Session(engine) as s:
        if not s.get(Project, pid): raise HTTPException(404, "Проект не найден")
        rows = s.exec(select(ProjectTask).where(ProjectTask.project_id==pid).order_by(ProjectTask.priority, ProjectTask.id)).all()
        return {"ok": True, "tasks": [{"id":r.id,"title":r.title,"status":r.status,"priority":r.priority} for r in rows]}

@app.post("/projects/{pid}/tasks")
def add_task(pid: int, title: str = Body(...), priority: int = Body(0)):
    with Session(engine) as s:
        if not s.get(Project, pid): raise HTTPException(404, "Проект не найден")
        row = ProjectTask(project_id=pid, title=title, priority=priority)
        s.add(row); s.commit()
        return {"ok": True, "task_id": row.id}

@app.patch("/projects/{pid}/tasks/{tid}")
def update_task(pid: int, tid: int, title: Optional[str] = Body(None), status: Optional[str] = Body(None), priority: Optional[int] = Body(None)):
    with Session(engine) as s:
        r = s.get(ProjectTask, tid)
        if not r or r.project_id != pid: raise HTTPException(404, "Задача не найдена")
        if title is not None: r.title = title
        if status is not None: r.status = status
        if priority is not None: r.priority = priority
        s.add(r); s.commit()
        return {"ok": True}

# ---- Schedule ----
@app.post("/projects/{pid}/schedule")
def set_schedule(pid: int, time_window: str = Body(...), days: str = Body("Mon,Tue,Wed,Thu,Fri,Sat,Sun"), enabled: bool = Body(True)):
    with Session(engine) as s:
        p = s.get(Project, pid)
        if not p: raise HTTPException(404, "Проект не найден")
        row = s.exec(select(WorkSchedule).where(WorkSchedule.project_id==pid)).first()
        if not row:
            row = WorkSchedule(project_id=pid, time_window=time_window, days=days, enabled=enabled)
        else:
            row.time_window = time_window; row.days = days; row.enabled = enabled
        s.add(row); s.commit()
        return {"ok": True}

# ---- Logs SSE ----
@app.get("/stream/{pid}")
async def stream(pid: int):
    async def event_gen():
        last = None
        while True:
            with Session(engine) as s:
                if not s.get(Project, pid):
                    yield {"event":"error","data":"Проект не найден"}
                    return
                logs = s.exec(select(StepLog).where(StepLog.project_id==pid).order_by(StepLog.ts.desc()).limit(1)).all()
                if logs:
                    l = logs[0]
                    key = f"{l.ts.isoformat()}|{l.id}"
                    if key != last:
                        last = key
                        yield {"event":"log","data":json.dumps({"ts":l.ts.isoformat(),"type":l.type,"role":l.role,"content":l.content}, ensure_ascii=False)}
            await asyncio.sleep(1.0)
    return EventSourceResponse(event_gen())

# ---- UI ----
@app.get("/ui", response_class=HTMLResponse)
def ui():
    html = (pathlib.Path(__file__).parent / "static" / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(html)
