import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { LibraryComparisonChart } from "./LibraryComparisonChart";
import type { Experiment } from "../types/algorithm";

const ctganExperiments: Experiment[] = [
  {
    id: "phase1_sdv_ctgan",
    library: "SDV",
    library_version: "1.27.0",
    params: { epochs: 100 },
    dataset: "d1_adult",
    data_type: "single_table",
    phase: "phase1",
    metrics: {
      quality_score: 0.86,
      tstr_f1: 0.82,
      dcr_mean: 0.34,
      time_sec: 325.2,
    },
  },
  {
    id: "phase1_synthcity_ctgan",
    library: "SynthCity",
    library_version: "0.2.7",
    params: {},
    dataset: "d1_adult",
    data_type: "single_table",
    phase: "phase1",
    metrics: {
      quality_score: 0.74,
      tstr_f1: 0.78,
      dcr_mean: 0.29,
      time_sec: 200.0,
    },
  },
  {
    id: "phase1_ydata_ctgan",
    library: "ydata-synthetic",
    library_version: "1.4.0",
    params: { epochs: 100 },
    dataset: "d1_adult",
    data_type: "single_table",
    phase: "phase1",
    metrics: {
      quality_score: 0.83,
      tstr_f1: 0.81,
      dcr_mean: 0.26,
      time_sec: 1464.3,
    },
  },
];

describe("LibraryComparisonChart", () => {
  it("(a) 2+ ライブラリが揃っている場合、ヘッダー / インサイト / テーブルが表示される", () => {
    render(<LibraryComparisonChart experiments={ctganExperiments} algorithmName="CTGAN" />);

    expect(screen.getByText("ライブラリ間比較")).toBeInTheDocument();

    // ライブラリ名がテーブルに表示される
    expect(screen.getByText("SDV")).toBeInTheDocument();
    expect(screen.getByText("SynthCity")).toBeInTheDocument();
    expect(screen.getByText("ydata-synthetic")).toBeInTheDocument();

    // インサイトが Quality 最高(SDV 0.86) と最低(SynthCity 0.74) を引用
    const insightHits = screen.getAllByText(/同じ CTGAN でも.*SDV.*Quality 0\.86.*SynthCity.*Quality 0\.74/);
    expect(insightHits.length).toBeGreaterThan(0);
  });

  it("(b) 1 ライブラリのみの場合は描画しない", () => {
    const { container } = render(
      <LibraryComparisonChart
        experiments={[ctganExperiments[0]]}
        algorithmName="CTGAN"
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it("(c) 同一ライブラリで複数 experiment がある場合、Quality 最高のものを代表値に採用", () => {
    const exps: Experiment[] = [
      ...ctganExperiments,
      {
        id: "phase1_sdv_ctgan_300ep",
        library: "SDV",
        library_version: "1.27.0",
        params: { epochs: 300 },
        dataset: "d1_adult",
        data_type: "single_table",
        phase: "phase1",
        metrics: {
          quality_score: 0.91,
          tstr_f1: 0.85,
          dcr_mean: 0.30,
          time_sec: 980.0,
        },
      },
    ];
    render(<LibraryComparisonChart experiments={exps} algorithmName="CTGAN" />);
    // SDV 行に Quality 0.91 が表示される
    expect(screen.getByText("0.910")).toBeInTheDocument();
    // 実験数 2 が SDV 行に表示
    expect(screen.getAllByText("2").length).toBeGreaterThanOrEqual(1);
  });
});
