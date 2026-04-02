"""SDV Phase 3: 時系列合成データ生成"""
import pandas as pd
import json
import time
import traceback
import os
import sys
import platform
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..', '..')
REAL_DATA_PATH = os.path.join(ROOT, 'data/processed/d3_nasdaq.csv')
METADATA_PATH = os.path.join(ROOT, 'data/raw/d3_nasdaq_metadata.json')
OUTPUT_DIR = os.path.join(ROOT, 'results/phase3')
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

if not os.path.exists(REAL_DATA_PATH):
    print(f"ERROR: {REAL_DATA_PATH} not found. Run prepare_data.py first.")
    sys.exit(1)

real_data = pd.read_csv(REAL_DATA_PATH)

from sdv.sequential import PARSynthesizer
from sdv.metadata import Metadata
import sdv

metadata = Metadata.load_from_dict(json.load(open(METADATA_PATH)))

results = {}
env = {
    'python_version': platform.python_version(),
    'sdv_version': sdv.__version__,
    'timestamp': datetime.now().isoformat(),
}

update_progress('04-phase3', 'in_progress', current_step='sdv')

try:
    start = time.time()
    synthesizer = PARSynthesizer(metadata, epochs=128)
    synthesizer.fit(real_data)

    # sequence_key を取得
    seq_key = None
    meta_dict = metadata.to_dict()
    if 'columns' in meta_dict:
        for col_name, col_info in meta_dict['columns'].items():
            if col_info.get('sdtype') == 'id':
                seq_key = col_name
                break

    num_seq = real_data[seq_key].nunique() if seq_key else 10
    synth_data = synthesizer.sample(num_sequences=num_seq)
    elapsed = time.time() - start

    synth_data.to_csv(os.path.join(OUTPUT_DIR, 'sdv_par.csv'), index=False)
    results['sdv_par'] = {
        'status': 'ok',
        'time_sec': round(elapsed, 2),
        'rows': len(synth_data),
        'sequences': int(num_seq),
    }
    print(f"SDV PAR: OK ({elapsed:.1f}s, {len(synth_data)} rows)")
except Exception as e:
    results['sdv_par'] = {'status': 'error', 'error': str(e), 'traceback': traceback.format_exc()}
    print(f"SDV PAR: ERROR - {e}")

results['_env'] = env
with open(os.path.join(OUTPUT_DIR, 'sdv_run_log.json'), 'w') as f:
    json.dump(results, f, indent=2)

print("SDV Phase3 complete.")
