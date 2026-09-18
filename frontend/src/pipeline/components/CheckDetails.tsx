import { z } from "zod";
import type { QualityCheck } from "../schemas";

const criterionSchema = z.object({ threshold: z.number(), operator: z.string() });
const classesSchema = z.array(z.object({ category_name: z.string(), image_count: z.number() }));
const samplesSchema = z.array(
  z.object({ image_id: z.number(), annotation_id: z.number().optional() })
);
const smallBoxSchema = z.object({
  width_px: z.number(),
  height_px: z.number(),
  operator: z.string(),
  combination: z.literal("and"),
});
const pairsSchema = z.array(
  z.object({
    image_id_a: z.number(),
    image_id_b: z.number(),
    similarity: z.number(),
    split_a: z.string().optional(),
    split_b: z.string().optional(),
    hamming_distance: z.number().optional(),
  })
);

export function CheckCriterion({ check }: Readonly<{ check: QualityCheck }>) {
  const criterion = criterionSchema.safeParse(check.details.criterion);
  return (
    <>
      {criterion.success
        ? `${criterion.data.operator} ${criterion.data.threshold}`
        : "Criterio no disponible"}
    </>
  );
}

export function CheckDetails({ check }: Readonly<{ check: QualityCheck }>) {
  const details = check.details;
  const classes = classesSchema.safeParse(
    details.images_per_category ?? details.classes_below_minimum
  );
  const samples = samplesSchema.safeParse(details.offending_samples);
  const pairs = pairsSchema.safeParse(details.image_pairs);
  const smallBox = smallBoxSchema.safeParse(details.small_box_detection);
  return (
    <div className="space-y-2 text-sm">
      {classes.success && (
        <ul>
          {classes.data.map((entry) => (
            <li key={entry.category_name}>
              {entry.category_name}: {entry.image_count} imágenes
            </li>
          ))}
        </ul>
      )}
      {smallBox.success && (
        <p>
          Caja pequeña: ancho {smallBox.data.operator} {smallBox.data.width_px} px y alto{" "}
          {smallBox.data.operator} {smallBox.data.height_px} px.
        </p>
      )}
      {typeof details.similarity_threshold === "number" && (
        <p>
          Detección pHash: similitud ≥ {details.similarity_threshold}. El criterio de aprobación
          cuenta pares, no similitud.
        </p>
      )}
      {pairs.success && pairs.data.length > 0 && (
        <details>
          <summary>Pares detectados ({pairs.data.length})</summary>
          <ul>
            {pairs.data.map((pair) => (
              <li key={`${pair.image_id_a}-${pair.image_id_b}`}>
                Imágenes {pair.image_id_a} / {pair.image_id_b}: similitud {pair.similarity}
                {pair.split_a && pair.split_b && (
                  <span>
                    {" "}
                    · {pair.split_a} → {pair.split_b}
                  </span>
                )}
                {pair.hamming_distance !== undefined && (
                  <span> · Hamming: {pair.hamming_distance}</span>
                )}
              </li>
            ))}
          </ul>
        </details>
      )}
      {samples.success && samples.data.length > 0 && (
        <details>
          <summary>Muestras afectadas ({samples.data.length})</summary>
          <ul>
            {samples.data.map((sample) => (
              <li key={`${sample.image_id}-${sample.annotation_id}`}>
                Imagen {sample.image_id}, anotación {sample.annotation_id ?? "no indicada"}
              </li>
            ))}
          </ul>
        </details>
      )}
      {typeof details.std_center_x === "number" && (
        <p>Dispersión horizontal: {details.std_center_x}</p>
      )}
      {typeof details.std_center_y === "number" && (
        <p>Dispersión vertical: {details.std_center_y}</p>
      )}
    </div>
  );
}
