import { StatCard } from "@/components/dashboard/StatCard";
import { Skeleton } from "@/components/ui/Skeleton";
import { PageHeader } from "../components/PageHeader";
import { ReportBoundary } from "../components/ReportBoundary";
import { StatusBadge } from "../components/StatusBadge";
import { useQualityReport, useSplitsReport, useVersionsReport } from "../dataSource";

/** Una StatCard que se apaga a "no disponible" si su fuente (splits/versions) no existe todavía. */
function OptionalStat({
  state,
  label,
  accent,
  render,
}: Readonly<{
  state: { status: "loading" | "error" | "success" };
  label: string;
  accent: "lilac" | "mint" | "peach" | "blue";
  render: () => number;
}>) {
  if (state.status === "loading") {
    return <Skeleton className="h-[92px] rounded-2xl" />;
  }
  if (state.status === "error") {
    return (
      <div className="rounded-2xl border border-dashed border-border-strong bg-surface p-5">
        <p className="text-sm text-ink-muted">{label}</p>
        <p className="mt-3 text-lg font-medium text-ink-faint">No disponible</p>
      </div>
    );
  }
  return <StatCard label={label} value={render()} accent={accent} />;
}

export function OverviewPage() {
  const quality = useQualityReport();
  const splits = useSplitsReport();
  const versions = useVersionsReport();

  return (
    <main className="flex-1 px-6 py-6 lg:px-10 lg:py-8">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <ReportBoundary state={quality}>
          {(report) => {
            const passedChecks = report.checks.filter((check) => check.passed).length;
            return (
              <>
                <PageHeader
                  title="Overview"
                  subtitle={`Dataset ${report.dataset_version} — contratos v${report.schema_version}`}
                >
                  <StatusBadge label={report.status} />
                </PageHeader>

                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  <OptionalStat
                    state={splits}
                    label="Imágenes totales"
                    accent="lilac"
                    render={() => (splits.status === "success" ? splits.data.total_images : 0)}
                  />
                  <StatCard label="Checks ejecutados" value={report.checks.length} accent="blue" />
                  <StatCard label="Checks aprobados" value={passedChecks} accent="mint" />
                  <OptionalStat
                    state={versions}
                    label="Releases publicadas"
                    accent="peach"
                    render={() =>
                      versions.status === "success" ? versions.data.releases.length : 0
                    }
                  />
                </div>
              </>
            );
          }}
        </ReportBoundary>
      </div>
    </main>
  );
}
