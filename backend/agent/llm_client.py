import requests, json
from .config import settings

def call_llm(prompt: str) -> str:
    payload={"model":settings.llm_model,"prompt":prompt,"stream":False}
    r = requests.post(settings.llm_endpoint, json=payload, timeout=120)
    r.raise_for_status()
    out = r.json()
    return out.get("response") or out.get("text") or str(out)

def chat_llm(system_prompt: str, history: list[dict]):
    payload={"model":settings.llm_model,"prompt": system_prompt + "\n" + _history_to_text(history), "stream": False}
    r = requests.post(settings.llm_endpoint, json=payload, timeout=120)
    r.raise_for_status()
    out = r.json()
    return out.get("response") or out.get("text") or str(out)

def _history_to_text(h):
    lines=[]; 
    for m in h[-12:]:
        lines.append(f"{m['role']}: {m['content']}")
    return "\n".join(lines)
