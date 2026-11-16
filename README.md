# Mapas offline: norte de España y Pirineos

Mapas vectoriales para usar sin conexión, en formato [PMTiles](https://docs.protomaps.com/pmtiles/),
divididos en zonas que se descargan por separado:

| Zona | Cobertura |
|---|---|
| Cantabria | Comunidad completa |
| La Rioja | Comunidad completa |
| País Vasco | Comunidad completa |
| Navarra | Comunidad completa |
| Pirineo aragonés | Parte pirenaica de Aragón (Jaca, Huesca, Benasque...) |
| Pirineo catalán | Parte pirenaica de Cataluña (Vall d'Aran, Berga, Olot, Girona...) |
| Andorra | País completo |
| Pirineo francés | De Hendaya a Perpiñán, con el prepirineo (Pau, Lourdes, Foix...) |

Los archivos están en las [Releases](../../releases). Cada zona tiene dos:

- `<zona>-base.pmtiles`: mapa base de OpenStreetMap (esquema OpenMapTiles), zoom 0-14.
- `<zona>-curvas.pmtiles`: curvas de nivel cada 10 m (capa `contour`), zoom 10-14.

Y cada Release incluye `catalogo.json` con la lista de zonas, sus tamaños y URLs. La URL
`https://github.com/Tuneful13/mapas-norte-pirineos/releases/latest/download/catalogo.json`
apunta siempre al catálogo de la última Release.

Las zonas vecinas se solapan ~1 km para que no queden huecos al combinarlas.

## Curvas de nivel

- Capa `contour` con los atributos `ele` (altitud en metros) y `nivel`: `"100"` en las curvas maestras
  (visibles desde zoom 10), `"50"` en las intermedias (desde zoom 12) y `"10"` en el resto (desde zoom 13).
- Copernicus GLO-30 es un modelo de *superficie*: incluye árboles y edificios. Por eso se suaviza
  ligeramente antes de calcular las curvas, y en bosques o pueblos pueden ir algo desplazadas
  respecto al terreno.

## Licencias y atribución

Quien use estos mapas debe mostrar:

- Mapa base: **© OpenStreetMap contributors** (datos bajo [ODbL](https://www.openstreetmap.org/copyright))
  y **© OpenMapTiles** ([CC-BY 4.0](https://github.com/openmaptiles/openmaptiles/blob/master/LICENSE.md)).
- Curvas de nivel: **© Copernicus DEM GLO-30**, producido con datos de © DLR e.V. 2010-2014 y
  © Airbus Defence and Space GmbH 2014-2018, proporcionados en el marco de COPERNICUS por la Unión
  Europea y la ESA.

## Ver los mapas

Abre `visor.html` en el navegador y elige un `-base.pmtiles` y después su `-curvas.pmtiles`
(opcionalmente, una ruta `.gpx`). No necesita servidor; solo conexión para cargar MapLibre y las fuentes.

## Regenerar los mapas

```bash
./build.sh [TAG]
```

Descarga los datos más recientes y genera en `data/zonas/` los archivos de cada zona y
`catalogo.json` (con las URLs de la Release `TAG`; por defecto `mapas-AAAA-MM-DD`).
Después hay que subir todo `data/zonas/*.pmtiles` y `data/zonas/catalogo.json` a esa Release.

Requisitos: Java 21+, Python 3, conda y curl. Usa unos 6 GB de memoria y deja ~4 GB de datos
intermedios en `data/` (extractos de OSM, modelo de elevación y datos auxiliares de Planetiler).
Tarda unos 30 minutos, más las descargas (~3 GB la primera vez).

| Archivo | Qué hace |
|---|---|
| `build.sh` | Todo el proceso |
| `area.py` | Contornos: la zona total y cada zona descargable (`ZONES`) |
| `contours.py` | Curvas de nivel desde el modelo de elevación |
| `contours.yml` | Esquema de [Planetiler](https://github.com/onthegomap/planetiler) para las curvas |
| `catalog.py` | Escribe `catalogo.json` |
| `visor.html` | Visor local con MapLibre GL JS |

Fuentes: extractos de [Geofabrik](https://download.geofabrik.de/) (Cantabria, La Rioja, País Vasco,
Navarra, Aragón, Cataluña, Andorra, Aquitaine, Midi-Pyrénées, Languedoc-Roussillon), recortados
con [osmium](https://osmcode.org/osmium-tool/), y [Copernicus GLO-30](https://registry.opendata.aws/copernicus-dem/).

## Limitaciones

- Sin sombreado de relieve.
- Fuera de estas zonas no hay mapa.
- Las zonas del Pirineo se recortan con una franja rectangular con algo de margen: incluyen parte
  del llano a ambos lados (por ejemplo Huesca, Pau, Perpiñán o Narbona).
