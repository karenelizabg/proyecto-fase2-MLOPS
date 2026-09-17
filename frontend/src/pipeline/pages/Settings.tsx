import { PageHeader } from "../components/PageHeader";
import { ReportBoundary } from "../components/ReportBoundary";
import { useVersionsReport } from "../dataSource";

/**
 * Placeholder a propósito: no hay compuerta/política editable todavía
 * (eso es una pantalla de edición real, fuera de alcance de P2-22/23/24).
 * Solo se muestra el dataset activo, que sí viene de un contrato real
 * (versions.json) — hoy ese archivo no existe (nada lo produce todavía),
 * así que esta pantalla muestra el estado de error honesto en vez de un
 * número inventado.
 */
export function SettingsPage() {
  const versions = useVersionsReport();

  return (
    <main className="flex-1 px-6 py-6 lg:px-10 lg:py-8">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <PageHeader title="Settings" subtitle="Configuración del pipeline de calidad" />

        <ReportBoundary state={versions}>
          {(report) => {
            const activeRelease = report.releases[report.releases.length - 1];
            return (
              <div className="rounded-2xl border border-border bg-surface p-5 shadow-card">
                <p className="text-sm text-ink-muted">Dataset activo</p>
                <p className="mt-1 text-lg font-semibold text-ink">
                  {activeRelease?.dataset_version ?? "Sin releases publicadas"}
                </p>
              </div>
            );
          }}
        </ReportBoundary>

        <div className="rounded-2xl border border-dashed border-border-strong bg-surface px-6 py-16 text-center text-sm text-ink-muted">
          La edición de políticas de calidad (quality.yaml) todavía no está implementada.
        </div>
      </div>
    </main>
  );
}
