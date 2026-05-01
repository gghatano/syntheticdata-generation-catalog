"""Issue #70 / #77 / fix: 事例ページの時系列可視化用 JSON を生成する。

real / synth から複数のペアを構築し、各ペアの時系列と全体の分布ヒストグラムを
JSON にまとめて出力する。

設計上のポイント:
  - PAR は real の特定シーケンス（銘柄など）と対応する synth を生成しないため、
    各ペアの synth は「real シーケンスの mean に最も近い synth シーケンス」を
    最寄りマッチングで選択する。
  - 株価のように real が 100+ シーケンスあり PAR が 10 程度しか生成しない場合、
    1 対 1 比較は誤解を招くので aggregate 分布も並列出力する。

実行: cd libs/evaluation && uv run python extract_timeseries_for_viz.py

副作用:
  - docs/catalog/public/data/timeseries/<case_id>.json を生成
"""
import hashlib
import json
import os
import sys
from typing import Optional

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..', '..')
OUTPUT_DIR = os.path.join(ROOT, 'docs/catalog/public/data/timeseries')

AGG_BINS = 30


def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()[:12]


def build_series(
    real_seq: pd.DataFrame,
    synth_seq: pd.DataFrame,
    series_cols: list[dict],
) -> list[dict]:
    n = min(len(real_seq), len(synth_seq))
    real_seq = real_seq.iloc[:n].reset_index(drop=True)
    synth_seq = synth_seq.iloc[:n].reset_index(drop=True)
    series = []
    for col in series_cols:
        c = col['name']
        if c not in real_seq.columns or c not in synth_seq.columns:
            continue
        points = []
        for i in range(n):
            r = real_seq[c].iloc[i]
            s = synth_seq[c].iloc[i]
            points.append({
                'x': i,
                'real': None if pd.isna(r) else round(float(r), 4),
                'synth': None if pd.isna(s) else round(float(s), 4),
            })
        series.append({
            'name': c,
            'label': col['label'],
            'unit': col.get('unit', ''),
            'real_mean': round(float(real_seq[c].mean()), 4),
            'synth_mean': round(float(synth_seq[c].mean()), 4),
            'real_std': round(float(real_seq[c].std()), 4),
            'synth_std': round(float(synth_seq[c].std()), 4),
            'points': points,
        })
    return series


def find_closest_synth(
    synth: pd.DataFrame,
    seq_key: str,
    target_mean: float,
    matching_col: str,
    exclude: set[str],
) -> Optional[str]:
    """matching_col の平均が target_mean に最も近い synth の seq id を返す。"""
    means = synth.groupby(seq_key)[matching_col].mean()
    if exclude:
        means = means[~means.index.isin(exclude)]
    if means.empty:
        return None
    diffs = (means - target_mean).abs().sort_values()
    return str(diffs.index[0])


def build_aggregate(
    real: pd.DataFrame,
    synth: pd.DataFrame,
    series_cols: list[dict],
) -> list[dict]:
    out = []
    for col in series_cols:
        c = col['name']
        if c not in real.columns or c not in synth.columns:
            continue
        rv = real[c].dropna().astype(float).values
        sv = synth[c].dropna().astype(float).values
        if len(rv) == 0 or len(sv) == 0:
            continue
        # 値域は real のレンジに揃える（外れ値は real のクリップで synth を抑える）
        lo = float(np.min(rv))
        hi = float(np.max(rv))
        if lo == hi:
            continue
        edges = np.linspace(lo, hi, AGG_BINS + 1)
        # synth の外れ値は端 bin に含める（一般的な histogram 挙動）
        sv_clipped = np.clip(sv, lo, hi)
        rc, _ = np.histogram(rv, bins=edges)
        sc, _ = np.histogram(sv_clipped, bins=edges)
        out.append({
            'name': c,
            'label': col['label'],
            'unit': col.get('unit', ''),
            'real_count': int(len(rv)),
            'synth_count': int(len(sv)),
            'real_mean': round(float(np.mean(rv)), 4),
            'synth_mean': round(float(np.mean(sv)), 4),
            'real_std': round(float(np.std(rv)), 4),
            'synth_std': round(float(np.std(sv)), 4),
            'bins': [
                {
                    'x': round(float(edges[i]), 4),
                    'x_end': round(float(edges[i + 1]), 4),
                    'real': int(rc[i]),
                    'synth': int(sc[i]),
                }
                for i in range(AGG_BINS)
            ],
        })
    return out


