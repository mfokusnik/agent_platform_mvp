from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: str = ""
    tech_stack: str = ""
    repo_url: Optional[str] = None
    workspace_path: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "idle"     # idle|running|paused|sleeping|error|done
    control: str = ""        # JSON: {pause:bool, stop:bool}

class StepLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int
    ts: datetime = Field(default_factory=datetime.utcnow)
    role: str = "system"     # system|assistant|tool|user
    type: str = "log"        # log|error|tool|plan|code|commit|test_report|rag|chat|explain
    content: str = ""        # markdown/json
    meta: str = ""           # json string

class FileIndex(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int
    path: str
    summary: str = ""
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int
    ts: datetime = Field(default_factory=datetime.utcnow)
    role: str = "user"       # user|assistant|system
    content: str = ""

class ProjectTask(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int
    title: str
    status: str = "pending"  # pending|in_progress|done
    priority: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class WorkSchedule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int
    time_window: str = "23:00-07:00"
    days: str = "Mon,Tue,Wed,Thu,Fri,Sat,Sun"
    enabled: bool = True
