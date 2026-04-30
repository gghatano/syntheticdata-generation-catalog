import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { TimeSeriesComparisonChart } from "./TimeSeriesComparisonChart";
import type { TimeSeriesData } from "../types/timeseries";

const mockData: TimeSeriesData = {
  case_id: "iot-sensor-monitoring",
  selected_real_location: "US, New York",
  selected_synth_sequence: "sdv-id-XXXXXX",
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
  note: "テスト用データ",
};

beforeEach(() => {
  vi.resetAllMocks();
});

describe("TimeSeriesComparisonChart", () => {
  it("(a) JSON fetch 成功時、ヘッダー・系列ラベル・拠点情報が表示される", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<TimeSeriesComparisonChart caseId="iot-sensor-monitoring" />);

    await waitFor(() => {
      expect(screen.getByText("時系列比較")).toBeInTheDocument();
    });
    expect(screen.getByText("最高気温 (°F)")).toBeInTheDocument();
    expect(screen.getByText(/US, New York/)).toBeInTheDocument();
    // mean / std サマリーが表示される
    expect(screen.getByText(/real μ=40/)).toBeInTheDocument();
    expect(screen.getByText(/synth μ=57/)).toBeInTheDocument();
    // fetch 先 URL に caseId が含まれる
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("iot-sensor-monitoring.json"));
  });

  it("(b) fetch 失敗時は何も描画しない", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: false, status: 404 });
    vi.stubGlobal("fetch", fetchMock);

    const { container } = render(<TimeSeriesComparisonChart caseId="iot-sensor-monitoring" />);

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalled();
    });

    // ローディング解除後、エラーケースは何も出さない (return null)
    await waitFor(() => {
      expect(screen.queryByText("時系列データを読み込み中...")).not.toBeInTheDocument();
    });
    expect(container.firstChild).toBeNull();
  });
});