def process_iot() -> Optional[dict]:
    real_csv = os.path.join(ROOT, 'data/processed/d_weather.csv')
    synth_csv = os.path.join(ROOT, 'results/phase3/weather_par.csv')
    if not (os.path.exists(real_csv) and os.path.exists(synth_csv)):
        return None
    real = pd.read_csv(real_csv)
    synth = pd.read_csv(synth_csv)

    seq_key = 'location'
    time_col = 'time'
    series_cols = [
        {'name': 'temperatureHigh', 'label': '最高気温 (°F)', 'unit': '°F'},
        {'name': 'humidity', 'label': '湿度', 'unit': ''},
    ]
    matching_col = 'temperatureHigh'

    target_real_id = 'US, New York' if 'US, New York' in real[seq_key].unique() else real[seq_key].iloc[0]
    target_real = real[real[seq_key] == target_real_id].sort_values(time_col).reset_index(drop=True)
    target_mean = float(target_real[matching_col].mean())

    synth_id = find_closest_synth(synth, seq_key, target_mean, matching_col, exclude=set())
    if synth_id is None:
        return None
    synth_seq = synth[synth[seq_key] == synth_id].reset_index(drop=True)

    series = build_series(target_real, synth_seq, series_cols)
    n = min(len(target_real), len(synth_seq))

    pair = {
        'label': f'{target_real_id}',
        'real_id': str(target_real_id),
        'synth_id': str(synth_id),
        'match_reason': f'real {matching_col} 平均 {target_mean:.2f} に最も近い synth として {synth_id} を選択',
        'date_range_real': {
            'start': str(target_real[time_col].iloc[0]),
            'end': str(target_real[time_col].iloc[-1]),
        },
        'sequence_length': n,
        'series': series,
    }

    aggregate = build_aggregate(real, synth, series_cols)

    return {
        'case_id': 'iot-sensor-monitoring',
        'pairs': [pair],
        'aggregate': {
            'note': '122 観測拠点 × 112 日と 10 synth シーケンス × 112 日の値の分布を、real のレンジで bin 分割して比較。',
            'series': aggregate,
        },
        'note': (
            'real は 122 観測拠点から 1 つを選択、synth は PAR 64ep が生成した 1 シーケンス（real の最高気温平均と最も近いものを採用）。'
            'x 軸は系列内の経過日数（synth の日付は real と整合しないため day_index 表示）。'
        ),
        'source': {
            'real_csv_sha256_prefix': file_sha256(real_csv),
            'synth_csv_sha256_prefix': file_sha256(synth_csv),
        },
    }


