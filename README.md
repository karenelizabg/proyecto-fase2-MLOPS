# Portal de anotación de imágenes

Monolito para subir, anotar y exportar un dataset de detección de objetos.
Las imágenes se almacenan en MinIO; los metadatos y las anotaciones en MariaDB.

## Estructura

```text
backend/    API HTTP con Express (UI → Logic → Data)
frontend/   Interfaz React + Vite (upload, anotación, dashboard, búsqueda)
```

Cada carpeta es un paquete npm independiente con su propio `package.json`.

## Arquitectura

```text
frontend  →  backend
                ├── src/ui      Endpoints HTTP
                ├── src/logic   Reglas de negocio y validación con Zod
                └── src/data    Drizzle (MariaDB) y MinIO
                                    ├── MariaDB  metadatos y anotaciones
                                    └── MinIO    archivos binarios
```

La capa UI nunca accede a MariaDB ni a MinIO: solo invoca a `logic`. La capa
`logic` es la única que puede importar de `data`.

Todo dato que entra por HTTP se valida con Zod antes de llegar a la capa de
datos, y los tipos se infieren del esquema con `z.infer`. La capa Logic lanza
errores tipados que la UI mapea a códigos HTTP:

| Error             | HTTP | Cuándo                                       |
|-------------------|------|----------------------------------------------|
| `ValidationError` | 400  | Dato mal formado o regla de negocio violada  |
| `NotFoundError`   | 404  | El recurso no existe en la base de datos     |

## Requisitos

- Docker y Docker Compose

## Despliegue con un solo comando

```bash
docker compose up --build
```

Este comando levanta los cuatro servicios (MariaDB, MinIO, backend y
frontend). El backend espera a que MariaDB y MinIO estén listos, aplica las
migraciones y siembra datos de ejemplo automáticamente antes de arrancar; no
hace falta ejecutar ningún paso manual.

| Servicio        | URL                              |
|-----------------|-----------------------------------|
| Frontend        | http://localhost:8080            |
| Backend (API)   | http://localhost:3100            |
| Consola MinIO   | http://localhost:9001 (minioadmin/minioadmin) |

Para apagar todo y borrar los datos persistidos (MariaDB y MinIO):

```bash
docker compose down -v
```

Las credenciales de MariaDB/MinIO usadas en `docker-compose.yml` son las de
desarrollo del proyecto; para un despliegue real, cámbialas ahí antes de
publicar los puertos a una red no confiable.

## Desarrollo local sin Docker para las apps

Para iterar con hot reload en backend y frontend, puedes levantar solo la
infraestructura con Docker y correr los paquetes Node directamente en tu
máquina:

### 1. Infraestructura

```bash
docker run --name proyecto1-mariadb \
  -e MARIADB_ROOT_PASSWORD=password \
  -e MARIADB_DATABASE=image_repo \
  -p 3306:3306 -d mariadb:11

docker run --name proyecto1-minio \
  -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  -d quay.io/minio/minio server /data --console-address ":9001"
```

El bucket se crea automáticamente al arrancar el backend.

### 2. Backend

```bash
cd backend
npm ci
cp ../.env.example .env
npm run db:migrate
npm run db:seed
npm run dev
```

Queda escuchando en `http://localhost:3000`.

Si el puerto 3306 ya está ocupado en tu máquina, publica MariaDB en otro
puerto (por ejemplo `-p 3307:3306`) y ajusta `DATABASE_URL` en `backend/.env`.
Nada está fijo en el código: puertos, credenciales y bucket salen del `.env`.

### 3. Frontend

```bash
cd frontend
npm ci
cp .env.example .env
npm run dev
```

Queda escuchando en `http://localhost:5173` y consume la API del backend a
través del proxy `/api` configurado en `vite.config.ts`.

### 4. Comprobación

```bash
curl http://localhost:3000/health
```

Respuesta esperada:

```json
{"status":"ok","database":"connected","timestamp":"..."}
```

