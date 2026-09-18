import { StatCard } from "@/components/dashboard/StatCard";
import type { SplitsReport } from "../schemas";

export function SplitSummary({ report }: Readonly<{ report: SplitsReport }>) {
  return (
    <section aria-label={`Splits de ${report.dataset_version}`}>
      <p className="mb-4">
        {report.total_images} imágenes · {report.dataset_version}
      </p>
      <div className="grid gap-4 sm:grid-cols-3">
        {(["train", "validation", "test"] as const).map((name) => (
          <StatCard
            key={name}
            label={`${name} (${Number((report.splits[name].ratio * 100).toFixed(4))}%)`}
            value={report.splits[name].image_count}
            accent="lilac"
          />
        ))}
      </div>
    </section>
  );
}
