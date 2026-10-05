#!/usr/bin/env bash
# Start the stack on free ports and open the frontend in the browser.
set -euo pipefail
cd "$(dirname "$0")"

docker compose up --build -d

frontend_port=$(docker compose port frontend 5173 | head -n1 | sed 's/.*://')
backend_port=$(docker compose port backend 8000 | head -n1 | sed 's/.*://')
url="http://localhost:${frontend_port}"

printf 'Waiting for frontend'
until curl -sf -o /dev/null "$url"; do printf '.'; sleep 1; done
echo

echo "Frontend: $url"
echo "API docs: http://localhost:${backend_port}/docs"
echo "Stop with: docker compose down"

case "$(uname -s)" in
  Darwin) open "$url" ;;
  Linux) xdg-open "$url" >/dev/null 2>&1 || true ;;
  MINGW*|MSYS*|CYGWIN*) start "$url" ;;
esac
