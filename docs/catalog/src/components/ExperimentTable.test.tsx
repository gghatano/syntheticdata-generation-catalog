import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ExperimentTable } from "./ExperimentTable";
import { mockAlgorithms } from "../test/fixtures";

describe("ExperimentTable", () => {
  it("renders experiment rows", () => {
    const algo = mockAlgorithms[1]; // CTGAN with 2 experiments
    render(<ExperimentTable experiments={algo.experiments} />);
    const sdvElements = screen.getAllByText("SDV");
    expect(sdvElements.length).toBeGreaterThanOrEqual(1);
  });

  it("renders quality score", () => {
    const algo = mockAlgorithms[0]; // GaussianCopula
    render(<ExperimentTable experiments={algo.experiments} />);
    // ExperimentTable renders as 0.817 (3 decimal places)
    expect(screen.getByText("0.817")).toBeInTheDocument();
  });

  it("renders nothing when experiments is empty", () => {
    const { container } = render(<ExperimentTable experiments={[]} />);
    // Should still render the table structure but with no data rows
    const rows = container.querySelectorAll("tbody tr");
    expect(rows).toHaveLength(0);
  });

  it("shows baseline reference note", () => {
    const algo = mockAlgorithms[0];
    render(<ExperimentTable experiments={algo.experiments} />);
    const matches = screen.getAllByText(/ベースライン/);
    expect(matches.length).toBeGreaterThanOrEqual(1);
  });
});
