import asyncio, pytz, datetime
from sqlmodel import Session, select
from .config import settings
from .models import Project, WorkSchedule, StepLog
from .runner_utils import within_window, set_status, log

async def schedule_loop(engine):
    tz = pytz.timezone(settings.timezone)
    while True:
        try:
            with Session(engine) as s:
                projects = s.exec(select(Project)).all()
                for p in projects:
                    ws = s.exec(select(WorkSchedule).where(WorkSchedule.project_id==p.id)).first()
                    ok = within_window(ws, tz) if ws else True
                    if not ok and p.status == "running":
                        set_status(s, p.id, "sleeping")
                        log(s, p.id, "explain", "Выполнение приостановлено по расписанию (ночной режим)", role="system")
                    if ok and p.status == "sleeping":
                        set_status(s, p.id, "idle")
                        log(s, p.id, "explain", "Разрешённый интервал: можно продолжить работу", role="system")
        except Exception:
            pass
        await asyncio.sleep(30)
