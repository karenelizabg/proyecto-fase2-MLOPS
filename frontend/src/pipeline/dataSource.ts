import { qualityReportSchema, splitsReportSchema, versionsReportSchema } from "./schemas";
import { useReportFetch } from "./useReportFetch";

/**
 * P2-22/23/24: fuente de datos real de las 6 pantallas del pipeline — lee
 * los reportes que escribe `app/presentation/gate.py` (ver
 * docker-compose.yml). Reemplaza los ejemplos estáticos de P2-14.
 *
 * `quality.json` lo escribe el gate en cada arranque de `app`. `splits.json`
 * y `versions.json` todavía no los produce nada (splits/versionado son
 * tiers futuros) — sus hooks devuelven `status: "error"` honesto (404) en
 * vez de datos inventados; cada pantalla decide cómo mostrarlo.
 */

export function useQualityReport() {
  return useReportFetch("/reports/quality.json", qualityReportSchema);
}

export function useSplitsReport() {
  return useReportFetch("/reports/splits.json", splitsReportSchema);
}

export function useVersionsReport() {
  return useReportFetch("/reports/versions.json", versionsReportSchema);
}
