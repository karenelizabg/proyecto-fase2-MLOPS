import {
  Bot,
  Gauge,
  LayoutDashboard,
  ScanSearch,
  Settings as SettingsIcon,
  SplitSquareHorizontal,
} from "lucide-react";
import type { ComponentType, SVGProps } from "react";
import { NavLink } from "react-router-dom";

interface NavItem {
  label: string;
  to: string;
  icon: ComponentType<SVGProps<SVGSVGElement>>;
}

const NAV_ITEMS: NavItem[] = [
  { label: "Overview", to: "/pipeline/overview", icon: LayoutDashboard },
  { label: "Analyzers", to: "/pipeline/analyzers", icon: ScanSearch },
  { label: "Splits", to: "/pipeline/splits", icon: SplitSquareHorizontal },
  { label: "Versions", to: "/pipeline/versions", icon: Gauge },
  { label: "Copilot", to: "/pipeline/copilot", icon: Bot },
  { label: "Settings", to: "/pipeline/settings", icon: SettingsIcon },
];

/**
 * Nav propio del dashboard de calidad de dataset (Frente 7, P2-14) — a
 * propósito NO es el mismo `GlobalNav` del portal de anotación P1 (distinto
 * producto: aquí se navegan los contratos JSON del pipeline, no imágenes).
 */
export function PipelineNav() {
  return (
    <aside className="flex w-full shrink-0 flex-col border-b border-border bg-sidebar lg:h-screen lg:w-64 lg:overflow-y-auto lg:border-b-0 lg:border-r">
      <div className="flex items-center gap-2 px-5 py-5">
        <span className="h-2.5 w-2.5 shrink-0 rounded-full bg-accent-mint" aria-hidden />
        <span className="truncate text-sm font-semibold text-ink">Dataset Quality Pipeline</span>
      </div>

      <nav className="flex gap-1 overflow-x-auto px-3 pb-3 lg:flex-col lg:overflow-visible lg:px-3 lg:pb-6">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex shrink-0 items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-accent-lilac-soft text-accent-lilac"
                    : "text-ink-muted hover:bg-surface hover:text-ink"
                }`
              }
            >
              <Icon className="h-4 w-4 shrink-0" aria-hidden />
              <span className="whitespace-nowrap">{item.label}</span>
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}
