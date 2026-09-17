# P2-12 — Contratos JSON v1.0

`contracts.py` define los contratos públicos con Pydantic v2. Los ejemplos
manuales y ficticios están en `examples/quality.json`, `examples/splits.json`
y `examples/versions.json`. No son resultados de un pipeline ejecutado ni releases
publicadas. No contienen credenciales, URLs de servicios ni rutas del equipo.

Los campos son obligatorios salvo `details`, que puede omitirse y toma `{}`.
Los modelos rechazan campos adicionales, conversiones de strings a números/bools,
números no finitos y valores fuera de los rangos definidos. `details` es la única
extensión abierta: sus claves dependen del check y sus valores deben ser JSON.
No se deben colocar objetos Python, secretos ni rutas locales en ese campo.

## Campos comunes

| Campo | Tipo y significado |
|---|---|
| `schema_version` | Literal `"1.0"`, versión del contrato, no del dataset. |
| `dataset_version` | Identificador opaco, no vacío, con letras ASCII, dígitos, puntos, guiones o guiones bajos; comienza con letra o dígito. Une los documentos de un mismo dataset. No implica un commit Git o hash DVC. |

La forma v1.0 queda congelada: cambiar campos, tipos o semántica requiere revisar
la versión del contrato y sus consumidores. Los schemas JSON se pueden obtener
con `QualityReport.model_json_schema()`, `SplitsReport.model_json_schema()` y
`VersionsReport.model_json_schema()` sin generar archivos ni acceder a servicios.
Las comprobaciones entre campos de los validadores Pydantic complementan el JSON
Schema: un validador JSON Schema genérico no ejecuta esos validadores Python.

## quality.json — QualityReport

| Campo | Uso |
|---|---|
| `schema_version`, `dataset_version` | Identifican el contrato y el dataset evaluado. |
| `status` | `passed`, `warning` o `failed`, resultado global entregado por la compuerta. |
| `checks` | Lista no vacía de checks ejecutados, con nombres únicos. No implica que todos los checks posibles hayan sido ejecutados. |
| `checks[].check_name` | Identificador estable del check; no es un texto traducido de UI. |
| `checks[].passed` | Booleano con el resultado ya calculado por el analizador/compuerta. |
| `checks[].metric_value` | Número finito; su unidad y significado dependen del check. |
| `checks[].details` | Objeto JSON con evidencia adicional; la UI puede mostrarlo sin asumir claves fijas. |
| `checks[].action` | `warn` o `fail`, efecto de un check no aprobado, suministrado por la capa de políticas. |

`QualityCheck` extiende `AnalyzerResult` sin modificarlo. Los checks existentes
se pueden adaptar con `QualityCheck.model_validate({**result.model_dump(),
"action": action})`; obtener `action` y calcular `status` corresponde a políticas,
no a presentación. `passed` significa que no hay incumplimientos; `warning`,
que hay advertencias pero no bloqueos; `failed`, que hay un bloqueo. El contrato
no calcula ni impone esa agregación para no implementar la compuerta de otro ticket.

En el ejemplo, `metric_value` representa: mínimo de imágenes por clase (400),
ratio mayor/menor clase (1), proporción de objetos pequeños (0.45), cantidad de
cajas degeneradas (0) y pares con fuga entre splits (0), respectivamente. Un check
con `action=fail` puede tener `passed=true`: la acción aplica solo si incumple.
No se copian ni evalúan umbrales de `policies/quality.yaml`. El umbral de similitud
de duplicados es un parámetro de análisis, no se inventa un resultado para él.

## splits.json — SplitsReport

| Campo | Uso |
|---|---|
| `schema_version`, `dataset_version` | Identifican contrato y dataset. |
| `total_images` | Entero positivo de imágenes incluidas en la partición. |
| `splits` | Objeto con exactamente `train`, `validation` y `test`. |
| `splits.<nombre>.image_count` | Entero no negativo; una imagen se cuenta una sola vez en el resumen. |
| `splits.<nombre>.ratio` | Proporción real de imágenes, entre 0 y 1; no porcentaje ni proporción solicitada. |

Los conteos deben sumar `total_images`; cada proporción debe coincidir con
`image_count / total_images` con tolerancia absoluta de `1e-6`. Se admiten splits
vacíos con ambos valores en cero, pero no una partición de cero imágenes. El
contrato solo valida el resumen: no genera particiones ni verifica estratificación,
solapamientos reales o leakage. La capa `splits` puede usar `val` internamente,
pero el nombre público congelado es `validation`.

## versions.json — VersionsReport

| Campo | Uso |
|---|---|
| `schema_version` | Versión del catálogo. |
| `releases` | Lista de releases disponibles; puede estar vacía. No tiene orden semántico ni designa automáticamente una versión como la más reciente. |
| `releases[].dataset_version` | Identificador único dentro del catálogo. |
| `releases[].quality_file` | Referencia relativa a un archivo llamado `quality.json`. |
| `releases[].splits_file` | Referencia relativa a un archivo llamado `splits.json`. |

