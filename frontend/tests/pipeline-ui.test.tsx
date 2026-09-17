import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";
import { App } from "../src/App";

afterEach(() => {
  cleanup();
});

function renderPipelineAt(path: string) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
}

describe("SPEC-PIPELINE-UI-001 - esqueleto de las 6 pantallas del pipeline (P2-14)", () => {
  it("Overview muestra datos que vienen de quality.json/splits.json/versions.json, no hardcodeados", () => {
    renderPipelineAt("/pipeline/overview");

    expect(screen.getByRole("heading", { name: "Overview" })).toBeInTheDocument();
    expect(screen.getByText(/demo-v1\.0\.0/)).toBeInTheDocument();
    // total_images de splits.json (separador de miles en formato "es")
    expect(screen.getByText((1200).toLocaleString("es"))).toBeInTheDocument();
    // checks.length de quality.json
    expect(screen.getByText("5")).toBeInTheDocument();
  });

  it("navega a las otras 5 pantallas desde el nav del pipeline", () => {
    renderPipelineAt("/pipeline/overview");

    fireEvent.click(screen.getByRole("link", { name: "Analyzers" }));
    expect(screen.getByRole("heading", { name: "Analyzers" })).toBeInTheDocument();
    // check_name de quality.json, no un texto inventado en el componente
    expect(screen.getByText("max_small_object_ratio")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("link", { name: "Splits" }));
    expect(screen.getByRole("heading", { name: "Splits" })).toBeInTheDocument();
    // image_count de splits.json
    expect(screen.getByText("840")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("link", { name: "Versions" }));
    expect(screen.getByRole("heading", { name: "Versions" })).toBeInTheDocument();
    expect(screen.getByText("demo-v1.0.0")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("link", { name: "Copilot" }));
    expect(screen.getByRole("heading", { name: "Copilot" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("link", { name: "Settings" }));
    expect(screen.getByRole("heading", { name: "Settings" })).toBeInTheDocument();
    // dataset activo también sale de versions.json
    expect(screen.getByText("demo-v1.0.0")).toBeInTheDocument();
  });

  it("/pipeline redirige a /pipeline/overview", () => {
    renderPipelineAt("/pipeline");
    expect(screen.getByRole("heading", { name: "Overview" })).toBeInTheDocument();
  });
});
