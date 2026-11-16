# Mapas offline: norte de España y Pirineos

Mapas vectoriales para usar sin conexión, en formato [PMTiles](https://docs.protomaps.com/pmtiles/).
Cubren **Cantabria, La Rioja, País Vasco, Navarra y todo el Pirineo** (lado español, Andorra y lado
francés, de Hendaya al cabo de Creus).

Los archivos están en las [Releases](../../releases) de este repositorio:

| Archivo | Contenido | Tamaño |
|---|---|---|
| `mapa-base.pmtiles` | Mapa base de OpenStreetMap (esquema OpenMapTiles), zoom 0-14 | ~408 MB |
| `curvas.pmtiles` | Curvas de nivel cada 10 m (capa `contour`), zoom 10-14 | ~284 MB |

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

Abre `visor.html` en el navegador y elige `mapa-base.pmtiles` y después `curvas.pmtiles`
(opcionalmente, una ruta `.gpx`). No necesita servidor; solo conexión para cargar MapLibre y las fuentes.

## Regenerar los mapas

```bash
./build.sh
```

Descarga los datos más recientes y genera los dos archivos en `data/`. Requisitos: Java 21+,
Python 3, conda y curl. Usa unos 6 GB de memoria y deja ~3 GB de datos intermedios en `data/`
(extractos de OSM, modelo de elevación y datos auxiliares de Planetiler). Tarda unos 10 minutos,
más las descargas (~3 GB la primera vez).

| Archivo | Qué hace |
|---|---|
| `build.sh` | Todo el proceso |
| `area.py` | Contorno de la zona (`zona.poly`): las cuatro comunidades más una franja del Pirineo |
| `contours.py` | Curvas de nivel desde el modelo de elevación |
| `contours.yml` | Esquema de [Planetiler](https://github.com/onthegomap/planetiler) para las curvas |
| `visor.html` | Visor local con MapLibre GL JS |

Fuentes: extractos de [Geofabrik](https://download.geofabrik.de/) (Cantabria, La Rioja, País Vasco,
Navarra, Aragón, Cataluña, Andorra, Aquitaine, Midi-Pyrénées, Languedoc-Roussillon), recortados a la
zona con [osmium](https://osmcode.org/osmium-tool/), y [Copernicus GLO-30](https://registry.opendata.aws/copernicus-dem/).

## Limitaciones

- Sin sombreado de relieve.
- Fuera de la zona no hay mapa.
- La franja del Pirineo es un rectángulo con algo de margen: incluye parte del llano a ambos lados
  (por ejemplo Huesca, Pau, Perpiñán o Narbona).
