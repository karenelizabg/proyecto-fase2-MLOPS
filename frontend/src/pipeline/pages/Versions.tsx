import { PageHeader } from "../components/PageHeader";
import { ReportBoundary } from "../components/ReportBoundary";
import { useVersionsReport } from "../dataSource";

export function VersionsPage() {
  const versions = useVersionsReport();

  return (
    <main className="flex-1 px-6 py-6 lg:px-10 lg:py-8">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <ReportBoundary state={versions}>
          {(report) => (
            <>
              <PageHeader
                title="Versions"
                subtitle={`${report.releases.length} release(s) publicadas del dataset`}
              />

              {report.releases.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-border-strong bg-surface px-6 py-16 text-center text-sm text-ink-muted">
                  Todavía no hay releases publicadas.
                </div>
              ) : (
                <ul className="flex flex-col gap-3">
                  {report.releases.map((release) => (
                    <li
                      key={release.dataset_version}
                      className="flex flex-col gap-1 rounded-2xl border border-border bg-surface p-5 shadow-card sm:flex-row sm:items-center sm:justify-between"
                    >
                      <span className="font-medium text-ink">{release.dataset_version}</span>
                      <span className="text-sm text-ink-muted">
                        {release.quality_file} · {release.splits_file}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </>
          )}
        </ReportBoundary>
      </div>
    </main>
  );
}
