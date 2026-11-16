"""Construye el contorno de la zona del mapa (archivo .poly de Osmosis).

Uso: python area.py salida.poly

Zona: Cantabria, La Rioja, País Vasco y Navarra (límites de Geofabrik)
más una franja que cubre todo el Pirineo, lado español, Andorra y lado
francés, de Hendaya al cabo de Creus. Se calcula la unión real para que
no haya solapes (osmium trataría un solape como un hueco).
Imprime la caja envolvente, que usan contours.py y build.sh.
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


def main():
    out = sys.argv[1]
    parts = [read_poly(f"data/sources/{r}.poly") for r in REGIONS]
    parts.append(box(*PYRENEES))
    # Pequeño margen (~1 km) para no cortar caminos justo en la frontera.
    area = unary_union(parts).buffer(0.01).simplify(0.002)
    write_poly(area, out)
    w, s, e, n = area.bounds
    print(f"{w:.2f},{s:.2f},{e:.2f},{n:.2f}")


if __name__ == "__main__":
    main()
