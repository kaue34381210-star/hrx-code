#!/usr/bin/env bash
# Remove o JARVIS. Por padrão preserva suas chaves; use --tudo para apagar também.
set -e

CMD="jarvis"
DEST="$HOME/.local/share/jarvis"
BIN="$HOME/.local/bin"
CFG="$HOME/.config/jarvis"

echo "Removendo JARVIS..."
rm -f "$BIN/$CMD"
rm -rf "$DEST"
echo "  comando e código removidos."

if [ "$1" = "--tudo" ]; then
    rm -rf "$CFG"
    echo "  chaves e config removidas (--tudo)."
else
    echo "  chaves preservadas em $CFG (use --tudo para apagar)."
fi
echo "✅ desinstalado."
