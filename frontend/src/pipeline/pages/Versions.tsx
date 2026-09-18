import { PageHeader } from "../components/PageHeader";
import { ReportBoundary } from "../components/ReportBoundary";
import { SplitSummary } from "../components/SplitSummary";
import { StatusBadge } from "../components/StatusBadge";
import { useReleaseReport, useVersionsReport } from "../dataSource";
import type { DatasetRelease } from "../schemas";

function ReleaseCard({ release }: Readonly<{ release: DatasetRelease }>) {
  const quality = useReleaseReport("quality", release);
  const splits = useReleaseReport("splits", release);
  return (
    <li className="rounded-2xl border border-border bg-surface p-5 space-y-4">
      <h2 className="font-semibold">{release.dataset_version}</h2>
      <ReportBoundary state={quality}>
        {(report) => (
          <p>
            Calidad: <StatusBadge label={report.status} />
          </p>
        )}
      </ReportBoundary>
      <ReportBoundary state={splits}>{(report) => <SplitSummary report={report} />}</ReportBoundary>
      <p className="flex gap-4">
        <a href={`/reports/${release.quality_file}`}>Reporte de calidad</a>
        <a href={`/reports/${release.splits_file}`}>Reporte de splits</a>
      </p>
    </li>
  );
}

export function VersionsPage() {
  const versions = useVersionsReport();
  return (
    <main className="flex-1 px-6 py-6 lg:px-10">
      <PageHeader
        title="Versions"
        subtitle="Catálogo de releases publicadas; sin orden cronológico definido"
      />
      <ReportBoundary state={versions}>
        {(catalog) =>
          catalog.releases.length === 0 ? (
            <p>Todavía no hay releases publicadas.</p>
          ) : (
            <ul className="mt-6 space-y-4">
              {catalog.releases.map((release) => (
                <ReleaseCard key={release.dataset_version} release={release} />
              ))}
            </ul>
          )
        }
      </ReportBoundary>
    </main>
  );
}
