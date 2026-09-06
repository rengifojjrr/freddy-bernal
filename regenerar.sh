#!/bin/sh
# Regenera informe.html de principio a fin.
#
# El orden importa: los colores de las barras se escriben DENTRO de
# graficos.json, así que muestrear_colores.py tiene que ejecutarse después de
# normalizar_graficos.py, que reescribe ese archivo por completo.
#
#   ./regenerar.sh                      solo reconstruye el HTML
#   ./regenerar.sh --todo <journal>     rehace también contenido y gráficos
set -e
cd "$(dirname "$0")"

if [ "$1" = "--todo" ]; then
  echo "== 1/4  DOCX + XLSX  ->  contenido.json y capturas/"
  python3 extraer_contenido.py informe.docx matriz.xlsx

  if [ -n "$2" ]; then
    echo
    echo "== 2/4  journal del flujo  ->  graficos.json"
    python3 normalizar_graficos.py "$2"
  else
    echo
    echo "== 2/4  omitido: no se indicó journal.jsonl, se conserva graficos.json"
  fi

  echo
  echo "== 3/4  PNG originales  ->  color real de cada barra"
  python3 -c "import muestrear_colores as m; m.main(); m.aplicar()"
  echo
fi

echo "== 4/4  contenido.json + capturas/ + graficos.json  ->  informe.html"
python3 build.py
