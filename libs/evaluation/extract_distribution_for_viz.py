"""Issue #77: 各事例ページの分布・振る舞い可視化用 JSON を生成する。

real CSV と synth CSV から、事例ごとに指定した数値列（histogram）と
カテゴリ列（bar chart）の分布を抽出し、軽量 JSON として書き出す。

出力先:
  docs/catalog/public/data/distribution/<case_id>.json

実行:
  cd libs/evaluation && uv run python extract_distribution_for_viz.py

事例ごとの列マッピングは下方の CASES に集約。新規事例を追加する場合は CASES に項目を足す。
"""
import json
import os
import sys
from typing import Callable, Optional

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..', '..')
OUTPUT_DIR = os.path.join(ROOT, 'docs/catalog/public/data/distribution')

NUM_BINS = 20
TOP_CATEGORIES = 8


def numeric_bins(real: pd.Series, synth: pd.Series, *, n_bins: int = NUM_BINS) -> list[dict]:
    """real と synth の値域を合わせて bin を切り、それぞれの度数を返す。"""
    real_clean = real.dropna().astype(float)
    synth_clean = synth.dropna().astype(float)
    combined = pd.concat([real_clean, synth_clean])
    if combined.empty:
        return []
    # 極小データは bin を絞る（real 30 行未満なら bin 数を 8 に）
    effective_bins = min(n_bins, max(4, len(real_clean) // 4)) if len(real_clean) < 100 else n_bins
    lo, hi = float(combined.min()), float(combined.max())
    if lo == hi:
        # 値が単一なら 1 bin
        return [{
            'x': round(lo, 4),
            'x_end': round(hi, 4),
            'real': int(len(real_clean)),
            'synth': int(len(synth_clean)),
        }]
    edges = np.linspace(lo, hi, effective_bins + 1)
    real_counts, _ = np.histogram(real_clean, bins=edges)
    synth_counts, _ = np.histogram(synth_clean, bins=edges)
    return [
        {
            'x': round(float(edges[i]), 4),
            'x_end': round(float(edges[i + 1]), 4),
            'real': int(real_counts[i]),
            'synth': int(synth_counts[i]),
        }
        for i in range(effective_bins)
    ]


def categorical_bars(real: pd.Series, synth: pd.Series, *, top_n: int = TOP_CATEGORIES) -> tuple[list[dict], int]:
    """real と synth で頻度上位の値を共通で抽出して比較データを返す。"""
    real_clean = real.dropna().astype(str)
    synth_clean = synth.dropna().astype(str)

    real_counts = real_clean.value_counts()
    synth_counts = synth_clean.value_counts()

    real_total = int(real_counts.sum()) or 1
    synth_total = int(synth_counts.sum()) or 1

    union = pd.concat([
        real_counts.rename('r'),
        synth_counts.rename('s'),
    ], axis=1).fillna(0)
    union['combined'] = union['r'] + union['s']
    union = union.sort_values('combined', ascending=False)

    top = union.head(top_n)
    bars = []
    for name, row in top.iterrows():
        bars.append({
            'name': str(name),
            'real_pct': round(float(row['r']) / real_total, 4),
            'synth_pct': round(float(row['s']) / synth_total, 4),
            'real_count': int(row['r']),
            'synth_count': int(row['s']),
        })
    total_categories = int(len(union))
    return bars, total_categories


def build_numeric_item(real: pd.DataFrame, synth: pd.DataFrame, column: str, label: str, *, unit: str | None = None) -> dict:
    bins = numeric_bins(real[column], synth[column])
    return {
        'type': 'numeric',
        'column': column,
        'label': label,
        'unit': unit or '',
        'real_mean': round(float(real[column].mean()), 4),
        'synth_mean': round(float(synth[column].mean()), 4),
        'real_std': round(float(real[column].std()), 4),
        'synth_std': round(float(synth[column].std()), 4),
        'bins': bins,
    }


def build_categorical_item(real: pd.DataFrame, synth: pd.DataFrame, column: str, label: str) -> dict:
    bars, total = categorical_bars(real[column], synth[column])
    return {
        'type': 'categorical',
        'column': column,
        'label': label,
        'categories': bars,
        'total_categories': total,
    }


def write_json(case_id: str, payload: dict) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = os.path.join(OUTPUT_DIR, f'{case_id}.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write('\n')
    return out


def load_csv(path: str) -> pd.DataFrame | None:
    if not os.path.exists(path):
        return None
    return pd.read_csv(path)


# ============================================================
# 事例ごとの抽出ロジック（CASES）
# ============================================================
# 各関数は (real_path, synth_path, items, library, algorithm) を返す。
# real_path / synth_path が None なら抽出をスキップ。
# ------------------------------------------------------------

def process_adult() -> dict | None:
    real = load_csv(os.path.join(ROOT, 'data/processed/d1_adult.csv'))
    # CTGAN がなければ GaussianCopula にフォールバック
    synth_path = os.path.join(ROOT, 'results/phase1/sdv_ctgan.csv')
    algorithm, library = 'CTGAN', 'SDV'
    if not os.path.exists(synth_path):
        synth_path = os.path.join(ROOT, 'results/phase1/sdv_gaussiancopula.csv')
        algorithm = 'GaussianCopula'
    synth = load_csv(synth_path)
    if real is None or synth is None:
        return None
    items: list[dict] = []
    if 'age' in real.columns and 'age' in synth.columns:
        items.append(build_numeric_item(real, synth, 'age', '年齢', unit='歳'))
    if 'hours-per-week' in real.columns:
        items.append(build_numeric_item(real, synth, 'hours-per-week', '週労働時間', unit='時間'))
    if 'workclass' in real.columns:
        items.append(build_categorical_item(real, synth, 'workclass', '雇用形態'))
    return {
        'case_id': 'adult-census-anonymization',
        'selected_synth': {'algorithm': algorithm, 'library': library, 'csv': os.path.relpath(synth_path, ROOT)},
        'real_source': {'csv': 'data/processed/d1_adult.csv', 'rows': int(len(real))},
        'synth_source': {'rows': int(len(synth))},
        'items': items,
        'note': 'Adult Census の年齢分布と雇用形態の比率を比較。CTGAN は分布の山形を捉えやすい一方、レアカテゴリの比率が崩れることがある。',
    }


def process_insurance() -> dict | None:
    real = load_csv(os.path.join(ROOT, 'data/raw/d_insurance.csv'))
    synth_path = os.path.join(ROOT, 'results/phase1/sdv_gaussiancopula_insurance.csv')
    algorithm, library = 'GaussianCopula', 'SDV'
    if not os.path.exists(synth_path):
        synth_path = os.path.join(ROOT, 'results/phase1/sdv_ctgan_50ep_insurance.csv')
        algorithm = 'CTGAN 50ep'
    synth = load_csv(synth_path)
    if real is None or synth is None:
        return None
    # SDV demo "insurance" は自動車保険のベイズネット由来で全列カテゴリ/真偽値
    items: list[dict] = []
    for col, label in [
        ('Age', '年齢区分'),
        ('SocioEcon', '社会経済層'),
        ('MakeModel', '車種'),
        ('ThisCarCost', 'この車の保険費用'),
    ]:
        if col in real.columns and col in synth.columns:
            items.append(build_categorical_item(real, synth, col, label))
    return {
        'case_id': 'insurance-risk-modeling',
        'selected_synth': {'algorithm': algorithm, 'library': library, 'csv': os.path.relpath(synth_path, ROOT)},
        'real_source': {'csv': 'data/raw/d_insurance.csv', 'rows': int(len(real))},
        'synth_source': {'rows': int(len(synth))},
        'items': items,
        'note': 'SDV demo の insurance は自動車保険のベイズネット表データ（全列カテゴリ）。年齢区分・社会経済層・車種・保険費用の比率を比較。',
    }


def process_company() -> dict | None:
    real = load_csv(os.path.join(ROOT, 'data/raw/d_fake_companies.csv'))
    synth = load_csv(os.path.join(ROOT, 'results/phase1/sdv_gaussiancopula_fake_companies.csv'))
    if real is None or synth is None:
        return None
    items: list[dict] = []
    # company-directory は 12 行と極小。可視化は意味付け的に「年齢 / 勤続年数」程度
    for col, label, unit in [('age', '年齢', '歳'), ('years_employed', '勤続年数', '年'), ('salary', '給与', 'USD')]:
        if col in real.columns and col in synth.columns:
            items.append(build_numeric_item(real, synth, col, label, unit=unit))
    if 'department' in real.columns:
        items.append(build_categorical_item(real, synth, 'department', '部署'))
    return {
        'case_id': 'company-directory',
        'selected_synth': {'algorithm': 'GaussianCopula', 'library': 'SDV', 'csv': 'results/phase1/sdv_gaussiancopula_fake_companies.csv'},
        'real_source': {'csv': 'data/raw/d_fake_companies.csv', 'rows': int(len(real))},
        'synth_source': {'rows': int(len(synth))},
        'items': items,
        'note': '12 行の極小データ。分布比較というより「ダミー値が常識的な範囲に収まっているか」の確認に近い。',
    }


def process_hotel() -> dict | None:
    real = load_csv(os.path.join(ROOT, 'data/processed/d2_guests.csv'))
    synth = load_csv(os.path.join(ROOT, 'results/phase2/sdv_hma_guests.csv'))
    if real is None or synth is None:
        return None
    items: list[dict] = []
    if 'room_rate' in real.columns:
        items.append(build_numeric_item(real, synth, 'room_rate', '宿泊料金 (1泊)', unit='USD'))
    if 'amenities_fee' in real.columns:
        items.append(build_numeric_item(real, synth, 'amenities_fee', '付帯料金', unit='USD'))
    if 'room_type' in real.columns:
        items.append(build_categorical_item(real, synth, 'room_type', '部屋タイプ'))
    return {
        'case_id': 'hotel-reservation-multitable',
        'selected_synth': {'algorithm': 'HMA', 'library': 'SDV', 'csv': 'results/phase2/sdv_hma_guests.csv'},
        'real_source': {'csv': 'data/processed/d2_guests.csv', 'rows': int(len(real))},
        'synth_source': {'rows': int(len(synth))},
        'items': items,
        'note': '複数表 (hotels / guests) のうち件数の多い guests テーブルから抽出。HMA は親 (hotels) の属性と整合した子 (guests) を生成する。',
    }


def process_imdb() -> dict | None:
    real = load_csv(os.path.join(ROOT, 'data/raw/d_imdb_actors.csv'))
    synth = load_csv(os.path.join(ROOT, 'results/phase2/sdv_hma_imdb_actors.csv'))
    if real is None or synth is None:
        return None
    items: list[dict] = []
    # actors テーブル: id, first_name, last_name, gender, film_count
    if 'gender' in real.columns and 'gender' in synth.columns:
        items.append(build_categorical_item(real, synth, 'gender', '性別'))
    if 'film_count' in real.columns and 'film_count' in synth.columns:
        items.append(build_numeric_item(real, synth, 'film_count', '出演本数', unit='本'))
    return {
        'case_id': 'imdb-movie-database',
        'selected_synth': {'algorithm': 'HMA', 'library': 'SDV', 'csv': 'results/phase2/sdv_hma_imdb_actors.csv'},
        'real_source': {'csv': 'data/raw/d_imdb_actors.csv', 'rows': int(len(real))},
        'synth_source': {'rows': int(len(synth))},
        'items': items,
        'note': '7 テーブルのうち最多件数の actors テーブルから抽出。多対多リレーションの整合性は HMA が自動で維持する。',
    }


def process_olist() -> dict | None:
    real = load_csv(os.path.join(ROOT, 'data/processed/olist/order_items.csv'))
    synth = load_csv(os.path.join(ROOT, 'results/phase2_olist/sdv_hma_order_items.csv'))
    if real is None or synth is None:
        return None
    items: list[dict] = []
    if 'price' in real.columns:
        items.append(build_numeric_item(real, synth, 'price', '商品単価', unit='BRL'))
    if 'freight_value' in real.columns:
        items.append(build_numeric_item(real, synth, 'freight_value', '送料', unit='BRL'))
    # products テーブルからカテゴリ
    products_real = load_csv(os.path.join(ROOT, 'data/processed/olist/products.csv'))
    products_synth = load_csv(os.path.join(ROOT, 'results/phase2_olist/sdv_hma_products.csv'))
    if products_real is not None and products_synth is not None and 'product_category_name' in products_real.columns:
        items.append(build_categorical_item(products_real, products_synth, 'product_category_name', '商品カテゴリ'))
    return {
        'case_id': 'olist-ec-transactions',
        'selected_synth': {'algorithm': 'HMA (7/7 tables)', 'library': 'SDV', 'csv': 'results/phase2_olist/sdv_hma_order_items.csv'},
        'real_source': {'csv': 'data/processed/olist/order_items.csv', 'rows': int(len(real))},
        'synth_source': {'rows': int(len(synth))},
        'items': items,
        'note': '7 テーブルすべてを HMA で合成。order_items (price/freight) と products (category) を比較。価格分布は右に長い裾を持つ。',
    }


def process_stock() -> dict | None:
    """株価事例は時系列なので Issue #70 の TimeSeriesComparisonChart を再利用する。
    extract_timeseries_for_viz.py 側でJSON生成するので、ここではスキップ。
    """
    return None


CASES: list[tuple[str, Callable[[], Optional[dict]]]] = [
    ('adult-census-anonymization', process_adult),
    ('insurance-risk-modeling', process_insurance),
    ('company-directory', process_company),
    ('hotel-reservation-multitable', process_hotel),
    ('imdb-movie-database', process_imdb),
    ('olist-ec-transactions', process_olist),
    ('stock-price-timeseries', process_stock),
]


def main() -> int:
    success: list[str] = []
    skipped: list[str] = []
    failed: list[tuple[str, str]] = []
    for case_id, fn in CASES:
        try:
            payload = fn()
        except Exception as e:
            failed.append((case_id, repr(e)))
            print(f"[ERROR] {case_id}: {e}")
            continue
        if payload is None:
            skipped.append(case_id)
            print(f"[SKIP] {case_id}: 入力 CSV が見つかりません")
            continue
        out = write_json(case_id, payload)
        size = os.path.getsize(out)
        success.append(case_id)
        print(f"[OK] {case_id} -> {os.path.relpath(out, ROOT)} ({size:,} bytes, items={len(payload['items'])})")
    print(f"\nSummary: {len(success)} ok / {len(skipped)} skipped / {len(failed)} failed")
    if skipped:
        print(f"  skipped: {skipped}")
    if failed:
        print(f"  failed: {failed}")
    return 0 if not failed else 1


if __name__ == '__main__':
    sys.exit(main())
