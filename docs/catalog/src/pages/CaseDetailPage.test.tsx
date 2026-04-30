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
  scripts: [
    {
      role: "prepare",
      library: "sdv",
      path: "libs/sdv/prepare_data.py",
      description: "Adult Census データセットを取得し processed CSV に整形",
    },
    {
      role: "synthesize",
      library: "sdv",
      path: "libs/sdv/run_phase1.py",
    },
  ],
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

    // スクリプトセクションが描画されること
    expect(screen.getByText("使用したスクリプト")).toBeInTheDocument();
    expect(screen.getByText("データ準備")).toBeInTheDocument();
    expect(screen.getByText("合成")).toBeInTheDocument();
    expect(screen.getByText("libs/sdv/prepare_data.py")).toBeInTheDocument();

    // GitHub blob/raw URL が組み立てられていること
    const blobLink = screen.getAllByRole("link", { name: /prepare_data.py を GitHub で表示/i })[0];
    expect(blobLink).toHaveAttribute(
      "href",
      "https://github.com/gghatano/syntheticdata-generation-catalog/blob/main/libs/sdv/prepare_data.py"
    );
    const rawLink = screen.getAllByRole("link", { name: /prepare_data.py をダウンロード/i })[0];
    expect(rawLink).toHaveAttribute(
      "href",
      "https://github.com/gghatano/syntheticdata-generation-catalog/raw/main/libs/sdv/prepare_data.py"
    );
  });

  it("(c2) scripts が未指定なら使用したスクリプトセクションは描画されない", () => {
    const caseWithoutScripts: ExperimentCase = { ...mockCase, scripts: undefined };
    mockUseExperimentCases.mockReturnValue({
      cases: [caseWithoutScripts],
      loading: false,
      error: null,
    });

    renderWithRouter("adult-census-anonymization");

    expect(screen.queryByText("使用したスクリプト")).not.toBeInTheDocument();
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
