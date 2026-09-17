import { PageHeader } from "../components/PageHeader";

/**
 * Placeholder a propósito: el Copilot (servidor MCP de solo lectura) es
 * P2-34, todavía sin implementar. No hay contrato JSON de ejemplo para esta
 * pantalla, así que no se inventan números — solo se deja el punto de
 * navegación listo.
 */
export function CopilotPage() {
  return (
    <main className="flex-1 px-6 py-6 lg:px-10 lg:py-8">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <PageHeader title="Copilot" subtitle="Asistente de consulta sobre el dataset" />

        <div className="rounded-2xl border border-dashed border-border-strong bg-surface px-6 py-16 text-center text-sm text-ink-muted">
          El Copilot (P2-34) todavía no está implementado.
        </div>
      </div>
    </main>
  );
}
