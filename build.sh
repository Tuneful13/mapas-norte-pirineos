#!/usr/bin/env bash
# Genera los mapas offline por zonas (PMTiles) y el catálogo que lee la app:
#   data/zonas/<zona>-base.pmtiles    mapa base (OpenStreetMap, esquema OpenMapTiles)
#   data/zonas/<zona>-curvas.pmtiles  curvas de nivel cada 10 m (Copernicus GLO-30)
#   data/zonas/catalogo.json          lista de zonas con tamaños y URLs
# Zonas: ver ZONES en area.py.
#
# Uso: ./build.sh [TAG]   (TAG de la Release de GitHub; por defecto mapas-AAAA-MM-DD)
# Requisitos: Java 21+, Python 3, conda, curl. Ejecutar desde esta carpeta.
set -euo pipefail
cd "$(dirname "$0")"

TAG="${1:-mapas-$(date +%F)}"
SRC=data/sources
ZONE="$SRC/zona.poly"
POLYS=data/zonas-poly
OUT=data/zonas
# Extractos de Geofabrik que tocan la zona (ruta bajo download.geofabrik.de/europe/)
EXTRACTS=(spain/cantabria spain/la-rioja spain/pais-vasco spain/navarra spain/aragon
          spain/cataluna andorra france/aquitaine france/midi-pyrenees
          france/languedoc-roussillon)
# Contornos de Geofabrik que usa area.py
POLYS_GEOFABRIK=(spain/cantabria spain/la-rioja spain/pais-vasco spain/navarra
                 spain/aragon spain/cataluna andorra france)
mkdir -p "$SRC" data/dem data/clip "$POLYS" "$OUT"

# 1. Herramientas: Planetiler, osmium (unir/recortar OSM) y Python
[ -f planetiler.jar ] || curl -sSfL -o planetiler.jar \
  https://github.com/onthegomap/planetiler/releases/latest/download/planetiler.jar
[ -x .conda/bin/osmium ] || CONDA_PKGS_DIRS="${TMPDIR:-/tmp}/conda-pkgs" \
  conda create -y -q -p ./.conda -c conda-forge --override-channels osmium-tool gh
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q shapely rasterio contourpy scipy numpy

# 2. Contornos: zona total y cada zona descargable
for p in "${POLYS_GEOFABRIK[@]}"; do
  n=$(basename "$p")
  [ -f "$SRC/$n.poly" ] || curl -sSfL -o "$SRC/$n.poly" "https://download.geofabrik.de/europe/$p.poly"
done
BOUNDS=$(.venv/bin/python area.py "$ZONE")
.venv/bin/python area.py --zonas "$POLYS" > "$POLYS/lista.txt"
echo "Zona total: $BOUNDS"

# 3. Extractos OSM (siempre la versión más reciente), recortados a la zona y unidos
clipped=()
for e in "${EXTRACTS[@]}"; do
  n=$(basename "$e")
  curl -sSfL -o "$SRC/$n.osm.pbf" "https://download.geofabrik.de/europe/$e-latest.osm.pbf"
  .conda/bin/osmium extract --overwrite -s smart -p "$ZONE" "$SRC/$n.osm.pbf" -o "data/clip/$n.osm.pbf"
  clipped+=("data/clip/$n.osm.pbf")
done
.conda/bin/osmium merge --overwrite "${clipped[@]}" -o "$SRC/zona.osm.pbf"

# 4. Datos auxiliares de Planetiler (mar, Natural Earth, lagos); solo se bajan una vez
dl() { [ -f "$SRC/$1" ] || curl -sSfL -o "$SRC/$1" "$2"; }
dl water-polygons-split-3857.zip https://osmdata.openstreetmap.de/download/water-polygons-split-3857.zip
dl natural_earth_vector.sqlite.zip https://naciscdn.org/naturalearth/packages/natural_earth_vector.sqlite.zip
dl lake_centerline.shp.zip https://github.com/acalcutt/osm-lakelines/releases/download/v12/lake_centerline.shp.zip

# 5. Modelo de elevación (cuadrículas de 1°) de toda la zona
read -r W S E N < <(echo "$BOUNDS" | tr ',' ' ')
lat_tiles() { python3 -c "import math;print(' '.join(f'N{l:02d}' for l in range(math.floor($S), math.ceil($N))))"; }
lon_tiles() { python3 -c "import math;print(' '.join((f'W{-l:03d}' if l<0 else f'E{l:03d}') for l in range(math.floor($W), math.ceil($E))))"; }
for lat in $(lat_tiles); do for lon in $(lon_tiles); do
  n="Copernicus_DSM_COG_10_${lat}_00_${lon}_00_DEM"
  [ -f "data/dem/$n.tif" ] || curl -sSfL -o "data/dem/$n.tif" \
    "https://copernicus-dem-30m.s3.amazonaws.com/$n/$n.tif" || echo "Sin datos: $n (mar)"
done; done

JAVA=(java -Xmx6g -Djava.io.tmpdir="${TMPDIR:-/tmp}" -jar planetiler.jar)

# 6. Cada zona: OSM recortado -> mapa base; elevación -> curvas
while IFS='|' read -r id name bounds <&3; do
  echo "== $name ($id)"
  .conda/bin/osmium extract --overwrite -s smart -p "$POLYS/$id.poly" \
    "$SRC/zona.osm.pbf" -o "data/clip/zona-$id.osm.pbf"
  "${JAVA[@]}" \
    --osm_path="data/clip/zona-$id.osm.pbf" \
    --bounds="$bounds" \
    --polygon="$POLYS/$id.poly" \
    --maxzoom=14 \
    --output="$OUT/$id-base.pmtiles" \
    --force > "$OUT/$id-base.log" 2>&1

  .venv/bin/python contours.py data/contours.geojson "$POLYS/$id.poly" 10
  "${JAVA[@]}" generate-custom \
    --schema=contours.yml \
    --polygon="$POLYS/$id.poly" \
    --maxzoom=14 \
    --output="$OUT/$id-curvas.pmtiles" \
    --force > "$OUT/$id-curvas.log" 2>&1
done 3< "$POLYS/lista.txt"
rm -f data/contours.geojson

# 7. Catálogo para la app
.venv/bin/python catalog.py "$TAG" > "$OUT/catalogo.json"
ls -lh "$OUT"/*.pmtiles "$OUT/catalogo.json"
echo "Sube data/zonas/*.pmtiles y data/zonas/catalogo.json a la Release $TAG"
