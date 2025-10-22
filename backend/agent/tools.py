import subprocess, os, json, pathlib, shlex
from typing import Any, Dict
from .config import settings

ALLOWED = ("git","pip","python","pytest","npm","pnpm","yarn","composer","php","node")

def ensure_dir(path: str) -> Dict[str, Any]:
    p = pathlib.Path(path); p.mkdir(parents=True, exist_ok=True)
    return {"ok": True, "path": str(p)}

def write_file(path: str, content: str, create_dirs: bool = True) -> Dict[str, Any]:
    p = pathlib.Path(path)
    if create_dirs: p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return {"ok": True, "path": str(p), "size": len(content)}

def read_file(path: str) -> Dict[str, Any]:
    p = pathlib.Path(path)
    return {"ok": p.exists(), "path": str(p), "content": p.read_text(encoding="utf-8") if p.exists() else ""}

def list_dir(path: str) -> Dict[str, Any]:
    p = pathlib.Path(path)
    if not p.exists(): return {"ok": False, "error": "Путь не существует"}
    items=[{"name":x.name,"is_dir":x.is_dir(),"size":x.stat().st_size} for x in p.iterdir()]
    return {"ok": True, "items": items}

def run_cmd(cmd: str, cwd: str | None = None, timeout: int = 900) -> Dict[str, Any]:
    parts = shlex.split(cmd)
    if not parts or parts[0] not in ALLOWED:
        return {"ok": False, "error": f"Команда '{parts[0] if parts else ''}' не разрешена"}
    try:
        res = subprocess.run(parts, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return {"ok": res.returncode==0, "code": res.returncode, "stdout": res.stdout, "stderr": res.stderr}
    except Exception as e:
        return {"ok": False, "error": str(e)}

TOOL_SPEC = [
    {"name":"ensure_dir","description":"Создать каталог","schema":{"path":"str"}},
    {"name":"write_file","description":"Записать текстовый файл","schema":{"path":"str","content":"str","create_dirs":"bool"}},
    {"name":"read_file","description":"Прочитать файл","schema":{"path":"str"}},
    {"name":"list_dir","description":"Список каталога","schema":{"path":"str"}},
    {"name":"run_cmd","description":"Выполнить команду (белый список)","schema":{"cmd":"str","cwd":"str"}},
]
