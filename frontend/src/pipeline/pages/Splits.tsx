import { StatCard } from "@/components/dashboard/StatCard";
import { PageHeader } from "../components/PageHeader";
import { ReportBoundary } from "../components/ReportBoundary";
import { useSplitsReport } from "../dataSource";
import type { SplitsReport } from "../schemas";

const SPLIT_LABELS: Record<keyof SplitsReport["splits"], string> = {
  train: "Train",
  validation: "Validation",
  test: "Test",
};

const SPLIT_ACCENTS: Record<keyof SplitsReport["splits"], "lilac" | "blue" | "mint"> = {
  train: "lilac",
  validation: "blue",
  test: "mint",
};

export function SplitsPage() {
  const splits = useSplitsReport();

  return (
    <main className="flex-1 px-6 py-6 lg:px-10 lg:py-8">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <ReportBoundary state={splits}>
          {(report) => (
            <>
              <PageHeader
                title="Splits"
                subtitle={`${report.total_images.toLocaleString("es")} imágenes en el dataset ${report.dataset_version}`}
              />

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                {(Object.keys(SPLIT_LABELS) as Array<keyof SplitsReport["splits"]>).map((key) => {
                  const summary = report.splits[key];
                  return (
                    <StatCard
                      key={key}
                      label={`${SPLIT_LABELS[key]} (${Math.round(summary.ratio * 100)}%)`}
                      value={summary.image_count}
                      accent={SPLIT_ACCENTS[key]}
                    />
                  );
                })}
              </div>
            </>
          )}
        </ReportBoundary>
      </div>
    </main>
  );
}
