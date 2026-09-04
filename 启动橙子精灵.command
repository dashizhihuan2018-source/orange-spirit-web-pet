#!/bin/bash
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
MCP_DIR="$ROOT/MCP插件"
[ -d "$MCP_DIR" ] || MCP_DIR="$ROOT/mcp"
node "$MCP_DIR/build/server.js" >/tmp/orange-spirit-mcp.stdout 2>/tmp/orange-spirit-mcp.stderr &
MCP_PID=$!
python3 -m http.server 5190 --bind 127.0.0.1 >/tmp/orange-spirit-web.log 2>&1 &
WEB_PID=$!
trap 'kill "$MCP_PID" "$WEB_PID" 2>/dev/null || true' EXIT INT TERM
open "http://127.0.0.1:5190/standalone-demo.html"
wait "$WEB_PID"