## Producción

La forma recomendada de desplegar es `docker compose up --build` (ver
[Despliegue con un solo comando](#despliegue-con-un-solo-comando)): construye
las imágenes de backend y frontend y levanta MariaDB y MinIO junto con ellas.

Si necesitas correr el backend fuera de Docker contra tu propia
infraestructura:

```bash
cd backend
npm run build
npm run start:prod
```

El servidor de producción escucha en `http://localhost:3100`. El script usa
`cross-env`, por lo que funciona igual en Windows, macOS y Linux.

La plantilla `.env.production.example` contiene la configuración de
producción, con `PORT=3100`.

## Variables de entorno

Se copian de `.env.example`. Ningún valor real se versiona: `.gitignore`
ignora todo `.env*` salvo las plantillas de ejemplo.

| Variable                | Propósito                                      |
|-------------------------|------------------------------------------------|
| `PORT`                  | Puerto HTTP (3000 desarrollo, 3100 producción) |
| `DATABASE_URL`          | Cadena de conexión a MariaDB                   |
| `MINIO_ENDPOINT`        | Host de MinIO                                  |
| `MINIO_PORT`            | Puerto de la API de MinIO                      |
| `MINIO_USE_SSL`         | `true` o `false`                               |
| `MINIO_ACCESS_KEY`      | Credencial de acceso                           |
| `MINIO_SECRET_KEY`      | Credencial secreta                             |
| `MINIO_BUCKET`          | Bucket donde se guardan las imágenes           |
| `MAX_UPLOAD_SIZE_BYTES` | Tamaño máximo por imagen (5 MiB por defecto)   |

## API

| Método | Ruta                        | Descripción                                 |
|--------|-----------------------------|---------------------------------------------|
| GET    | `/health`                   | Estado del servicio y de la base de datos   |
| POST   | `/images`                   | Sube una imagen (`multipart/form-data`)     |
| GET    | `/images/search`            | Búsqueda con filtros y paginación           |
| DELETE | `/images/:id`               | Elimina imagen, binario y anotaciones       |
| GET    | `/images/:id/file`          | Sirve el binario desde MinIO                |
| PATCH  | `/images/:id/status`        | Transiciona el estado de anotación          |
| GET    | `/images/:id/annotations`   | Cajas de una imagen, con su categoría       |
| POST   | `/images/:id/annotations`   | Crea una bounding box                       |
| PATCH  | `/annotations/:id`          | Mueve, redimensiona o reclasifica una caja  |
| DELETE | `/annotations/:id`          | Elimina una caja                            |
| GET    | `/categories`               | Categorías disponibles con su color         |
| GET    | `/dashboard/summary`        | Métricas calculadas en SQL                  |
| GET    | `/export/coco`              | Descarga el dataset en formato COCO         |

### Búsqueda

`GET /images/search` acepta:

| Query param         | Descripción                                                |
|---------------------|------------------------------------------------------------|
| `q`                 | Clases con operadores, ej. `car AND person`, `car OR dog`   |
| `categories`        | Ids de categoría separados por coma                        |
| `status`            | `pending`, `in_progress`, `completed` (separados por coma)  |
| `dateFrom`/`dateTo` | Rango sobre la fecha de subida                             |
| `page`/`pageSize`   | Paginación                                                 |

Los operadores se resuelven con subconsultas `EXISTS` en SQL, nunca filtrando
en memoria. Con `AND` la imagen debe contener todas las clases; con `OR`, al
menos una. Mezclar `AND` con `OR` devuelve `400`, porque la precedencia
sería ambigua.

```bash
curl "http://localhost:3000/images/search?q=car%20AND%20person&status=pending&page=1&pageSize=24"
```

### Exportación COCO

```bash
curl -O -J http://localhost:3000/export/coco
```

```json
{
  "images":      [{ "id", "file_name", "width", "height" }],
  "annotations": [{ "id", "image_id", "category_id",
                    "bbox": [x, y, width, height],
                    "area", "iscrowd", "segmentation" }],
  "categories":  [{ "id", "name" }]
}
```

El `bbox` va en píxeles absolutos, `area` es coherente con `width × height`,
e `iscrowd` siempre está presente. Los `id` son consistentes entre las tres
secciones.

## Calidad

Desde `backend/`:

```bash
npm run typecheck   # TypeScript en modo strict
npm run lint        # Biome: cero errores y cero advertencias
npm test            # Vitest
npm run build       # Compilación a dist/
```

Desde `frontend/`:

```bash
npm run typecheck
npm run lint        # Biome: cero errores y cero advertencias
npm run build
```

## Especificaciones y pruebas

Cada regla crítica está trazada de la especificación al escenario Gherkin y
de ahí a la prueba automatizada.

| SPEC            | Regla                                   | Implementación               |
|-----------------|-----------------------------------------|------------------------------|
| SPEC-UPLOAD-001 | Tipo y tamaño de la imagen subida       | `image-upload.validation.ts` |
| SPEC-ANNOT-001  | Geometría y categoría de las cajas      | `annotation.validation.ts`   |
| SPEC-COCO-001   | Estructura y consistencia del JSON COCO | `coco-export.builder.ts`     |
| SPEC-SEARCH-001 | Operadores `AND` / `OR` de búsqueda     | `search-query.parser.ts`     |
| SPEC-VALID-001  | Validación de la frontera HTTP con Zod  | `annotation.validation.ts`   |
| SPEC-DASH-001   | Métricas del dashboard desde SQL        | `dashboard.builder.ts`       |

```text
backend/specs/<nombre>.spec.md
        ↓
backend/features/<nombre>.feature    (Given / When / Then)
        ↓
backend/tests/<nombre>.test.ts       (Vitest)
        ↓
backend/src/logic/<nombre>.ts        (implementación)
```

Las pruebas están diseñadas para fallar si la lógica se rompe: invertir
`width` y `height` en la exportación COCO, permitir un `categoryId` no
positivo o dejar de validar `imageId` hace fallar la suite.

## Fuera de alcance

El entrenamiento del modelo y MLOps corresponden a una fase posterior.

## Etapas del proyecto

El proyecto se construyó por etapas, cada una sobre la anterior:

| Etapa | Qué aportó                                                                 |
|-------|----------------------------------------------------------------------------|
| 1     | Esqueleto: TypeScript, Biome, arquitectura UI/Logic/Data, esquema Drizzle. |
| 2     | Persistencia: MariaDB, MinIO, migraciones, upload de imágenes, seeder.     |
| 3     | Frontend React: portal de anotación, canvas, dashboard y búsqueda.         |
| 4     | Integración final: lógica de negocio, COCO, dashboard y validación Zod.    |

### Qué agrega la etapa final (integración)

Esta etapa conecta el frontend con el backend y completa lo que faltaba para
que el portal funcione de punta a punta:

- **Exportación COCO** (`GET /export/coco`): documento JSON descargable con
  `images`, `annotations` y `categories`, con ids consistentes entre
  secciones (SPEC-COCO-001).
- **Métricas del dashboard** (`GET /dashboard/summary`): totales, objetos por
  clase y progreso de anotación, todo calculado en SQL (SPEC-DASH-001).
- **Búsqueda por clases con operadores** en `GET /images/search`: `AND` / `OR`
  resueltos con subconsultas `EXISTS` en SQL, más filtros por categoría,
  estado y rango de fechas (SPEC-SEARCH-001).
- **Validación de la frontera HTTP con Zod**: todo body, query param y route
  param se valida antes de llegar a la base de datos, con errores tipados que
  la UI mapea a códigos HTTP (SPEC-VALID-001).
- **Reglas de anotación**: la caja debe caber dentro de la imagen, el área la
  calcula el backend, y una imagen sin cajas no puede quedar como completada
  (SPEC-ANNOT-001).

### Notas de puesta en marcha

- Usa `npm install` la primera vez en cada paquete (`backend/` y `frontend/`).
  `node_modules` no se versiona: se reconstruye desde `package-lock.json`.
- El backend valida sus variables de entorno al arrancar (fail-fast con Zod).
  Si falta el `.env` o alguna variable, el proceso termina indicando cuáles
  faltan; copia `.env.example` a `.env` antes de arrancar.
- Si publicaste MariaDB en un puerto distinto al 3306 (por ejemplo 3307
  porque el 3306 ya estaba ocupado), ajusta `DATABASE_URL` en `backend/.env`
  para que coincida.
- El frontend habla con el backend a través del proxy `/api` de Vite en
  desarrollo. `VITE_API_BASE_URL` puede dejarse en `/api`; en producción se
  apunta a la URL real del backend.

## P2-04 — MinIO local y remotes DVC

Esta sección configura el almacenamiento DVC sin cambiar el portal de P1.

- `dev` usa `s3://dvc-cache` con endpoint `http://localhost:9000` (MinIO local).
- `prod` usa `s3://mlops-p2-dvc-cache` en AWS S3.
- `mlops-p2-dataset-releases` se reserva para releases finales del dataset; no es un remote DVC.

### Resumen rápido

- `dev` → MinIO local, bucket `dvc-cache`.
- `prod` → AWS S3, bucket `mlops-p2-dvc-cache`.
- `mlops-p2-dataset-releases` → releases finales del dataset.
- Git versiona la configuración y los archivos `.dvc`; los binarios se guardan en los remotes.
- Cada integrante necesita sus propias credenciales locales de MinIO y su propio acceso SSO a AWS.
- No se comparten contraseñas, access keys, secret keys ni tokens SSO.

### Preparar un clon limpio

Desde la raíz del proyecto, crea tu archivo `.env` local a partir de la plantilla:

```bash
test -e .env || cp .env.example .env
chmod 600 .env
```

Completa:

```text
MINIO_ROOT_USER=
MINIO_ROOT_PASSWORD=
```

con valores locales propios.

Puedes generar una contraseña con:

```bash
openssl rand -hex 32
```

No uses claves AWS en `.env`.

`frontend/.env.example` es independiente y no cambia para este ticket.

Levanta MinIO:

```bash
docker compose up -d --no-deps minio
```

### Instalar DVC

Instala DVC con soporte S3 en un entorno Python separado:

```bash
python3 -m venv .venv-dvc
. .venv-dvc/bin/activate
python -m pip install 'dvc[s3]==3.67.1'
export DVC_NO_ANALYTICS=1
export DVC_SITE_CACHE_DIR="${TMPDIR:-/tmp}/p2-04-dvc-site-cache"
```

El repositorio ya contiene la inicialización de DVC y la configuración de los remotes, por lo que no es necesario ejecutar `dvc init`.

### Configurar `dev` con MinIO local

Carga las variables de tu `.env`:

```bash
set -a
. ./.env
set +a
```

Configura las credenciales de MinIO únicamente de forma local:

```bash
dvc remote modify --local dev access_key_id "$MINIO_ROOT_USER"
dvc remote modify --local dev secret_access_key "$MINIO_ROOT_PASSWORD"
chmod 600 .dvc/config.local
```

No omitas `--local`.

No agregues `.env` ni `.dvc/config.local` a Git.

### Crear el bucket local `dvc-cache`

Si el bucket `dvc-cache` todavía no existe en MinIO, créalo con:

```bash
python - <<'PY'
import os
from botocore.session import get_session
from botocore.exceptions import ClientError

client = get_session().create_client(
    's3',
    endpoint_url='http://localhost:9000',
    region_name='us-east-1',
    aws_access_key_id=os.environ['MINIO_ROOT_USER'],
    aws_secret_access_key=os.environ['MINIO_ROOT_PASSWORD'],
)

try:
    client.head_bucket(Bucket='dvc-cache')
except ClientError as error:
    if error.response['ResponseMetadata']['HTTPStatusCode'] != 404:
        raise
    client.create_bucket(Bucket='dvc-cache')

print('Bucket local dvc-cache disponible')
PY
```

Este paso solo opera contra MinIO local en `localhost:9000`.

No modifica el bucket `image-annotations` usado por el portal.

### Verificar los remotes

Ejecuta:

```bash
dvc remote list -v
```

La salida debe incluir:

```text
dev     s3://dvc-cache
prod    s3://mlops-p2-dvc-cache
```

### Subir y bajar archivos con `dev`

Primero registra el archivo o directorio con DVC:

```bash
dvc add ruta/al/dataset
```

Para subirlo a MinIO:

```bash
dvc push -r dev
```

Para recuperarlo:

```bash
dvc pull -r dev
```

Los archivos `.dvc` generados se comparten mediante Git.

Los binarios se guardan en MinIO, no directamente en GitHub.

### AWS S3 y remote `prod`

AWS está configurado en la región:

```text
us-east-1
```

Buckets usados por el proyecto:

| Bucket | Uso |
|---|---|
| `mlops-p2-dvc-cache` | Remote DVC `prod`. |
| `mlops-p2-dataset-releases` | Releases finales del dataset. |

`prod` utiliza AWS S3 real y no utiliza un endpoint personalizado.

Cada integrante necesita su propia identidad autorizada mediante AWS IAM Identity Center / SSO.

El perfil local recomendado es:

```text
mlops-p2
```

Instala AWS CLI v2 y comprueba la instalación:

```bash
aws --version
```

Configura el acceso SSO:

```bash
aws configure sso --profile mlops-p2
aws sso login --profile mlops-p2
aws sts get-caller-identity --profile mlops-p2
```

Usa la región:

```text
us-east-1
```

No copies la salida de `aws sts get-caller-identity` al repositorio.

Configura el perfil únicamente de forma local para DVC:

```bash
dvc remote modify --local prod profile mlops-p2
```

Comprueba nuevamente los remotes:

```bash
dvc remote list -v
```

La salida debe incluir:

```text
dev     s3://dvc-cache
prod    s3://mlops-p2-dvc-cache
```

Para subir archivos a AWS S3:

```bash
dvc push -r prod
```

Para recuperarlos:

```bash
dvc pull -r prod
```

Si la sesión SSO expira:

```bash
aws sso login --profile mlops-p2
```

### Flujo recomendado para el equipo

1. Hacer `git pull` para obtener los metadatos `.dvc` más recientes.
2. Activar el entorno de DVC.
3. Iniciar sesión con AWS SSO si se va a usar `prod`.
4. Ejecutar `dvc pull -r prod` para recuperar los archivos del dataset compartido.
5. Agregar o actualizar archivos del dataset.
6. Ejecutar `dvc add <ruta>` para actualizar los metadatos.
7. Ejecutar `dvc push -r prod` para subir los binarios a S3.
8. Versionar con Git los archivos `.dvc` y los cambios de código correspondientes.

No subas los binarios grandes directamente al repositorio de GitHub.

### Seguridad y validación

Los siguientes archivos o datos no deben versionarse:

- `.env`
- `.dvc/config.local`
- access keys de AWS
- secret keys de AWS
- tokens SSO
- credenciales reales de MinIO

Comprueba que los archivos privados estén ignorados:

```bash
git check-ignore .env .dvc/config.local
```

La salida debe incluir:

```text
.env
.dvc/config.local
```

Comprueba que `.env.example` sí pueda versionarse:

```bash
git check-ignore .env.example
```

Ese comando no debe mostrar salida.

Comprueba que no existan access keys AWS con prefijo `AKIA` en el historial:

```bash
git log --all -p -S 'AKIA'
```

La salida debe estar vacía.

P2-04 externaliza las credenciales MinIO usadas por Docker Compose y evita agregar secretos AWS al repositorio.

No se reescribe el historial de Git ni se modifica la configuración heredada de MariaDB.

### Criterios de aceptación

Antes de cerrar P2-04, verificar:

- `docker compose up -d --no-deps minio` levanta MinIO.
- `.env.example` existe y no contiene credenciales reales.
- `dvc remote list -v` muestra `dev` y `prod`.
- `dvc push -r dev` funciona siguiendo este README desde un clon limpio.
- `dvc push -r prod` y `dvc pull -r prod` funcionan con AWS S3.
- `git log --all -p -S 'AKIA'` no devuelve resultados.
- `.env` y `.dvc/config.local` permanecen fuera de Git.
- Los buckets `mlops-p2-dvc-cache` y `mlops-p2-dataset-releases` existen en AWS.

## P2-42 — Pipeline DVC completo (`dvc.yaml`)

Hasta este ticket, el dataset se manejaba con `dvc add` suelto: reproducible
como almacenamiento de archivos, pero sin un pipeline declarado con
dependencias/salidas. `dvc.yaml` define un stage, `quality_gate`, que corre
la compuerta de calidad real (`app/presentation/gate.py`) contra
`data/raw/annotations` + `data/raw/images` y escribe `reports/quality.json`.

```bash
dvc repro
```

- **`app/dvc_gate_stage.py`** es un wrapper, no un cambio a `gate.py`: DVC
  ejecuta `cmd` vía el shell del sistema operativo (`cmd.exe` en Windows),
  que no soporta `VAR=valor comando` (sintaxis bash usada en los ejemplos
  de `app/presentation/README.md`). El wrapper fija con `os.environ` los
  mismos valores placeholder que `DATABASE_URL`/`MINIO_*` necesitan (campos
  requeridos por `storage.Settings`, nunca usados por el gate) antes de
  llamar a `gate.run()` — no a `gate.main()`, que si el dataset no pasa la
  compuerta devuelve `exit 1` y rompería `dvc repro` para un estado
  legítimo y esperado del dataset (ver `min_images_per_class` en la sección
  de Frente 1 más abajo). `dvc repro` solo debe fallar si el cómputo en sí
  falla, no si el reporte resultante dice `status: failed`.
- **`reports/quality.json` es un `metrics`, no un `outs`**, con
  `cache: false`: es un reporte chico y legible, pensado para diffs de PR y
  `dvc metrics diff`, no un artefacto binario que amerite el object store
  de DVC.
- **`always_changed: true`**: en esta máquina (con `Documents` sincronizado
  por OneDrive), el run-cache interno de DVC (`.dvc/cache/runs/`) falla con
  `WinError 3` durante su propio `move()` de archivo temporal — no es un
  bug de este stage. `always_changed` evita ese código por completo; el
  costo es que el stage siempre se re-ejecuta en `dvc repro` en vez de
  saltarse cuando nada cambió, aceptable dado lo barato que es correrlo.
- Los remotes `dev`/`prod` de P2-04 ya existían; lo que faltaba en un
  checkout nuevo era el paso local `dvc remote modify --local dev
  access_key_id/secret_access_key` (con `$MINIO_ROOT_USER`/
  `$MINIO_ROOT_PASSWORD`) y crear el bucket `dvc-cache` si no existía —
  ambos ya documentados arriba en P2-04, solo faltaba ejecutarlos en este
  checkout.

### Criterios de aceptación

- `dvc.yaml` define el stage `quality_gate` con dependencias y salida reales.
- `dvc.lock` y `dvc.yaml` versionados en Git; los datos siguen fuera de Git.
- `dvc repro` corre limpio y regenera `reports/quality.json`.
- `dvc push`/`dvc pull` funcionan contra `dev` y `prod` (verificado: 612
  archivos sincronizados en `dev`, `prod` ya en uso durante todo el proyecto).

## Frente 1 — Arquitectura y entorno del pipeline de calidad

El portal de anotación (arriba) ya no es el entregable de la Fase 2: es la
fuente del COCO crudo. El entregable es un pipeline en Python que mide la
calidad de ese COCO, decide si se libera y versiona el resultado con DVC.

Este frente deja listo el esqueleto; la lógica de cada tier la completan los
frentes 2 a 6.

### Capas (`app/`)

El pipeline vive en `app/`, como paquete Python independiente (hermano de
`backend/` y `frontend/`), con una carpeta por capa:

```text
app/
  ingestion/      Tier 1 — COCO crudo del Proyecto 1
  analyzers/      Tier 2 — 5 analizadores de calidad (objetos pequeños,
                  desbalance, duplicados, cajas inválidas, sesgo espacial)
  policies/       Tier 3 — compuerta de calidad (policies/quality.yaml)
  splits/         Tier 4 — split estratificado train/val/test
  storage/        Tier 5 — MariaDB y MinIO/S3 (DVC)
  presentation/   Expone los resultados a la app web y al Dataset Copilot
```

**Regla de la compuerta de acoplamiento:** solo `storage/` importa `os`
(para leer variables de entorno), crea clientes `boto3`/`Minio(` o abre un
`create_engine`/`pymysql.connect`. Todas las demás capas son funciones puras
que reciben los datos ya cargados como argumento — así se pueden probar con
`pytest` sin levantar MariaDB/MinIO reales. Se verifica con:

```bash
grep -rn "os\.environ\|os\.getenv\|boto3\.client\|Minio(\|create_engine\|pymysql\.connect" app/analyzers/
```

(sin resultados) y con `app/tests/test_architecture.py`, que corre lo mismo
en CI.

### Levantar todo

```bash
docker compose up
```

Además de `mariadb`, `minio`, `backend` y `frontend` (portal P1, se mantiene
porque la cola de re-anotación —cuando la compuerta bloquea el release—
ocurre ahí), se agrega el servicio `app`: el pipeline Python, que reutiliza
el mismo MariaDB y el mismo MinIO del portal (mismas credenciales de
`.env`, sin variables nuevas). Al arrancar, `app` valida que puede
conectarse a ambos y queda a la espera de que los siguientes frentes
implementen la lógica de cada tier.

### Python y lockfile

`app/pyproject.toml` fija `requires-python = "==3.12.*"` y `app/Dockerfile`
usa `python:3.12-slim` — misma versión en ambos lados. Las dependencias
quedan resueltas y pineadas en `app/uv.lock` (generado con `uv lock`, no a
mano); el `Dockerfile` instala desde ese lockfile con
`uv sync --locked`, así que build local y build en CI siempre resuelven
exactamente las mismas versiones.

Para trabajar en `app/` localmente con [uv](https://docs.astral.sh/uv/):

```bash
cd app
uv sync            # crea .venv con dependencias + grupo dev (ruff, pytest)
uv run pytest -q
uv run ruff check .
```

### Supuestos de este frente pendientes de confirmar con Karen/Heri

Lo siguiente se infirió a partir del diagrama de tiers y los mockups del
profe, y del trabajo ya mergeado de DVC (P2-04); si Karen decide otra cosa,
son fáciles de mover porque todo el pipeline está aislado en `app/`:

- El portal Node (`backend`/`frontend`) se queda corriendo junto al pipeline
  en el mismo `docker-compose.yml`, en vez de retirarse porque "el portal ya
  no es el entregable".
- El pipeline reutiliza el MariaDB/MinIO del portal (misma base
  `image_repo`, mismo bucket `image-annotations`) en vez de tener su propia
  infraestructura de datos en dev.
- Quién es responsable del frente 4 (compuerta) no estaba claro en el
  reparto compartido — confirmar con Karen.