Las referencias se resuelven respecto del directorio que contiene `versions.json`.
Permiten subdirectorios de nombres ASCII alfanuméricos con `.`, `_` y `-`; prohíben
rutas absolutas, segmentos vacíos, `.`/`..`, URLs y separadores Windows. Para más
releases pueden usarse referencias como `demo-v2/quality.json`. El modelo valida
su forma, sin abrir los archivos: el productor del catálogo debe garantizar su
existencia y que `dataset_version` coincida en ambos reportes.

El ejemplo cataloga `demo-v1.0.0` y referencia los otros dos JSON de la misma
carpeta. No duplica el estado de calidad o los conteos en el catálogo para evitar
datos divergentes. No contiene URIs S3, ETags, firmas, semver obligatorio ni una
integración inventada con el frontend.

## Pruebas y límites

Desde `app/`, con las dependencias de desarrollo declaradas instaladas:

```bash
pytest
ruff check .
ruff format --check .
```

Las pruebas usan `unittest.TestCase`, que pytest descubre, y `model_validate`
de Pydantic v2. También pueden ejecutarse sin pytest con
`python -m unittest tests.test_json_contracts -v` (requiere Pydantic v2).
Verifican los tres ejemplos, referencias reales entre ellos, round trip y rechazos
de documentos inválidos. No importan el entrypoint `presentation.main` ni ejecutan
conexiones del código preexistente.

P2-11 deberá aportar resultados y un resumen compatibles; este ticket no implementa
sus algoritmos. P2-14 deberá acordar con estos contratos la identificación de releases
y ubicación de reportes. No se presupone su API: ambos tickets no están implementados
en esta copia. Cualquier necesidad nueva debe discutirse antes de cambiar v1.0.

## P2-22/23/24 — La compuerta de calidad end-to-end (`gate.py`)

`gate.py` es el primer código que efectivamente corre el pipeline contra el
dataset real: `ingestion/loader.py` junta los `annotations-lote-*.json` de
`data/raw/annotations/` en un `CocoDataset` validado, corre los 5
analizadores existentes (`imbalance`, `small_objects`, `invalid_boxes`,
`duplicates`, `spatial_bias`), arma un `QualityReport` real (no el ejemplo)
y lo escribe en `REPORTS_DIR/quality.json`.

- `min_images_per_class` no es su propio analizador (vive dentro de
  `imbalance.py`, ver `details.classes_below_minimum`); el gate lo deriva
  como check independiente porque `quality.yaml` le da una severidad
  distinta (`fail`) a la de `max_imbalance_ratio` (`warn`).
- `analyze_duplicates()` usa el check_name interno `duplicate_images`
  (ver `analyzers/duplicates.py` y su test); el gate lo renombra a
  `duplicate_similarity_threshold` en el reporte — el nombre de la política
  que en verdad evalúa — sin tocar el analizador ya mergeado.
- `spatial_bias` (P2-29) mide dispersión del centro normalizado de las
  cajas; el ticket original no definía el algoritmo, se confirmó con Andy
  (ver `analyzers/README.md`). `quality.yaml` gana una clave nueva
  (`min_spatial_dispersion`) que no existía para ningún analizador previo.
- `cross_split_leakage` NO se incluye: requiere splits reales, que no
  existen hasta que se implemente ese tier. El reporte solo declara los 6
  checks que sí se pueden evaluar hoy; no se inventa ese dato.
- `main()` devuelve `1` si algún check con `action: fail` no pasó — pensado
  para encadenarse como dependencia dura de la siguiente etapa
  (`python -m presentation.gate; echo "exit=$?"`).
- `presentation/main.py` corre el gate una vez al arrancar el contenedor
  `app` y sigue vivo aunque falle (loggea y continúa) — el contenedor es un
  servicio de larga duración, el gate es un paso de pipeline con su propio
  exit code; no se confunden.

`DATASET_DIR`/`REPORTS_DIR` (ver `storage/settings.py`) apuntan a los
volúmenes montados en `docker-compose.yml`, no a rutas calculadas desde
`__file__`: el Dockerfile aplana `app/` a `/app`, así que una ruta relativa
al código (`../../data/raw`) dejaría de tener sentido ahí. El frontend lee
`REPORTS_DIR` como estático servido por nginx en `/reports/*.json`
(volumen compartido `reports_data`, sin backend HTTP nuevo) — ver
`frontend/docker/nginx.conf` y `frontend/src/pipeline/dataSource.ts`.

Con el dataset real actual, la compuerta **bloquea de verdad**: `person`/
`car` están sembrados como categorías pero nunca se han anotado (0
imágenes cada una), así que `min_images_per_class` (umbral 300, severidad
`fail`) nunca pasa mientras existan categorías declaradas sin imágenes.
Esto no es un bug del gate — es el reflejo honesto de que el dataset
todavía no cumple la meta M3 del curso.

```bash
uv run pytest tests/test_loader.py tests/test_gate.py
DATABASE_URL=... MINIO_ENDPOINT=... MINIO_PORT=... MINIO_ACCESS_KEY=... \
MINIO_SECRET_KEY=... MINIO_BUCKET=... DATASET_DIR=../data/raw REPORTS_DIR=/tmp/reports \
uv run python -m presentation.gate
```
