import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { getQualityReport } from "../dataSource";

export function AnalyzersPage() {
  const quality = getQualityReport();

  return (
    <main className="flex-1 px-6 py-6 lg:px-10 lg:py-8">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <PageHeader
          title="Analyzers"
          subtitle={`${quality.checks.length} checks del dataset ${quality.dataset_version}`}
        >
          <StatusBadge label={quality.status} />
        </PageHeader>

        <div className="overflow-hidden rounded-2xl border border-border bg-surface shadow-card">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-border bg-sidebar text-xs uppercase text-ink-muted">
              <tr>
                <th className="px-5 py-3 font-medium">Check</th>
                <th className="px-5 py-3 font-medium">Resultado</th>
                <th className="px-5 py-3 font-medium">Métrica</th>
                <th className="px-5 py-3 font-medium">Acción si falla</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {quality.checks.map((check) => (
                <tr key={check.check_name}>
                  <td className="px-5 py-3 font-medium text-ink">{check.check_name}</td>
                  <td className="px-5 py-3">
                    <StatusBadge label={check.passed ? "passed" : "failed"} />
                  </td>
                  <td className="px-5 py-3 text-ink-muted">{check.metric_value}</td>
                  <td className="px-5 py-3 text-ink-muted">{check.action}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  );
}
