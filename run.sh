#!/usr/bin/env bash
# Sobe o agente de terminal.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export AGENTE_BASE="$DIR"
exec "$DIR/.venv/bin/python" "$DIR/agente.py" "$@"
