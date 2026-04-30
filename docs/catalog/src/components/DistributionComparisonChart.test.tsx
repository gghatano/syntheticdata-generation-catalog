import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { DistributionComparisonChart } from "./DistributionComparisonChart";
import type { DistributionData } from "../types/distribution";

const mockNumericData: DistributionData = {
  case_id: "adult-census-anonymization",
  selected_synth: {
    algorithm: "CTGAN",
    library: "SDV",
    csv: "results/phase1/sdv_ctgan.csv",
  },
  real_source: { csv: "data/processed/d1_adult.csv", rows: 32561 },
  synth_source: { rows: 32561 },
  items: [
    {
      type: "numeric",
      column: "age",
      label: "年齢",
      unit: "歳",
      real_mean: 38.5,
      synth_mean: 39.1,
      real_std: 13.6,
      synth_std: 12.9,
      bins: [
        { x: 17, x_end: 25, real: 5000, synth: 4800 },
        { x: 25, x_end: 35, real: 9000, synth: 9100 },
      ],
    },
    {
      type: "categorical",
      column: "workclass",
      label: "雇用形態",
      categories: [
        { name: "Private", real_pct: 0.74, synth_pct: 0.71, real_count: 24000, synth_count: 23100 },
        { name: "Self-emp", real_pct: 0.11, synth_pct: 0.13, real_count: 3500, synth_count: 4200 },
      ],
      total_categories: 8,
    },
  ],
  note: "テスト用データ",
};

beforeEach(() => {
  vi.resetAllMocks();
});

describe("DistributionComparisonChart", () => {
  it("(a) JSON 取得成功時、ヘッダー・各 item のラベル・統計サマリーが表示される", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockNumericData),
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<DistributionComparisonChart caseId="adult-census-anonymization" />);

    await waitFor(() => {
      expect(screen.getByText("分布比較")).toBeInTheDocument();
    });
    expect(screen.getByText("年齢")).toBeInTheDocument();
    expect(screen.getByText(/real μ=38.5/)).toBeInTheDocument();
    expect(screen.getByText(/synth μ=39.1/)).toBeInTheDocument();
    expect(screen.getByText("雇用形態")).toBeInTheDocument();
    expect(screen.getByText(/上位 2 \/ 全 8 カテゴリ/)).toBeInTheDocument();

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("adult-census-anonymization.json")
    );
  });

  it("(b) fetch 失敗時は何も描画しない", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: false, status: 404 });
    vi.stubGlobal("fetch", fetchMock);

    const { container } = render(<DistributionComparisonChart caseId="missing" />);

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalled();
    });
    await waitFor(() => {
      expect(screen.queryByText("分布データを読み込み中...")).not.toBeInTheDocument();
    });
    expect(container.firstChild).toBeNull();
  });
});
