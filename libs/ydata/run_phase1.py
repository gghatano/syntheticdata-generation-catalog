"""ydata-synthetic Phase 1: 単一表合成データ生成"""
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

results = {}
env = {
    'python_version': platform.python_version(),
    'timestamp': datetime.now().isoformat(),
}

update_progress('02-phase1', 'in_progress', current_step='ydata')

try:
    from ydata_synthetic.synthesizers.regular import RegularSynthesizer
    from ydata_synthetic.synthesizers import ModelParameters, TrainParameters
    import ydata_synthetic
    env['ydata_version'] = getattr(ydata_synthetic, '__version__', 'unknown')

    cat_cols = real_data.select_dtypes(include=['object', 'category']).columns.tolist()
    num_cols = real_data.select_dtypes(include=['number']).columns.tolist()

    start = time.time()
    model_params = ModelParameters(batch_size=500, lr=2e-4, betas=(0.5, 0.9))
    train_params = TrainParameters(epochs=100)

    synth = RegularSynthesizer(modelname='ctgan', model_parameters=model_params)
    synth.fit(data=real_data, train_arguments=train_params, num_cols=num_cols, cat_cols=cat_cols)
    synth_data = synth.sample(len(real_data))
    elapsed = time.time() - start

    synth_data.to_csv(os.path.join(OUTPUT_DIR, 'ydata_ctgan.csv'), index=False)
    results['ydata_ctgan'] = {'status': 'ok', 'time_sec': round(elapsed, 2), 'rows': len(synth_data)}
    print(f"ydata CTGAN: OK ({elapsed:.1f}s)")
except Exception as e:
    results['ydata_ctgan'] = {'status': 'error', 'error': str(e), 'traceback': traceback.format_exc()}
    print(f"ydata CTGAN: ERROR - {e}")

results['_env'] = env
with open(os.path.join(OUTPUT_DIR, 'ydata_run_log.json'), 'w') as f:
    json.dump(results, f, indent=2)

print("ydata Phase1 complete.")
