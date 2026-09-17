import { StatCard } from "@/components/dashboard/StatCard";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { getQualityReport, getSplitsReport, getVersionsReport } from "../dataSource";

export function OverviewPage() {
  const quality = getQualityReport();
  const splits = getSplitsReport();
  const versions = getVersionsReport();
  const passedChecks = quality.checks.filter((check) => check.passed).length;

  return (
    <main className="flex-1 px-6 py-6 lg:px-10 lg:py-8">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <PageHeader
          title="Overview"
          subtitle={`Dataset ${quality.dataset_version} — contratos v${quality.schema_version}`}
        >
          <StatusBadge label={quality.status} />
        </PageHeader>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard label="Imágenes totales" value={splits.total_images} accent="lilac" />
          <StatCard label="Checks ejecutados" value={quality.checks.length} accent="blue" />
          <StatCard label="Checks aprobados" value={passedChecks} accent="mint" />
          <StatCard label="Releases publicadas" value={versions.releases.length} accent="peach" />
        </div>
      </div>
    </main>
  );
}
