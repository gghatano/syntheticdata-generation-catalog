"""Issue #70 / #77: 事例ページの時系列可視化用 JSON を生成する。

real と synth から代表 1 シーケンス（拠点・銘柄など）を選び、指定列の時系列を
JSON で書き出す。複数事例を `CASES` で管理する。

実行: cd libs/evaluation && uv run python extract_timeseries_for_viz.py

副作用:
  - docs/catalog/public/data/timeseries/<case_id>.json を生成
"""
import hashlib
import json
import os
import sys
from typing import Optional

import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..', '..')
OUTPUT_DIR = os.path.join(ROOT, 'docs/catalog/public/data/timeseries')


def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()[:12]


def build_payload(
    *,
    case_id: str,
    real_csv: str,
    synth_csv: str,
    seq_key: str,
    time_col: str,
    series_cols: list[dict],
    preferred_real_seq: Optional[str] = None,
    note_template: str,
) -> Optional[dict]:
    if not os.path.exists(real_csv) or not os.path.exists(synth_csv):
        print(f"[SKIP] {case_id}: 入力 CSV が見つかりません ({real_csv} or {synth_csv})")
        return None

    real = pd.read_csv(real_csv)
    synth = pd.read_csv(synth_csv)

    if seq_key not in real.columns or seq_key not in synth.columns:
        print(f"[SKIP] {case_id}: sequence_key '{seq_key}' が CSV に無い")
        return None

    real_seq_id = preferred_real_seq if preferred_real_seq and preferred_real_seq in real[seq_key].unique() else real[seq_key].iloc[0]
    synth_seq_id = synth[seq_key].iloc[0]

    real_seq = real[real[seq_key] == real_seq_id].sort_values(time_col).reset_index(drop=True)
    synth_seq = synth[synth[seq_key] == synth_seq_id].reset_index(drop=True)

    n = min(len(real_seq), len(synth_seq))
    if n == 0:
        print(f"[SKIP] {case_id}: シーケンス長 0")
        return None
    real_seq = real_seq.iloc[:n]
    synth_seq = synth_seq.iloc[:n]

    series = []
    for col in series_cols:
        c = col['name']
        if c not in real_seq.columns or c not in synth_seq.columns:
            print(f"  [WARN] {case_id}: 列 {c} が存在しないためスキップ")
            continue
        points = []
        for i in range(n):
            r_val = real_seq[c].iloc[i]
            s_val = synth_seq[c].iloc[i]
            points.append({
                'x': i,
                'real': None if pd.isna(r_val) else round(float(r_val), 4),
                'synth': None if pd.isna(s_val) else round(float(s_val), 4),
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

    return {
        'case_id': case_id,
        'selected_real_location': str(real_seq_id),
        'selected_synth_sequence': str(synth_seq_id),
        'date_range_real': {
            'start': str(real_seq[time_col].iloc[0]),
            'end': str(real_seq[time_col].iloc[-1]),
        },
        'sequence_length': n,
        'series': series,
        'note': note_template.format(real_seq_id=real_seq_id, n=n),
        'source': {
            'real_csv_sha256_prefix': file_sha256(real_csv),
            'synth_csv_sha256_prefix': file_sha256(synth_csv),
        },
    }


def process_iot() -> Optional[dict]:
    return build_payload(
        case_id='iot-sensor-monitoring',
        real_csv=os.path.join(ROOT, 'data/processed/d_weather.csv'),
        synth_csv=os.path.join(ROOT, 'results/phase3/weather_par.csv'),
        seq_key='location',
        time_col='time',
        series_cols=[
            {'name': 'temperatureHigh', 'label': '最高気温 (°F)', 'unit': '°F'},
            {'name': 'humidity', 'label': '湿度', 'unit': ''},
        ],
        preferred_real_seq='US, New York',
        note_template=(
            "real は {real_seq_id}（{n} 日間）、synth は PAR 64ep が生成した 1 シーケンス。"
            "x 軸は系列内の経過日数（synth の日付は real と整合しないため day_index 表示）。"
        ),
    )


def process_stock() -> Optional[dict]:
    # synth は run_phase3.py の出力 (sdv_par.csv) を想定
    synth_candidates = [
        os.path.join(ROOT, 'results/phase3/sdv_par.csv'),
        os.path.join(ROOT, 'results/phase3/sdv_par_128ep.csv'),
    ]
    synth_csv = next((p for p in synth_candidates if os.path.exists(p)), synth_candidates[0])
    return build_payload(
        case_id='stock-price-timeseries',
        real_csv=os.path.join(ROOT, 'data/processed/d3_nasdaq.csv'),
        synth_csv=synth_csv,
        seq_key='Symbol',
        time_col='Date',
        series_cols=[
            {'name': 'Close', 'label': '終値', 'unit': 'USD'},
            {'name': 'Volume', 'label': '出来高', 'unit': '株'},
        ],
        preferred_real_seq='AAPL',
        note_template=(
            "real は {real_seq_id} の 2019 年日次（{n} 営業日）、synth は PAR 128ep が生成した 1 シーケンス。"
            "x 軸は系列内の経過営業日（synth の日付は real と整合しないため index 表示）。"
        ),
    )


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
            print(f"[ERROR] {case_id}: {e}")
            failed += 1
            continue
        if payload is None:
            skipped += 1
            continue
        out = os.path.join(OUTPUT_DIR, f'{case_id}.json')
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
            f.write('\n')
        size = os.path.getsize(out)
        print(f"[OK] {case_id} -> {os.path.relpath(out, ROOT)} ({size:,} bytes, "
              f"{payload['sequence_length']} pts × {len(payload['series'])} series)")
        for s in payload['series']:
            print(f"  {s['name']}: real_mean={s['real_mean']} synth_mean={s['synth_mean']}")
        success += 1
    print(f"\nSummary: {success} ok / {skipped} skipped / {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
