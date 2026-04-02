"""SDV Phase 2: 複数表合成データ生成"""
import pandas as pd
import json
import time
import traceback
import os
import sys
import glob
import platform
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..', '..')
OUTPUT_DIR = os.path.join(ROOT, 'results/phase2')
PROGRESS_FILE = os.path.join(ROOT, 'docs/tasks/progress.json')
os.makedirs(OUTPUT_DIR, exist_ok=True)

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

from sdv.multi_table import HMASynthesizer
from sdv.metadata import Metadata
import sdv

metadata_path = os.path.join(ROOT, 'data/raw/d2_metadata.json')
if not os.path.exists(metadata_path):
    print(f"ERROR: {metadata_path} not found. Run prepare_data.py first.")
    sys.exit(1)

metadata_dict = json.load(open(metadata_path))
metadata = Metadata.load_from_dict(metadata_dict)

# 複数テーブルを dict で読み込み
data = {}
for csv_file in sorted(glob.glob(os.path.join(ROOT, 'data/processed/d2_*.csv'))):
    table_name = os.path.basename(csv_file).replace('d2_', '').replace('.csv', '')
    # profile.json は除外
    if 'profile' in table_name:
        continue
    data[table_name] = pd.read_csv(csv_file)
    print(f"Loaded {table_name}: {len(data[table_name])} rows")

results = {}
env = {
    'python_version': platform.python_version(),
    'sdv_version': sdv.__version__,
    'timestamp': datetime.now().isoformat(),
}

update_progress('03-phase2', 'in_progress', current_step='sdv')

try:
    start = time.time()
    synthesizer = HMASynthesizer(metadata)
    synthesizer.fit(data)
    synth_data = synthesizer.sample()
    elapsed = time.time() - start

    for table_name, df in synth_data.items():
        df.to_csv(os.path.join(OUTPUT_DIR, f'sdv_hma_{table_name}.csv'), index=False)

    results['sdv_hma'] = {
        'status': 'ok',
        'time_sec': round(elapsed, 2),
        'tables': {name: len(df) for name, df in synth_data.items()}
    }
    print(f"SDV HMA: OK ({elapsed:.1f}s)")
except Exception as e:
    results['sdv_hma'] = {'status': 'error', 'error': str(e), 'traceback': traceback.format_exc()}
    print(f"SDV HMA: ERROR - {e}")

results['_env'] = env
with open(os.path.join(OUTPUT_DIR, 'sdv_run_log.json'), 'w') as f:
    json.dump(results, f, indent=2)

update_progress('03-phase2', 'completed' if results.get('sdv_hma', {}).get('status') == 'ok' else 'error')
print("SDV Phase2 complete.")
