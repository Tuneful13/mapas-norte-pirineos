"""Contornos de los mapas (archivos .poly de Osmosis).

Uso:
  python area.py salida.poly    contorno total; imprime su caja envolvente
  python area.py --zonas DIR    DIR/<id>.poly de cada zona descargable;
                                imprime "id|nombre|caja" por línea

Zona total: Cantabria, La Rioja, País Vasco y Navarra (límites de Geofabrik)
más una franja que cubre todo el Pirineo, lado español, Andorra y lado
francés, de Hendaya al cabo de Creus. Se calcula la unión real para que
no haya solapes (osmium trataría un solape como un hueco).
Zonas descargables: ver ZONES.
"""

import sys

from shapely.geometry import MultiPolygon, Polygon, box
from shapely.ops import unary_union

REGIONS = ["cantabria", "la-rioja", "pais-vasco", "navarra"]

# Franja del Pirineo (lon oeste, lat sur, lon este, lat norte). Deja algo de
# prepirineo a ambos lados: Jaca, Huesca, Berga, Olot; Pau, Lourdes, Foix,
# Perpiñán. Las ciudades del llano (Zaragoza, Lleida, Toulouse) quedan fuera.
PYRENEES = (-1.85, 41.95, 3.35, 43.40)


def read_poly(path):
    """Lee un .poly de Geofabrik: anillos exteriores y huecos (con '!')."""
    outers, holes = [], []
    with open(path) as f:
        lines = [l.strip() for l in f if l.strip()]
    i = 1  # la primera línea es el nombre
    while i < len(lines) and lines[i] != "END":
        name = lines[i]
        i += 1
        ring = []
        while lines[i] != "END":
            lon, lat = map(float, lines[i].split()[:2])
            ring.append((lon, lat))
            i += 1
        i += 1
        (holes if name.startswith("!") else outers).append(Polygon(ring))
    shape = unary_union(outers)
    for h in holes:
        shape = shape.difference(h)
    return shape


def write_poly(shape, path):
    polys = shape.geoms if isinstance(shape, MultiPolygon) else [shape]
    n = 0
    with open(path, "w") as f:
        f.write("zona\n")
        for p in polys:
            n += 1
            f.write(f"{n}\n")
            for lon, lat in p.exterior.coords:
                f.write(f"   {lon:.6f}   {lat:.6f}\n")
            f.write("END\n")
            for hole in p.interiors:
                n += 1
                f.write(f"!{n}\n")
                for lon, lat in hole.coords:
                    f.write(f"   {lon:.6f}   {lat:.6f}\n")
                f.write("END\n")
        f.write("END\n")


# Zonas que se descargan por separado en la app:
# (id, nombre, .poly de Geofabrik, ¿recortar a la franja del Pirineo?)
ZONES = [
    ("cantabria", "Cantabria", "cantabria", False),
    ("la-rioja", "La Rioja", "la-rioja", False),
    ("pais-vasco", "País Vasco", "pais-vasco", False),
    ("navarra", "Navarra", "navarra", False),
    ("pirineo-aragones", "Pirineo aragonés", "aragon", True),
    ("pirineo-catalan", "Pirineo catalán", "cataluna", True),
    ("andorra", "Andorra", "andorra", False),
    ("pirineo-frances", "Pirineo francés", "france", True),
]


def _finish(shape):
    # Pequeño margen (~1 km) para no cortar caminos justo en la frontera y
    # que las zonas vecinas se solapen un poco (sin huecos entre ellas).
    return shape.buffer(0.01).simplify(0.002)


def _bounds(shape):
    w, s, e, n = shape.bounds
    return f"{w:.2f},{s:.2f},{e:.2f},{n:.2f}"


def zones():
    """[(id, nombre, forma)] de cada zona descargable."""
    band = box(*PYRENEES)
    out = []
    for zid, name, poly, clip in ZONES:
        shape = read_poly(f"data/sources/{poly}.poly")
        if clip:
            shape = shape.intersection(band)
        out.append((zid, name, _finish(shape)))
    return out


def main():
    """
    python area.py zona.poly      -> contorno total; imprime su caja
    python area.py --zonas DIR    -> DIR/<id>.poly de cada zona; imprime
                                     "id|nombre|caja" por línea
    """
    if len(sys.argv) == 3 and sys.argv[1] == "--zonas":
        outdir = sys.argv[2]
        for zid, name, shape in zones():
            write_poly(shape, f"{outdir}/{zid}.poly")
            print(f"{zid}|{name}|{_bounds(shape)}")
        return
    out = sys.argv[1]
    parts = [read_poly(f"data/sources/{r}.poly") for r in REGIONS]
    parts.append(box(*PYRENEES))
    area = _finish(unary_union(parts))
    write_poly(area, out)
    print(_bounds(area))


if __name__ == "__main__":
    main()
