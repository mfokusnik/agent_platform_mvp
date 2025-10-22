import pathlib
from sqlmodel import Session, select
from .models import FileIndex, StepLog
from .llm_client import call_llm

def index_project(session: Session, project):
    root = pathlib.Path(project.workspace_path)
    files = [p for p in root.rglob("*") if p.is_file() and p.suffix in (".md",".py",".js",".ts",".php",".json",".yaml",".yml",".txt",".ini",".env",".html",".css")]
    for p in files[:400]:
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            txt = ""
        prompt = f"Суммаризируй файл простыми словами (1-2 абзаца) для пользователя без тех. знаний.\nПуть: {p.relative_to(root)}\n---\n{txt[:4000]}"
        summary = call_llm(prompt)
        row = session.exec(select(FileIndex).where(FileIndex.project_id==project.id, FileIndex.path==str(p))).first()
        if not row:
            row = FileIndex(project_id=project.id, path=str(p), summary=summary)
            session.add(row)
        else:
            row.summary = summary
        session.add(StepLog(project_id=project.id, type="rag", role="system", content=f"Indexed {p}"))
    session.commit()

def build_context_markdown(session: Session, project):
    root = pathlib.Path(project.workspace_path)
    agent_dir = root / ".agent"; agent_dir.mkdir(exist_ok=True)
    rows = session.exec(select(FileIndex).where(FileIndex.project_id==project.id)).all()
    body = ["# Краткое описание файлов (для всех)\n"]
    for r in rows[:200]:
        body.append(f"## {r.path}\n{r.summary}\n")
    (agent_dir / "context.md").write_text("\n".join(body), encoding="utf-8")
    session.add(StepLog(project_id=project.id, type="explain", role="system", content="Обновлён контекст проекта (.agent/context.md)"))
    session.commit()
