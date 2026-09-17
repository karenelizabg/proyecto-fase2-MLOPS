# P2-13 — Objetos pequeños

`analyze_small_objects(coco, config)` recibe un COCO ya cargado y devuelve el
`AnalyzerResult` común. No hace I/O ni modifica el documento de entrada.
La configuración se obtiene por separado:

```python
from analyzers.small_objects import analyze_small_objects
from policies.small_objects import load_small_object_config

config = load_small_object_config()  # Lee policies/quality.yaml; requiere PyYAML.
result = analyze_small_objects(coco, config)  # coco ya cargado por el llamador.
```

En `max_small_object_ratio`, `width_px` y `height_px` valen 32 por defecto en el
YAML. No hay valores de respaldo hardcodeados en Python. `threshold: 0.40`
sigue siendo la proporción máxima permitida, no un tamaño. `action: warn`
permanece intacto; este analizador no decide bloquear un release.

Para resolver la ambigüedad de “32×32”, una caja es pequeña solo si **ambas**
dimensiones son estrictamente menores que sus límites. Una caja 20×50 no es
pequeña con límites 32×32; tampoco una 32×32. Se usan ancho y alto de `bbox`
COCO `[x, y, width, height]`, no `area` (que puede describir una segmentación).
No se normalizan los tamaños por la resolución de imagen.

Se cuentan todas las anotaciones, incluidas las marcadas `iscrowd`. El COCO
debe tener `annotations` y `categories` válidos. Se rechazan cajas degeneradas
o no finitas y categorías desconocidas; no se reparan datos ni se implementa
el analizador de cajas inválidas. No se comprueban los límites de imagen.

Salida:

- `check_name`: `max_small_object_ratio`.
- `passed`: la proporción es menor o igual al `threshold` suministrado.
- `metric_value`: proporción entre 0 y 1 (multiplicar por 100 para porcentaje).
- `details.small_objects`, `details.total_objects`: conteos de cajas.
- `details.most_affected_class`: `category_id`, `category_name`, `small_objects`,
  `total_objects` y `ratio` dentro de esa clase; `null` si no hay ofensoras.
  Se elige por mayor **conteo** de cajas pequeñas, con desempate por menor ID.
- `details.offending_samples`: lista de `annotation_id`, `image_id`,
  `category_id`, `bbox`, en orden de entrada. Cada muestra es una anotación,
  no una imagen única; permite localizar varias ofensoras en la misma imagen.

Con cero anotaciones: proporción 0, `passed=true`, conteos 0, clase `null`
y lista vacía. Esto no certifica que un dataset vacío tenga calidad suficiente;
solo indica que este check no encontró objetos pequeños.

La salida conserva `AnalyzerResult` sin cambios y no agrega campos de la
compuerta ni integra contratos de presentación ausentes en esta rama.

Desde `app/`, con las dependencias declaradas disponibles:

```bash
python -m pytest tests/test_small_objects.py
python -m pytest
ruff check .
ruff format --check .
```
