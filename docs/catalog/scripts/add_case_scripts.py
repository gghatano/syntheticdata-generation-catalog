"""experiment-cases.json の各事例に scripts フィールドを追加する。

Issue #63 対応。手書きで JSON を編集すると壊れやすいので、Python で一括更新する。
実行: python3 docs/catalog/scripts/add_case_scripts.py
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
CASES_JSON = os.path.join(ROOT, 'docs/catalog/public/data/experiment-cases.json')

SCRIPTS_BY_CASE: dict[str, list[dict]] = {
    "adult-census-anonymization": [
        {"role": "prepare", "library": "sdv", "path": "libs/sdv/prepare_data.py",
         "description": "Adult Census データセットを取得し全ライブラリ共通の processed CSV に整形"},
        {"role": "synthesize", "library": "sdv", "path": "libs/sdv/run_phase1.py",
         "description": "SDV の GaussianCopula / CTGAN で単一表合成"},
        {"role": "synthesize", "library": "synthcity", "path": "libs/synthcity/run_phase1.py",
         "description": "SynthCity の BayesianNetwork / TVAE / AdsGAN / NFlow で単一表合成"},
        {"role": "synthesize", "library": "ydata", "path": "libs/ydata/run_phase1.py",
         "description": "ydata-synthetic の CTGAN で単一表合成"},
    ],
    "insurance-risk-modeling": [
        {"role": "prepare", "library": "sdv", "path": "libs/sdv/prepare_data.py",
         "description": "SDV demo (insurance) を取得・整形"},
        {"role": "synthesize", "library": "sdv", "path": "libs/sdv/run_additional_experiments.py",
         "description": "GaussianCopula / CTGAN で Insurance データを合成"},
        {"role": "evaluate", "library": "evaluation", "path": "libs/evaluation/eval_insurance.py",
         "description": "SDMetrics + TSTR + DCR による品質・プライバシー評価"},
    ],
    "company-directory": [
        {"role": "prepare", "library": "sdv", "path": "libs/sdv/prepare_data.py",
         "description": "SDV demo (Fake Companies) を取得・整形"},
        {"role": "synthesize", "library": "sdv", "path": "libs/sdv/run_additional_experiments.py",
         "description": "GaussianCopula で Fake Companies データを合成"},
        {"role": "evaluate", "library": "evaluation", "path": "libs/evaluation/eval_fake_companies.py",
         "description": "12行の極小データに対する品質・プライバシー評価"},
    ],
    "hotel-reservation-multitable": [
        {"role": "prepare", "library": "sdv", "path": "libs/sdv/prepare_data.py",
         "description": "SDV demo (Fake Hotels) を取得し複数表メタデータも保存"},
        {"role": "synthesize", "library": "sdv", "path": "libs/sdv/run_phase2.py",
         "description": "SDV HMASynthesizer で hotels / guests を外部キー整合性付きで合成"},
        {"role": "evaluate", "library": "evaluation", "path": "libs/evaluation/eval_hotel.py",
         "description": "FK 整合性チェック + 単表 SDMetrics による評価"},
    ],
    "imdb-movie-database": [
        {"role": "prepare", "library": "sdv", "path": "libs/sdv/prepare_data.py",
         "description": "SDV demo (IMDB Small) を取得し7テーブル分のメタデータを保存"},
        {"role": "synthesize", "library": "sdv", "path": "libs/sdv/run_additional_experiments.py",
         "description": "SDV HMASynthesizer で IMDB 7テーブル + 多対多リレーションを合成"},
        {"role": "evaluate", "library": "evaluation", "path": "libs/evaluation/eval_imdb.py",
         "description": "6リレーションすべての FK 整合性 + 単表 SDMetrics による評価"},
    ],
    "olist-ec-transactions": [
        {"role": "prepare", "library": "sdv", "path": "libs/sdv/prepare_olist.py",
         "description": "Brazilian E-Commerce (Olist) 7テーブルを uniformly sample (5000 customers ベース) し processed に保存"},
        {"role": "synthesize", "library": "sdv", "path": "libs/sdv/run_olist_hma.py",
         "description": "SDV HMASynthesizer で Olist 7/7 テーブルを合成（FK 6本維持）"},
        {"role": "synthesize", "library": "realtabformer", "path": "libs/realtabformer/run_olist.py",
         "description": "REaLTabFormer で orders → order_items の親子1ペアを合成（数値分布精度比較用）"},
        {"role": "evaluate", "library": "evaluation", "path": "libs/evaluation/eval_olist.py",
         "description": "FK 整合性 + 件数分布 + 単変量分布 + 結合 TSTR (review_score 予測) による評価"},
    ],
    "stock-price-timeseries": [
        {"role": "prepare", "library": "sdv", "path": "libs/sdv/prepare_data.py",
         "description": "SDV demo (NASDAQ 100 2019) を取得し時系列メタデータを保存"},
        {"role": "synthesize", "library": "sdv", "path": "libs/sdv/run_phase3.py",
         "description": "SDV PARSynthesizer (128ep) で銘柄別の日次株価時系列を合成"},
        {"role": "evaluate", "library": "evaluation", "path": "libs/evaluation/eval_stock.py",
         "description": "SDMetrics + 自己相関乖離 + DCR による評価"},
    ],
    "iot-sensor-monitoring": [
        {"role": "evaluate", "library": "evaluation", "path": "libs/evaluation/eval_iot_weather.py",
         "description": "Daily Weather 2020 の取得・PAR 64ep による合成・SDMetrics + 自己相関 + DCR 評価を1スクリプトで実行"},
    ],
}


def main() -> None:
    with open(CASES_JSON, encoding='utf-8') as f:
        cases = json.load(f)

    updated = 0
    skipped: list[str] = []
    for case in cases:
        cid = case.get('id')
        if cid in SCRIPTS_BY_CASE:
            case['scripts'] = SCRIPTS_BY_CASE[cid]
            updated += 1
        else:
            skipped.append(cid)

    with open(CASES_JSON, 'w', encoding='utf-8') as f:
        json.dump(cases, f, indent=2, ensure_ascii=False)
        f.write('\n')

    print(f"Updated {updated} cases.")
    if skipped:
        print(f"Skipped (no mapping): {skipped}")


if __name__ == '__main__':
    main()
