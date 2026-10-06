# Document Ingestion Pipeline - Fletchers Assessment

- Uploading `.pdf` / `.docx` files

- Extracting and store their content, and retrieve it through a web UI and REST API.


- Brief: [BRIEFING.md](BRIEFING.md)
- Written answers: [Follow-Up Questions.md](Follow-Up%20Questions.md)

**Stack:** Python + FastAPI (backend), React + TypeScript + Vite (frontend).

## Running

### Option 1: Docker

```bash
./start.sh
```

Docker picks free ports. The script prints the URLs and opens the app in your browser. On Windows, run it from Git Bash. Stop with `docker compose down`.

### Option 2: Locally (uv + npm)

Requires Python 3.10+, [uv](https://docs.astral.sh/uv/getting-started/installation/) and Node 20+.

From the repo root:

```bash
npm install   # installs frontend + backend deps
npm run dev   # starts both, live reload
```

Open http://localhost:5173 (or the next free port Vite prints). Ctrl+C stops both.

Tests: `npm test`
