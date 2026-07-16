#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

ffmpeg -hide_banner -loglevel error -y \
  -f lavfi -i "color=c=0x0d1117:s=1200x675:d=15:r=15" \
  -filter_complex \
  "[0:v]subtitles=docs/demo.ass,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=3" \
  -loop 0 docs/demo.gif

echo "Demonstração criada em docs/demo.gif"
