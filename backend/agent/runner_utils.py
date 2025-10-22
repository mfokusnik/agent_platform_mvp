import json, datetime, pytz, pathlib
from sqlmodel import SQLModel, Session, create_engine, select
from .models import Project, StepLog, WorkSchedule
from .config import settings

DB_PATH = pathlib.Path("state.db")
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SQLModel.metadata.create_all(engine)

def _now_local(tz):
    return datetime.datetime.now(tz)

def within_window(ws: WorkSchedule, tz) -> bool:
    if not ws or not ws.enabled: return True
    now = _now_local(tz)
    day = now.strftime("%a")
    if day not in ws.days.split(","): return False
    try:
        start_s, end_s = ws.time_window.split("-")
        sh, sm = map(int, start_s.split(":"))
        eh, em = map(int, end_s.split(":"))
    except Exception:
        return True
    start = now.replace(hour=sh, minute=sm, second=0, microsecond=0)
    end = now.replace(hour=eh, minute=em, second=0, microsecond=0)
    if start <= end:
        return start <= now <= end
    return now >= start or now <= end

def set_status(session: Session, pid: int, status: str):
    p = session.get(Project, pid); p.status = status; session.add(p); session.commit()

def log(session: Session, pid: int, type_: str, content: str, role: str = "system"):
    entry = StepLog(project_id=pid, type=type_, content=content, role=role)
    session.add(entry); session.commit()
