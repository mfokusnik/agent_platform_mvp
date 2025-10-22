# Агент‑студия v5 — объединение UX (v4) и функционала (v3)

**Что входит:**
- Чат (WebSocket), История, Список задач (CRUD, статусы).
- Расписание (ночной режим) + понятные статусы `idle/running/sleeping`.
- Поток логов (SSE): планы, действия, коммиты, объяснения.
- RAG‑контекст и `.agent/context.md` для понятного обзора файлов.
- Полностью русскоязычный интерфейс и формулировки «без жаргона».

## Запуск
### Локально
```
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS:
. .venv/bin/activate
pip install -r requirements.txt
cp .env.sample .env
uvicorn app:app --host 0.0.0.0 --port 8080 --reload
```
UI: `http://localhost:8080/ui`

### Docker
```
docker compose up --build
```
UI: `http://localhost:8096/ui`

## Основные API
- `POST /projects` — создать проект
- `GET  /projects/{id}` — статус
- `POST /projects/{id}/run` — запустить шаг
- `GET  /projects/{id}/chat/history` — история чата
- `WS   /ws/{id}` — чат в реальном времени
- `GET  /projects/{id}/tasks` — список задач
- `POST /projects/{id}/tasks` — добавить задачу
- `PATCH /projects/{id}/tasks/{tid}` — обновить
- `POST /projects/{id}/schedule` — расписание
- `GET  /stream/{id}` — поток логов

## Заметки
- LLM должна отвечать на русском для лучшего UX (можно настроить в модели).
- Команды, установки и тесты выполняются через инструмент `run_cmd` (белый список).
- Рекомендуется запускать в контейнере и монтировать только каталог рабочих проектов.
