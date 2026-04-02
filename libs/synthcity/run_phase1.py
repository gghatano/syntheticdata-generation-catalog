"""SynthCity Phase 1: 単一表合成データ生成"""
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

from synthcity.plugins import Plugins
from synthcity.plugins.core.dataloader import GenericDataLoader

loader = GenericDataLoader(real_data)

available = Plugins().list()
print(f"Available models: {available}")

target_models = ['marginal_distributions', 'bayesian_network', 'ctgan', 'tvae', 'adsgan', 'nflow']
models_to_run = [m for m in target_models if m in available]
print(f"Running: {models_to_run}")

# Model-specific kwargs to limit training time
MODEL_KWARGS = {
    'ctgan': {'n_iter': 20},
    'tvae': {'n_iter': 20},
    'adsgan': {'n_iter': 20},
    'nflow': {'n_iter': 20},
}

results = {}
env = {
    'python_version': platform.python_version(),
    'timestamp': datetime.now().isoformat(),
}
try:
    import synthcity
    env['synthcity_version'] = getattr(synthcity, '__version__', 'unknown')
except:
    pass

update_progress('02-phase1', 'in_progress', current_step='synthcity')

for model_name in models_to_run:
    try:
        start = time.time()
        kwargs = MODEL_KWARGS.get(model_name, {})
        plugin = Plugins().get(model_name, **kwargs)
        plugin.fit(loader)
        synth = plugin.generate(count=len(real_data)).dataframe()
        elapsed = time.time() - start
        synth.to_csv(os.path.join(OUTPUT_DIR, f'synthcity_{model_name}.csv'), index=False)
        results[f'synthcity_{model_name}'] = {'status': 'ok', 'time_sec': round(elapsed, 2), 'rows': len(synth)}
        print(f"{model_name}: OK ({elapsed:.1f}s)")
    except Exception as e:
        results[f'synthcity_{model_name}'] = {'status': 'error', 'error': str(e), 'traceback': traceback.format_exc()}
        print(f"{model_name}: ERROR - {e}")

if not models_to_run:
    results['synthcity'] = {'status': 'error', 'error': f'No target models available. Found: {available}'}

results['_env'] = env
with open(os.path.join(OUTPUT_DIR, 'synthcity_run_log.json'), 'w') as f:
    json.dump(results, f, indent=2)

print("SynthCity Phase1 complete.")
