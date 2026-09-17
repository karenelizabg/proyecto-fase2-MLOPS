import { Navigate, Route, Routes } from "react-router-dom";
import { AnnotateScreen } from "@/components/annotate/AnnotateScreen";
import { AppLayout } from "@/components/layout/AppLayout";
import { UploadScreen } from "@/components/upload/UploadScreen";
import { DashboardPage } from "@/pages/Dashboard";
import { SearchPage } from "@/pages/SearchPage";
import { PipelineLayout } from "@/pipeline/PipelineLayout";
import { AnalyzersPage } from "@/pipeline/pages/Analyzers";
import { CopilotPage } from "@/pipeline/pages/Copilot";
import { OverviewPage } from "@/pipeline/pages/Overview";
import { SettingsPage } from "@/pipeline/pages/Settings";
import { SplitsPage } from "@/pipeline/pages/Splits";
import { VersionsPage } from "@/pipeline/pages/Versions";

export function App(): JSX.Element {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route
        path="/dashboard"
        element={
          <AppLayout>
            <DashboardPage />
          </AppLayout>
        }
      />
      {/* SearchPage se envuelve con AppLayout internamente (no aquí), porque
          necesita pasarle su propio contenido de filtros como sidebarExtra
          — ver SearchPage.tsx. */}
      <Route path="/search" element={<SearchPage />} />
      <Route
        path="/upload"
        element={
          <AppLayout>
            <UploadScreen />
          </AppLayout>
        }
      />
      {/* Annotate es un modo de enfoque de pantalla completa a propósito: sin
          nav global, con su propio botón "Volver". Ver GlobalNav.tsx. */}
      <Route path="/annotate/:imageId" element={<AnnotateScreen />} />

      {/* P2-14: dashboard de calidad de dataset (Frente 7), con su propio
          nav (PipelineNav) — producto distinto al portal de anotación de
          arriba, ver PipelineLayout.tsx. */}
      <Route path="/pipeline" element={<Navigate to="/pipeline/overview" replace />} />
      <Route
        path="/pipeline/overview"
        element={
          <PipelineLayout>
            <OverviewPage />
          </PipelineLayout>
        }
      />
      <Route
        path="/pipeline/analyzers"
        element={
          <PipelineLayout>
            <AnalyzersPage />
          </PipelineLayout>
        }
      />
      <Route
        path="/pipeline/splits"
        element={
          <PipelineLayout>
            <SplitsPage />
          </PipelineLayout>
        }
      />
      <Route
        path="/pipeline/versions"
        element={
          <PipelineLayout>
            <VersionsPage />
          </PipelineLayout>
        }
      />
      <Route
        path="/pipeline/copilot"
        element={
          <PipelineLayout>
            <CopilotPage />
          </PipelineLayout>
        }
      />
      <Route
        path="/pipeline/settings"
        element={
          <PipelineLayout>
            <SettingsPage />
          </PipelineLayout>
        }
      />

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
