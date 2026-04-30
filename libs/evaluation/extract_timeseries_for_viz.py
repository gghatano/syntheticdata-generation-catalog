"""Issue #70: 事例ページの時系列可視化用 JSON を抽出する。

real (Daily Weather 2020) と synth (PAR 64ep) から、代表 1 拠点 / 1 シーケンスを
選び、temperatureHigh と humidity の時系列を JSON で書き出す。

実行: cd libs/evaluation && uv run python extract_timeseries_for_viz.py

副作用:
  - docs/catalog/public/data/timeseries/iot-sensor-monitoring.json を生成
"""
import hashlib
import json
import os
import sys

import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..', '..')
REAL_CSV = os.path.join(ROOT, 'data/processed/d_weather.csv')
SYNTH_CSV = os.path.join(ROOT, 'results/phase3/weather_par.csv')
OUTPUT_JSON = os.path.join(ROOT, 'docs/catalog/public/data/timeseries/iot-sensor-monitoring.json')

REAL_LOCATION = 'US, New York'  # 温帯気候。気温・湿度の季節変動が分かりやすい
SERIES_COLS = [
    {'name': 'temperatureHigh', 'label': '最高気温 (°F)', 'unit': '°F'},
    {'name': 'humidity', 'label': '湿度', 'unit': ''},
]


def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()[:12]


def main() -> int:
    if not os.path.exists(REAL_CSV) or not os.path.exists(SYNTH_CSV):
        print(f"[ERROR] 入力 CSV が見つかりません。先に eval_iot_weather.py を実行してください:")
        print(f"  REAL : {REAL_CSV} (exists={os.path.exists(REAL_CSV)})")
        print(f"  SYNTH: {SYNTH_CSV} (exists={os.path.exists(SYNTH_CSV)})")
        return 1

    real = pd.read_csv(REAL_CSV)
    synth = pd.read_csv(SYNTH_CSV)

    if REAL_LOCATION not in real['location'].unique():
        print(f"[WARN] 想定 real location '{REAL_LOCATION}' が見つかりません。最初のロケーションで代替します")
        real_loc = real['location'].iloc[0]
    else:
        real_loc = REAL_LOCATION

    real_seq = real[real['location'] == real_loc].sort_values('time').reset_index(drop=True)
    synth_loc = synth['location'].iloc[0]
    synth_seq = synth[synth['location'] == synth_loc].reset_index(drop=True)

    # 長さを合わせる（min を採用）
    n = min(len(real_seq), len(synth_seq))
    real_seq = real_seq.iloc[:n]
    synth_seq = synth_seq.iloc[:n]

    series = []
    for col in SERIES_COLS:
        c = col['name']
        if c not in real_seq.columns or c not in synth_seq.columns:
            print(f"[WARN] 列 {c} が存在しないためスキップ")
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
            'unit': col['unit'],
            'real_mean': round(float(real_seq[c].mean()), 4),
            'synth_mean': round(float(synth_seq[c].mean()), 4),
            'real_std': round(float(real_seq[c].std()), 4),
            'synth_std': round(float(synth_seq[c].std()), 4),
            'points': points,
        })

    output = {
        'case_id': 'iot-sensor-monitoring',
        'selected_real_location': real_loc,
        'selected_synth_sequence': synth_loc,
        'date_range_real': {
            'start': str(real_seq['time'].iloc[0]),
            'end': str(real_seq['time'].iloc[-1]),
        },
        'sequence_length': n,
        'series': series,
        'note': (
            f"real は {real_loc}（{n} 日間）、synth は PAR 64ep が生成した 1 シーケンス。"
            "x 軸は系列内の経過日数（synth の日付は real と整合しないため day_index 表示）。"
        ),
        'source': {
            'real_csv_sha256_prefix': file_sha256(REAL_CSV),
            'synth_csv_sha256_prefix': file_sha256(SYNTH_CSV),
        },
    }

    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
        f.write('\n')

    size = os.path.getsize(OUTPUT_JSON)
    print(f"Wrote {OUTPUT_JSON} ({size:,} bytes, {n} points × {len(series)} series)")
    print(f"  real: {real_loc} ({output['date_range_real']['start']} – {output['date_range_real']['end']})")
    print(f"  synth: {synth_loc}")
    for s in series:
        print(f"  {s['name']}: real_mean={s['real_mean']} synth_mean={s['synth_mean']}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
