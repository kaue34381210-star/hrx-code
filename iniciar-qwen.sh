#!/usr/bin/env bash
# Inicia o Qwen GGUF com o servidor HTTP compatível com OpenAI do llamafile.
set -euo pipefail

DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

# Portável por padrão:
# - HRX_LLAMAFILE / HRX_MODELO_GGUF podem sobrescrever.
# - Sem env, procura binário e modelo ao lado do script ou em ./bin.
LLAMAFILE="${HRX_LLAMAFILE:-$DIR/llamafile}"
MODELO="${HRX_MODELO_GGUF:-$DIR/modelo.gguf}"
PORTA="${HRX_PORTA:-8080}"
CONTEXTO="${HRX_CONTEXTO:-4096}"

if [ ! -x "$LLAMAFILE" ] && [ -x "$DIR/bin/llamafile" ]; then
    LLAMAFILE="$DIR/bin/llamafile"
fi
if [ ! -f "$MODELO" ] && [ -f "$DIR/bin/modelo.gguf" ]; then
    MODELO="$DIR/bin/modelo.gguf"
fi

if [ ! -x "$LLAMAFILE" ]; then
    echo "Erro: llamafile não encontrado ou não executável: $LLAMAFILE" >&2
    echo "Defina HRX_LLAMAFILE apontando para o binário do llamafile." >&2
    exit 1
fi
if [ ! -f "$MODELO" ]; then
    echo "Erro: modelo GGUF não encontrado: $MODELO" >&2
    echo "Defina HRX_MODELO_GGUF apontando para o arquivo .gguf." >&2
    exit 1
fi

echo "Iniciando Qwen local em http://127.0.0.1:$PORTA"
echo "Modelo: $MODELO"
exec "$LLAMAFILE" --server --port "$PORTA" -c "$CONTEXTO" -m "$MODELO"