def process_stock() -> Optional[dict]:
    real_csv = os.path.join(ROOT, 'data/processed/d3_nasdaq.csv')
    synth_candidates = [
        os.path.join(ROOT, 'results/phase3/sdv_par.csv'),
        os.path.join(ROOT, 'results/phase3/sdv_par_128ep.csv'),
    ]
    synth_csv = next((p for p in synth_candidates if os.path.exists(p)), synth_candidates[0])
    if not (os.path.exists(real_csv) and os.path.exists(synth_csv)):
        return None
    real = pd.read_csv(real_csv)
    synth = pd.read_csv(synth_csv)

    seq_key = 'Symbol'
    time_col = 'Date'
    series_cols = [
        {'name': 'Close', 'label': '終値', 'unit': 'USD'},
        {'name': 'Volume', 'label': '出来高', 'unit': '株'},
    ]
    matching_col = 'Close'

    # real の銘柄を mean Close で並べ、小型 / 中型 / 大型を選定
    real_means = real.groupby(seq_key)[matching_col].mean()
    sorted_real = real_means.sort_values()
    if len(sorted_real) < 3:
        return None

    # 選定: 25th percentile / median / 90th percentile に最も近い銘柄
    quantile_targets = [0.10, 0.50, 0.90]
    quantile_labels = ['小型株', '中型株', '大型株']
    chosen_real_ids: list[tuple[str, str]] = []  # (label, symbol)
    used = set()
    for q, lbl in zip(quantile_targets, quantile_labels):
        target_v = sorted_real.quantile(q)
        diffs = (sorted_real - target_v).abs()
        # 重複回避
        for sym, _ in diffs.sort_values().items():
            if sym not in used:
                chosen_real_ids.append((lbl, str(sym)))
                used.add(sym)
                break

    pairs = []
    used_synth: set[str] = set()
    for lbl, real_id in chosen_real_ids:
        target_real = real[real[seq_key] == real_id].sort_values(time_col).reset_index(drop=True)
        target_mean = float(target_real[matching_col].mean())
        synth_id = find_closest_synth(synth, seq_key, target_mean, matching_col, exclude=used_synth)
        if synth_id is None:
            continue
        used_synth.add(synth_id)
        synth_seq = synth[synth[seq_key] == synth_id].reset_index(drop=True)

        series = build_series(target_real, synth_seq, series_cols)
        n = min(len(target_real), len(synth_seq))
        synth_mean = float(synth_seq[matching_col].mean())

        pairs.append({
            'label': f'{lbl} ({real_id})',
            'real_id': real_id,
            'synth_id': synth_id,
            'match_reason': (
                f'real {real_id} の {matching_col} 平均 ${target_mean:.2f} に最も近い '
                f'synth として {synth_id} (平均 ${synth_mean:.2f}) を選択'
            ),
            'date_range_real': {
                'start': str(target_real[time_col].iloc[0]),
                'end': str(target_real[time_col].iloc[-1]),
            },
            'sequence_length': n,
            'series': series,
        })

    if not pairs:
        return None

    aggregate = build_aggregate(real, synth, series_cols)

    return {
        'case_id': 'stock-price-timeseries',
        'pairs': pairs,
        'aggregate': {
            'note': (
                f'real {real[seq_key].nunique()} 銘柄 × {len(real)//real[seq_key].nunique() if real[seq_key].nunique() else 0} 営業日と、'
                f'synth {synth[seq_key].nunique()} シーケンス × {len(synth)//max(synth[seq_key].nunique(),1)} 営業日の値分布を比較。'
                'PAR が銘柄ごとのスケール感を学習しきれていない場合、real の幅広い分布に対し synth が中央寄りに収束する傾向が読み取れる。'
            ),
            'series': aggregate,
        },
        'note': (
            'PAR は real の銘柄に対応する synth を生成しないため、ここでは各 real 銘柄に対し '
            f'mean {matching_col} が最も近い synth シーケンスをマッチングしている（{len(pairs)} ペア）。'
            f'real 全 {real[seq_key].nunique()} 銘柄 vs synth 全 {synth[seq_key].nunique()} シーケンスの aggregate 分布も併記。'
        ),
        'source': {
            'real_csv_sha256_prefix': file_sha256(real_csv),
            'synth_csv_sha256_prefix': file_sha256(synth_csv),
        },
    }


CASES = [
    ('iot-sensor-monitoring', process_iot),
    ('stock-price-timeseries', process_stock),
]


def main() -> int:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    success = 0
    skipped = 0
    failed = 0
    for case_id, fn in CASES:
        try:
            payload = fn()
        except Exception as e:
            print(f'[ERROR] {case_id}: {e}')
            import traceback
            traceback.print_exc()
            failed += 1
            continue
        if payload is None:
            print(f'[SKIP] {case_id}')
            skipped += 1
            continue
        out = os.path.join(OUTPUT_DIR, f'{case_id}.json')
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
            f.write('\n')
        size = os.path.getsize(out)
        n_pairs = len(payload['pairs'])
        n_agg = len(payload.get('aggregate', {}).get('series', []))
        print(f'[OK] {case_id} -> {os.path.relpath(out, ROOT)} ({size:,} bytes, {n_pairs} pairs, {n_agg} aggregate series)')
        for p in payload['pairs']:
            print(f'  pair: {p["label"]} (real={p["real_id"]}, synth={p["synth_id"]})')
            for s in p['series']:
                print(f'    {s["name"]}: real_mean={s["real_mean"]} synth_mean={s["synth_mean"]}')
        success += 1
    print(f'\nSummary: {success} ok / {skipped} skipped / {failed} failed')
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
