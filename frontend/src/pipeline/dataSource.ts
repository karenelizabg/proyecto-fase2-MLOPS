import qualityExample from "./examples/quality.json";
import splitsExample from "./examples/splits.json";
import versionsExample from "./examples/versions.json";
import {
  type QualityReport,
  qualityReportSchema,
  type SplitsReport,
  splitsReportSchema,
  type VersionsReport,
  versionsReportSchema,
} from "./schemas";

/**
 * P2-14: fuente de datos de las 6 pantallas del pipeline. Hoy lee los
 * ejemplos congelados por P2-12 (`app/presentation/examples/`, copiados a
 * `./examples/` porque el build de Docker del frontend solo tiene acceso a
 * `frontend/`, no a `app/`). P2-24 reemplaza el cuerpo de estas tres
 * funciones por `fetch` contra el backend real; las pantallas no cambian.
 */

export function getQualityReport(): QualityReport {
  return qualityReportSchema.parse(qualityExample);
}

export function getSplitsReport(): SplitsReport {
  return splitsReportSchema.parse(splitsExample);
}

export function getVersionsReport(): VersionsReport {
  return versionsReportSchema.parse(versionsExample);
}
