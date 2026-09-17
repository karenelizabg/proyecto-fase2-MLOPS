import { z } from "zod";

/**
 * Espeja `app/presentation/contracts.py` (P2-12, forma v1.0 congelada).
 * Igual que con el backend real: nunca se confía en el tipo que TypeScript
 * infiere del JSON importado, se valida con estos schemas y el tipo de cada
 * componente sale de z.infer<typeof schema>.
 */

const identifierSchema = z
  .string()
  .regex(/^[A-Za-z0-9][A-Za-z0-9._-]*$/, "dataset_version/check_name tiene un formato inválido");

export const qualityCheckSchema = z.object({
  check_name: identifierSchema,
  passed: z.boolean(),
  metric_value: z.number(),
  details: z.record(z.string(), z.unknown()).default({}),
  action: z.enum(["warn", "fail"]),
});
export type QualityCheck = z.infer<typeof qualityCheckSchema>;

export const qualityReportSchema = z.object({
  schema_version: z.literal("1.0"),
  dataset_version: identifierSchema,
  status: z.enum(["passed", "warning", "failed"]),
  checks: z.array(qualityCheckSchema).min(1),
});
export type QualityReport = z.infer<typeof qualityReportSchema>;

const splitSummarySchema = z.object({
  image_count: z.number().int().min(0),
  ratio: z.number().min(0).max(1),
});

export const splitsReportSchema = z.object({
  schema_version: z.literal("1.0"),
  dataset_version: identifierSchema,
  total_images: z.number().int().positive(),
  splits: z.object({
    train: splitSummarySchema,
    validation: splitSummarySchema,
    test: splitSummarySchema,
  }),
});
export type SplitsReport = z.infer<typeof splitsReportSchema>;

const datasetReleaseSchema = z.object({
  dataset_version: identifierSchema,
  quality_file: z.string(),
  splits_file: z.string(),
});

export const versionsReportSchema = z.object({
  schema_version: z.literal("1.0"),
  releases: z.array(datasetReleaseSchema),
});
export type VersionsReport = z.infer<typeof versionsReportSchema>;
