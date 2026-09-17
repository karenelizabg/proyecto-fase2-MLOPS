import { PageHeader } from "../components/PageHeader";
import { getVersionsReport } from "../dataSource";

/**
 * Placeholder a propósito: no hay compuerta/política editable todavía
 * (P2-22). Solo se muestra el dataset activo, que sí viene de un contrato
 * JSON real (versions.json), no un número inventado.
 */
export function SettingsPage() {
  const versions = getVersionsReport();
  const activeRelease = versions.releases[versions.releases.length - 1];

  return (
    <main className="flex-1 px-6 py-6 lg:px-10 lg:py-8">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <PageHeader title="Settings" subtitle="Configuración del pipeline de calidad" />

        <div className="rounded-2xl border border-border bg-surface p-5 shadow-card">
          <p className="text-sm text-ink-muted">Dataset activo</p>
          <p className="mt-1 text-lg font-semibold text-ink">
            {activeRelease?.dataset_version ?? "Sin releases publicadas"}
          </p>
        </div>

        <div className="rounded-2xl border border-dashed border-border-strong bg-surface px-6 py-16 text-center text-sm text-ink-muted">
          La edición de políticas de calidad (quality.yaml) todavía no está implementada.
        </div>
      </div>
    </main>
  );
}
