import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { TimeSeriesComparisonChart } from "./TimeSeriesComparisonChart";
import type { TimeSeriesData } from "../types/timeseries";

const mockData: TimeSeriesData = {
  case_id: "iot-sensor-monitoring",
  pairs: [
    {
      label: "US, New York",
      real_id: "US, New York",
      synth_id: "sdv-id-XXXXXX",
      match_reason: "real 平均 40 に最も近い synth として sdv-id-XXXXXX を選択",
      date_range_real: { start: "2019-12-31", end: "2020-04-20" },
      sequence_length: 3,
      series: [
        {
          name: "temperatureHigh",
          label: "最高気温 (°F)",
          unit: "°F",
          real_mean: 40,
          synth_mean: 57,
          real_std: 10,
          synth_std: 14,
          points: [
            { x: 0, real: 32, synth: 50 },
            { x: 1, real: 35, synth: 60 },
            { x: 2, real: 40, synth: 55 },
          ],
        },
      ],
    },
  ],
  aggregate: {
    note: "全 122 拠点 × 112 日と 10 synth シーケンスを比較",
    series: [
      {
        name: "temperatureHigh",
        label: "最高気温 (°F)",
        unit: "°F",
        real_count: 13664,
        synth_count: 1120,
        real_mean: 50,
        synth_mean: 47,
        real_std: 18,
        synth_std: 14,
        bins: [
          { x: 0, x_end: 20, real: 100, synth: 80 },
          { x: 20, x_end: 40, real: 500, synth: 400 },
        ],
      },
    ],
  },
  note: "テスト用データ。pairs と aggregate を含む。",
};

beforeEach(() => {
  vi.resetAllMocks();
});

describe("TimeSeriesComparisonChart", () => {
  it("(a) JSON fetch 成功時、ヘッダー / pair / aggregate が表示される", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<TimeSeriesComparisonChart caseId="iot-sensor-monitoring" />);

    await waitFor(() => {
      expect(screen.getByText("時系列比較")).toBeInTheDocument();
    });
    // Pair label / real_id とも "US, New York" を含む（h3 と説明文の両方）
    expect(screen.getAllByText(/US, New York/).length).toBeGreaterThan(0);
    // Match reason
    expect(screen.getByText(/最も近い synth として/)).toBeInTheDocument();
    // Aggregate section header
    expect(screen.getByText("全体分布の比較")).toBeInTheDocument();
    expect(screen.getByText(/全 122 拠点/)).toBeInTheDocument();

    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("iot-sensor-monitoring.json"));
  });

  it("(b) fetch 失敗時は何も描画しない", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: false, status: 404 });
    vi.stubGlobal("fetch", fetchMock);

    const { container } = render(<TimeSeriesComparisonChart caseId="iot-sensor-monitoring" />);

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(screen.queryByText("時系列データを読み込み中...")).not.toBeInTheDocument();
    });
    expect(container.firstChild).toBeNull();
  });

  it("(c) 複数 pair (例: stock 3 銘柄) を順に描画する", async () => {
    const stockData: TimeSeriesData = {
      case_id: "stock-price-timeseries",
      pairs: [
        { ...mockData.pairs[0], label: "小型株 (FOXA)", real_id: "FOXA", synth_id: "AAAJ" },
        { ...mockData.pairs[0], label: "中型株 (ROST)", real_id: "ROST", synth_id: "AAAA" },
        { ...mockData.pairs[0], label: "大型株 (ILMN)", real_id: "ILMN", synth_id: "AAAI" },
      ],
      note: "3 ペア比較",
    };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve(stockData) }));

    render(<TimeSeriesComparisonChart caseId="stock-price-timeseries" />);

    await waitFor(() => {
      expect(screen.getByText("小型株 (FOXA)")).toBeInTheDocument();
    });
    expect(screen.getByText("中型株 (ROST)")).toBeInTheDocument();
    expect(screen.getByText("大型株 (ILMN)")).toBeInTheDocument();
  });
});
