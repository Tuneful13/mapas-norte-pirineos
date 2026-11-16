#!/usr/bin/env bash
# Genera los mapas offline de la app (PMTiles):
#   data/mapa-base.pmtiles  mapa base (esquema OpenMapTiles) desde OpenStreetMap
#   data/curvas.pmtiles     curvas de nivel cada 10 m desde Copernicus GLO-30
# Zona: Cantabria, La Rioja, País Vasco, Navarra y todo el Pirineo (ver area.py).
#
# Requisitos: Java 21+, Python 3, conda, curl. Ejecutar desde esta carpeta.
set -euo pipefail
cd "$(dirname "$0")"

SRC=data/sources
ZONE="$SRC/zona.poly"
# Extractos de Geofabrik que tocan la zona (ruta bajo download.geofabrik.de/europe/)
EXTRACTS=(spain/cantabria spain/la-rioja spain/pais-vasco spain/navarra spain/aragon
          spain/cataluna andorra france/aquitaine france/midi-pyrenees
          france/languedoc-roussillon)
mkdir -p "$SRC" data/dem data/clip

# 1. Herramientas: Planetiler, osmium (unir/recortar OSM) y Python
[ -f planetiler.jar ] || curl -sSfL -o planetiler.jar \
  https://github.com/onthegomap/planetiler/releases/latest/download/planetiler.jar
[ -x .conda/bin/osmium ] || CONDA_PKGS_DIRS="${TMPDIR:-/tmp}/conda-pkgs" \
  conda create -y -q -p ./.conda -c conda-forge --override-channels osmium-tool gh
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q shapely rasterio contourpy scipy numpy

# 2. Contorno de la zona (necesita los .poly de Geofabrik de las 4 comunidades)
for r in cantabria la-rioja pais-vasco navarra; do
  [ -f "$SRC/$r.poly" ] || curl -sSfL -o "$SRC/$r.poly" "https://download.geofabrik.de/europe/spain/$r.poly"
done
BOUNDS=$(.venv/bin/python area.py "$ZONE")
echo "Zona: $BOUNDS"

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

JAVA=(java -Xmx6g -Djava.io.tmpdir="${TMPDIR:-/tmp}" -jar planetiler.jar)

# 5. Mapa base (zoom 0-14; la app sobreamplía a 15-18)
"${JAVA[@]}" \
  --osm_path="$SRC/zona.osm.pbf" \
  --bounds="$BOUNDS" \
  --polygon="$ZONE" \
  --maxzoom=14 \
  --output=data/mapa-base.pmtiles \
  --force

# 6. Curvas de nivel: modelo de elevación (cuadrículas de 1°) -> GeoJSON -> PMTiles
read -r W S E N < <(echo "$BOUNDS" | tr ',' ' ')
lat_tiles() { python3 -c "import math;print(' '.join(f'N{l:02d}' for l in range(math.floor($S), math.ceil($N))))"; }
lon_tiles() { python3 -c "import math;print(' '.join((f'W{-l:03d}' if l<0 else f'E{l:03d}') for l in range(math.floor($W), math.ceil($E))))"; }
for lat in $(lat_tiles); do for lon in $(lon_tiles); do
  n="Copernicus_DSM_COG_10_${lat}_00_${lon}_00_DEM"
  [ -f "data/dem/$n.tif" ] || curl -sSfL -o "data/dem/$n.tif" \
    "https://copernicus-dem-30m.s3.amazonaws.com/$n/$n.tif" || echo "Sin datos: $n (mar)"
done; done
.venv/bin/python contours.py data/contours.geojson "$ZONE" 10

"${JAVA[@]}" generate-custom \
  --schema=contours.yml \
  --polygon="$ZONE" \
  --maxzoom=14 \
  --output=data/curvas.pmtiles \
  --force

ls -lh data/mapa-base.pmtiles data/curvas.pmtiles
