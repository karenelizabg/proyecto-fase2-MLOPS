import type { ReactNode } from "react";
import { PipelineNav } from "./PipelineNav";

/** Shell compartido por las 6 pantallas del pipeline. Ver PipelineNav. */
export function PipelineLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col bg-canvas lg:flex-row">
      <PipelineNav />
      <div className="flex min-w-0 flex-1 flex-col">{children}</div>
    </div>
  );
}
