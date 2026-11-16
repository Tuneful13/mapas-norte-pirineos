"""Escribe el catálogo de zonas que lee la app para ofrecer las descargas.

Uso: python catalog.py TAG > data/zonas/catalogo.json

TAG es la Release de GitHub donde se suben los archivos de data/zonas/.
La app descarga siempre el catálogo de la última Release:
  https://github.com/<repo>/releases/latest/download/catalogo.json
y de ahí saca las URLs (con su TAG) de cada archivo.

Formato:
{
  "formato": 1,
  "version": TAG,
  "zonas": [
    {"id": "navarra", "nombre": "Navarra", "caja": [oeste, sur, este, norte],
     "base":   {"url": "...", "bytes": 123},
     "curvas": {"url": "...", "bytes": 456}},
    ...
  ]
}
"""

import json
import os
import sys

from area import zones

REPO = "Tuneful13/mapas-norte-pirineos"
DIR = "data/zonas"


def asset(tag, name):
    path = f"{DIR}/{name}"
    return {
        "url": f"https://github.com/{REPO}/releases/download/{tag}/{name}",
        "bytes": os.path.getsize(path),
    }


def main():
    tag = sys.argv[1]
    out = {"formato": 1, "version": tag, "zonas": []}
    for zid, name, shape in zones():
        w, s, e, n = shape.bounds
        out["zonas"].append({
            "id": zid,
            "nombre": name,
            "caja": [round(w, 3), round(s, 3), round(e, 3), round(n, 3)],
            "base": asset(tag, f"{zid}-base.pmtiles"),
            "curvas": asset(tag, f"{zid}-curvas.pmtiles"),
        })
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
