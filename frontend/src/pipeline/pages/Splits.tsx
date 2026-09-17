import { StatCard } from "@/components/dashboard/StatCard";
import { PageHeader } from "../components/PageHeader";
import { getSplitsReport } from "../dataSource";
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
  const splits = getSplitsReport();

  return (
    <main className="flex-1 px-6 py-6 lg:px-10 lg:py-8">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <PageHeader
          title="Splits"
          subtitle={`${splits.total_images.toLocaleString("es")} imágenes en el dataset ${splits.dataset_version}`}
        />

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {(Object.keys(SPLIT_LABELS) as Array<keyof SplitsReport["splits"]>).map((key) => {
            const summary = splits.splits[key];
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
      </div>
    </main>
  );
}
