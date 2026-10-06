# Document Ingestion Pipeline - Fletchers Assessment

- Uploading `.pdf` / `.docx` files
- Extracting and storing their content
- Retrieving it through a web UI and REST API

## 1. Answers to Follow-up questions

**[FOLLOWUP_QUESTIONS.md](FOLLOWUP_QUESTIONS.md)** 

Other files:
- Brief: [BRIEFING.md](BRIEFING.md)
- Architecture + pipeline flow: [ARCHITECTURE.md](ARCHITECTURE.md)

## 2. How to run

**Stack:** Python + FastAPI (backend), React + TypeScript + Vite (frontend), SQLite (storage).

Requires Python 3.10+, [uv](https://docs.astral.sh/uv/getting-started/installation/) and Node 20+. From the repo root:

```bash
npm install
npm run dev
```

- `npm install` installs frontend + backend dependencies
- `npm run dev` starts both with live reload, in one terminal
- Open the URL Vite prints (http://localhost:5173 or the next free port); Ctrl+C stops both
- API docs: http://localhost:8000/docs
