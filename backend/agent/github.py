import pathlib
from git import Repo
from typing import Optional

def init_repo(workspace_path: str, remote_url: Optional[str], token: Optional[str]) -> str:
    wp = pathlib.Path(workspace_path)
    repo = Repo.init(wp) if not (wp / ".git").exists() else Repo(wp)
    if remote_url:
        if token and remote_url.startswith("https://") and f"{token}@" not in remote_url:
            remote_url = remote_url.replace("https://", f"https://{token}@")
        try:
            if "origin" in [r.name for r in repo.remotes]:
                repo.delete_remote("origin")
            repo.create_remote("origin", remote_url)
        except Exception:
            pass
    return str(repo.working_dir)

def new_branch(workspace_path: str, branch_name: str) -> str:
    repo = Repo(workspace_path)
    head = repo.create_head(branch_name) if branch_name not in repo.heads else repo.heads[branch_name]
    head.checkout()
    return head.name

def commit_all(workspace_path: str, message: str) -> str:
    repo = Repo(workspace_path)
    repo.git.add(A=True)
    if repo.is_dirty():
        repo.index.commit(message)
        return "committed"
    return "nothing_to_commit"

def push_current(workspace_path: str, set_upstream: bool = True) -> str:
    repo = Repo(workspace_path)
    current = repo.active_branch.name
    if set_upstream:
        repo.git.push("--set-upstream", "origin", current)
    else:
        repo.git.push("origin", current)
    return current
