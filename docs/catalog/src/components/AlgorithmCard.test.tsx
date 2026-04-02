import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { AlgorithmCard } from "./AlgorithmCard";
import { mockAlgorithms } from "../test/fixtures";

function renderCard(index = 0) {
  return render(
    <BrowserRouter>
      <AlgorithmCard algorithm={mockAlgorithms[index]} />
    </BrowserRouter>
  );
}

describe("AlgorithmCard", () => {
  it("renders algorithm name", () => {
    renderCard(0);
    expect(screen.getByText("GaussianCopula")).toBeInTheDocument();
  });

  it("renders category badge", () => {
    renderCard(0);
    expect(screen.getByText("コピュラ")).toBeInTheDocument();
  });

  it("renders library badges", () => {
    renderCard(1); // CTGAN has 3 libraries
    expect(screen.getByText("SDV")).toBeInTheDocument();
    expect(screen.getByText("SynthCity")).toBeInTheDocument();
    expect(screen.getByText("ydata")).toBeInTheDocument();
  });

  it("renders privacy risk badge", () => {
    renderCard(0); // low risk
    expect(screen.getByText("低リスク")).toBeInTheDocument();
  });

  it("renders link to detail page", () => {
    renderCard(0);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", expect.stringContaining("/algorithm/gaussiancopula"));
  });

  it("renders data type badges", () => {
    renderCard(0);
    expect(screen.getByText("単一表")).toBeInTheDocument();
  });
});
