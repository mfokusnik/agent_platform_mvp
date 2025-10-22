import json, pathlib, pytz
from sqlmodel import Session, select
from .models import Project, StepLog, ChatMessage, ProjectTask
from .tools import write_file, run_cmd
from .llm_client import call_llm, chat_llm
from .rag import index_project, build_context_markdown
from .github import init_repo, new_branch, commit_all, push_current
from .runner_utils import engine, set_status, log
from .config import settings

def bootstrap_project(session: Session, name: str, description: str, tech_stack: str, repo_url: str | None) -> Project:
    root = pathlib.Path(settings.workspace_root); root.mkdir(parents=True, exist_ok=True)
    wp = root / name.replace(" ","_"); wp.mkdir(parents=True, exist_ok=True)
    project = Project(name=name, description=description, tech_stack=tech_stack, repo_url=repo_url, workspace_path=str(wp))
    session.add(project); session.commit()
    init_repo(str(wp), repo_url, settings.github_token)
    write_file(str(wp / "README.md"), f"# {name}\n\n{description}\n\nТехстек: {tech_stack}\n", create_dirs=True)
    commit_all(str(wp), "chore: bootstrap project")
    return project

def agent_step(session: Session, pid: int, message: str):
    project = session.get(Project, pid)
    set_status(session, pid, "running")
    # Пояснение для нефизтехов
    explain_prompt = f"Объясни простыми словами, что будет сделано: {message}. Коротко: 1-2 предложения."
    explanation = call_llm(explain_prompt)
    log(session, pid, "explain", explanation, role="assistant")
    # План и действия (минимальная демонстрация)
    plan_prompt = f"""
Ты агент-помощник. Составь чёткий план (3-7 шагов) и предложи конкретные команды (если нужны).
Проект: {project.name} (стек: {project.tech_stack})
Задача: {message}
"""
    plan = call_llm(plan_prompt)
    log(session, pid, "plan", plan, role="assistant")
    # Сохраняем план
    write_file(str(pathlib.Path(project.workspace_path)/".agent"/"plan.txt"), plan, create_dirs=True)
    state = commit_all(project.workspace_path, "docs: обновлён план")
    log(session, pid, "commit", state)
    # Индексация (краткие описания для всех)
    index_project(session, project); build_context_markdown(session, project)
    set_status(session, pid, "idle")

def chat_message(session: Session, pid: int, text: str) -> str:
    project = session.get(Project, pid)
    session.add(ChatMessage(project_id=pid, role="user", content=text)); session.commit()
    ctx_file = pathlib.Path(project.workspace_path)/".agent"/"context.md"
    system = f"Ты — агент проекта '{project.name}'. Объясняй просто, предлагай действия, добавляй задачи при необходимости."
    history=[{"role":"user","content":text}]
    if ctx_file.exists(): system += "\nКонтекст:\n" + ctx_file.read_text(encoding="utf-8")[:4000]
    reply = chat_llm(system, history)
    session.add(ChatMessage(project_id=pid, role="assistant", content=reply)); session.commit()
    log(session, pid, "chat", reply, role="assistant")
    return reply
