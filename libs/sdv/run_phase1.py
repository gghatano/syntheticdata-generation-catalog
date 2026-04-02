"""SDV Phase 1: 単一表合成データ生成"""
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
REAL_DATA_PATH = os.path.join(ROOT, 'data/processed/d1_adult.csv')
METADATA_PATH = os.path.join(ROOT, 'data/raw/d1_adult_metadata.json')
OUTPUT_DIR = os.path.join(ROOT, 'results/phase1')
PROGRESS_FILE = os.path.join(ROOT, 'docs/tasks/progress.json')
RANDOM_SEED = 42

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
print(f"Loaded real data: {len(real_data)} rows, {len(real_data.columns)} columns")

from sdv.single_table import GaussianCopulaSynthesizer, CTGANSynthesizer
from sdv.metadata import Metadata
import sdv

metadata = Metadata.load_from_dict(json.load(open(METADATA_PATH)))

results = {}
env = {
    'python_version': platform.python_version(),
    'sdv_version': sdv.__version__,
    'timestamp': datetime.now().isoformat(),
}

update_progress('02-phase1', 'in_progress', current_step='sdv')

# --- GaussianCopula ---
try:
    start = time.time()
    gc = GaussianCopulaSynthesizer(metadata)
    gc.fit(real_data)
    synth_gc = gc.sample(num_rows=len(real_data))
    elapsed = time.time() - start
    synth_gc.to_csv(os.path.join(OUTPUT_DIR, 'sdv_gaussiancopula.csv'), index=False)
    results['sdv_gaussiancopula'] = {'status': 'ok', 'time_sec': round(elapsed, 2), 'rows': len(synth_gc)}
    print(f"GaussianCopula: OK ({elapsed:.1f}s, {len(synth_gc)} rows)")
except Exception as e:
    results['sdv_gaussiancopula'] = {'status': 'error', 'error': str(e), 'traceback': traceback.format_exc()}
    print(f"GaussianCopula: ERROR - {e}")

# --- CTGAN ---
try:
    start = time.time()
    ctgan = CTGANSynthesizer(metadata, epochs=100)
    ctgan.fit(real_data)
    synth_ctgan = ctgan.sample(num_rows=len(real_data))
    elapsed = time.time() - start
    synth_ctgan.to_csv(os.path.join(OUTPUT_DIR, 'sdv_ctgan.csv'), index=False)
    results['sdv_ctgan'] = {'status': 'ok', 'time_sec': round(elapsed, 2), 'rows': len(synth_ctgan)}
    print(f"CTGAN: OK ({elapsed:.1f}s, {len(synth_ctgan)} rows)")
except Exception as e:
    results['sdv_ctgan'] = {'status': 'error', 'error': str(e), 'traceback': traceback.format_exc()}
    print(f"CTGAN: ERROR - {e}")

results['_env'] = env
with open(os.path.join(OUTPUT_DIR, 'sdv_run_log.json'), 'w') as f:
    json.dump(results, f, indent=2)

print("SDV Phase1 complete.")
