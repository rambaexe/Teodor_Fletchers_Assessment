# Document Ingestion Pipeline - Fletchers Assessment

- Uploading `.pdf` / `.docx` files
- Extracting and stopring their content
- Retrieving it through a web UI and REST API.


- Brief: [BRIEFING.md](BRIEFING.md)
- Written answers: [Follow-Up Questions.md](Follow-Up%20Questions.md)

## Running

### Option 1: Docker

```bash
./start.sh
```

Docker picks free ports. The script prints the URLs and opens the app in your browser. On Windows, run it from Git Bash. Stop with `docker compose down`.

### Option 2: Locally (uv + npm)

Requires Python 3.10+, [uv](https://docs.astral.sh/uv/getting-started/installation/) and Node 20+.

```bash
cd backend
uv run uvicorn app.main:app --reload
```

```bash
cd frontend
npm install
npm run dev
```

Open the URL Vite prints.