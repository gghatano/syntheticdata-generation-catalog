"""SDV HMASynthesizer による Olist 合成データ生成。

実行: cd libs/sdv && uv run python run_olist_hma.py
"""
import json
import os
import platform
import time
import traceback
from datetime import datetime

import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..', '..')
PROC_DIR = os.path.join(ROOT, 'data', 'processed', 'olist')
OUTPUT_DIR = os.path.join(ROOT, 'results', 'phase2_olist')
PROGRESS_FILE = os.path.join(ROOT, 'docs', 'tasks', 'progress.json')
os.makedirs(OUTPUT_DIR, exist_ok=True)

RANDOM_SEED = 42


def update_progress(task_id, status, **kwargs):
    progress = {}
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            progress = json.load(f)
    if 'tasks' not in progress:
        progress['tasks'] = {}
    entry = {'status': status, 'updated_at': datetime.now().isoformat()}
    entry.update(kwargs)
    progress['tasks'][task_id] = entry
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)


from sdv.metadata import Metadata
from sdv.multi_table import HMASynthesizer
import sdv

update_progress('issue-65-sdv-hma', 'in_progress')

metadata_dict = json.load(open(os.path.join(PROC_DIR, 'metadata.json')))
metadata = Metadata.load_from_dict(metadata_dict)

data = {}
for tname in metadata_dict['tables'].keys():
    csv_path = os.path.join(PROC_DIR, f'{tname}.csv')
    df = pd.read_csv(csv_path)
    # datetime 列を再パース（CSV では文字列になる）
    for col, col_def in metadata_dict['tables'][tname]['columns'].items():
        if col_def['sdtype'] == 'datetime' and col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    data[tname] = df
    print(f"loaded {tname}: {len(df)} rows")

env = {
    'python_version': platform.python_version(),
    'sdv_version': sdv.__version__,
    'timestamp': datetime.now().isoformat(),
}

results = {}
try:
    print("\n=== HMASynthesizer 学習 ===")
    fit_start = time.time()
    synthesizer = HMASynthesizer(metadata)
    synthesizer.fit(data)
    fit_elapsed = time.time() - fit_start
    print(f"  学習時間: {fit_elapsed:.2f}s")

    print("\n=== サンプリング ===")
    sample_start = time.time()
    synth_data = synthesizer.sample()
    sample_elapsed = time.time() - sample_start
    print(f"  生成時間: {sample_elapsed:.2f}s")

    for tname, df in synth_data.items():
        out = os.path.join(OUTPUT_DIR, f'sdv_hma_{tname}.csv')
        df.to_csv(out, index=False)
        print(f"  saved {out}: {len(df)} rows")

    results['sdv_hma'] = {
        'status': 'ok',
        'fit_time_sec': round(fit_elapsed, 2),
        'sample_time_sec': round(sample_elapsed, 2),
        'time_sec': round(fit_elapsed + sample_elapsed, 2),
        'tables': {name: len(df) for name, df in synth_data.items()},
        'dataset': 'olist',
        'model': 'HMASynthesizer',
    }
except Exception as e:
    results['sdv_hma'] = {
        'status': 'error',
        'error': str(e),
        'traceback': traceback.format_exc(),
        'dataset': 'olist',
    }
    print(f"ERROR: {e}")
    traceback.print_exc()

results['_env'] = env
with open(os.path.join(OUTPUT_DIR, 'sdv_run_log.json'), 'w') as f:
    json.dump(results, f, indent=2)

update_progress(
    'issue-65-sdv-hma',
    'completed' if results.get('sdv_hma', {}).get('status') == 'ok' else 'error',
)
print("\nSDV HMA Olist 完了。")
