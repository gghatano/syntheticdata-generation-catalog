import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, act } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { CaseDetailPage } from "./CaseDetailPage";
import type { ExperimentCase } from "../types/experiment-case";

// useExperimentCases フックをモック
vi.mock("../hooks/useExperimentCases");
import { useExperimentCases } from "../hooks/useExperimentCases";
const mockUseExperimentCases = vi.mocked(useExperimentCases);

// テスト用 fixture（adult-census-anonymization の実データ構造を踏襲）
const mockCase: ExperimentCase = {
  id: "adult-census-anonymization",
  title: "顧客属性データの合成（匿名化・テストデータ生成）",
  data_category: "single_table_master",
  scenario: {
    description: "個人属性を含む顧客マスタデータを合成する。",
    use_case: "テストデータ生成・匿名化",
  },
  dataset: {
    name: "Adult Census",
    source_url: "https://archive.ics.uci.edu/dataset/2/adult",
    rows: 32561,
    columns: 15,
    features: ["年齢", "職業", "学歴"],
  },
  results: [
    {
      algorithm_id: "ctgan",
      algorithm_name: "CTGAN",
      library: "SDV",
      params: { epochs: 100 },
      metrics: {
        quality_score: 0.86,
        tstr_f1: 0.8203,
        dcr_mean: 0.3438,
        time_sec: 325.24,
      },
      privacy_risk: "medium",
    },
    {
      algorithm_id: "gaussiancopula",
      algorithm_name: "GaussianCopula",
      library: "SDV",
      params: {},
      metrics: {
        quality_score: 0.8168,
        tstr_f1: 0.6555,
        dcr_mean: 0.533,
        time_sec: 5.94,
      },
      privacy_risk: "low",
    },
  ],
  recommendation: "CTGAN が最もバランスが良い。",
};

// MemoryRouter で指定 id のルートにレンダーするヘルパー
function renderWithRouter(id: string) {
  return render(
    <MemoryRouter initialEntries={[`/case/${id}`]}>
      <Routes>
        <Route path="/case/:id" element={<CaseDetailPage />} />
      </Routes>
    </MemoryRouter>
  );
}

beforeEach(() => {
  vi.resetAllMocks();
});

describe("CaseDetailPage", () => {
  it("(a) loading 中は「読み込み中...」が表示される", () => {
    mockUseExperimentCases.mockReturnValue({
      cases: [],
      loading: true,
      error: null,
    });

    renderWithRouter("adult-census-anonymization");

    expect(screen.getByText("読み込み中...")).toBeInTheDocument();
  });

  it("(b) 存在しない id の場合「事例が見つかりません」が表示される", () => {
    mockUseExperimentCases.mockReturnValue({
      cases: [mockCase],
      loading: false,
      error: null,
    });

    renderWithRouter("non-existent-id");

    expect(screen.getByText("事例が見つかりません")).toBeInTheDocument();
  });

  it("(c) 有効な id の場合、事例タイトルと結果テーブルが描画されクラッシュしない", () => {
    mockUseExperimentCases.mockReturnValue({
      cases: [mockCase],
      loading: false,
      error: null,
    });

    renderWithRouter("adult-census-anonymization");

    // タイトルが表示されること
    expect(
      screen.getByText("顧客属性データの合成（匿名化・テストデータ生成）")
    ).toBeInTheDocument();

    // 結果テーブルに手法名が表示されること（MetricsBarChart などで複数表示されることがあるため getAllByText を使用）
    expect(screen.getAllByText("CTGAN").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("GaussianCopula").length).toBeGreaterThanOrEqual(1);
  });

  it("(d) loading → resolved 遷移を通してクラッシュしない", () => {
    // 最初は loading=true
    mockUseExperimentCases.mockReturnValue({
      cases: [],
      loading: true,
      error: null,
    });

    const { rerender } = render(
      <MemoryRouter initialEntries={["/case/adult-census-anonymization"]}>
        <Routes>
          <Route path="/case/:id" element={<CaseDetailPage />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText("読み込み中...")).toBeInTheDocument();

    // loading が完了しデータが返ってくる
    mockUseExperimentCases.mockReturnValue({
      cases: [mockCase],
      loading: false,
      error: null,
    });

    act(() => {
      rerender(
        <MemoryRouter initialEntries={["/case/adult-census-anonymization"]}>
          <Routes>
            <Route path="/case/:id" element={<CaseDetailPage />} />
          </Routes>
        </MemoryRouter>
      );
    });

    // クラッシュせずタイトルが表示されること
    expect(
      screen.getByText("顧客属性データの合成（匿名化・テストデータ生成）")
    ).toBeInTheDocument();
  });
});
