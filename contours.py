"""Calcula curvas de nivel desde el modelo de elevación Copernicus GLO-30.

Uso: python contours.py salida.geojson zona.poly [intervalo_m]

Lee las cuadrículas de data/dem/*.tif, las une en la caja de la zona,
descarta lo que queda fuera del contorno (zona.poly, de area.py), suaviza
un poco el relieve y escribe una LineString por curva con:
  ele   = altitud en metros
  nivel = "100" (maestra), "50" (intermedia) o "10" (normal); decide
          a partir de qué zoom se ve cada curva (ver contours.yml).
"""

import glob
import json
import sys

import contourpy
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.merge import merge
from scipy.ndimage import gaussian_filter

from area import read_poly

# Copernicus GLO-30 a estas latitudes: 1" en latitud y 1,5" en longitud.
RES = (1.5 / 3600, 1 / 3600)
# Copernicus es un modelo de superficie (incluye árboles y edificios):
# un suavizado ligero evita curvas "dentadas" en bosques y pueblos.
SIGMA_PX = 1.5
MIN_POINTS = 8  # descarta curvitas sueltas de ruido


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    out, poly_path = sys.argv[1], sys.argv[2]
    step = int(sys.argv[3]) if len(sys.argv) > 3 else 10

    zone = read_poly(poly_path)
    srcs = [rasterio.open(f) for f in sorted(glob.glob("data/dem/*.tif"))]
    mosaic, tr = merge(srcs, bounds=zone.bounds, res=RES, dtype="float32")
    del srcs
    z = gaussian_filter(mosaic[0], SIGMA_PX)
    del mosaic
    h, w = z.shape

    # Fuera de la zona no hay curvas (NaN = sin datos para contourpy).
    outside = geometry_mask([zone], out_shape=(h, w), transform=tr)
    z[outside] = np.nan
    del outside

    # Centros de píxel en lon/lat; se invierte para que la latitud sea creciente.
    x = tr.c + (np.arange(w) + 0.5) * tr.a
    y = tr.f + (np.arange(h) + 0.5) * tr.e
    z, y = z[::-1], y[::-1]

    gen = contourpy.contour_generator(x, y, z, line_type="Separate")
    top = int(np.nanmax(z))
    n = 0
    with open(out, "w") as f:
        f.write('{"type":"FeatureCollection","features":[\n')
        first = True
        for ele in range(step, top + 1, step):
            nivel = "100" if ele % 100 == 0 else "50" if ele % 50 == 0 else "10"
            for line in gen.lines(ele):
                if len(line) < MIN_POINTS:
                    continue
                coords = np.round(line, 5).tolist()
                feat = {
                    "type": "Feature",
                    "properties": {"ele": ele, "nivel": nivel},
                    "geometry": {"type": "LineString", "coordinates": coords},
                }
                f.write(("" if first else ",\n") + json.dumps(feat, separators=(",", ":")))
                first = False
                n += 1
        f.write("\n]}\n")
    print(f"{n} curvas, de {step} a {top} m, malla {w}x{h}")


if __name__ == "__main__":
    main()
