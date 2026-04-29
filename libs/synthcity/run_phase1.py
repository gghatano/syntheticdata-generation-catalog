"""SynthCity Phase 1: 単一表合成データ生成"""
import pandas as pd
import json
import os
import sys
import platform
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..', '..')
REAL_DATA_PATH = os.path.join(ROOT, 'data/processed/d1_adult.csv')
OUTPUT_DIR = os.path.join(ROOT, 'results/phase1')
META_DIR = os.path.join(ROOT, 'results/metadata')
PROGRESS_FILE = os.path.join(ROOT, 'docs/tasks/progress.json')
RANDOM_SEED = 42

os.makedirs(OUTPUT_DIR, exist_ok=True)

sys.path.insert(0, os.path.join(ROOT, 'libs'))
from common.experiment import ExperimentRun, build_run_log, update_progress, update_manifest

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

env = {
    'python_version': platform.python_version(),
    'timestamp': datetime.now().isoformat(),
}
try:
    import synthcity
    env['synthcity_version'] = getattr(synthcity, '__version__', 'unknown')
except:
    pass

synthcity_version = env.get('synthcity_version', 'unknown')

dataset_info = {
    "name": "d1_adult",
    "path": REAL_DATA_PATH,
    "rows": len(real_data),
    "columns": len(real_data.columns),
}

runs = []

update_progress(PROGRESS_FILE, '02-phase1', 'in_progress', current_step='synthcity')

for model_name in models_to_run:
    kwargs = MODEL_KWARGS.get(model_name, {})
    params = {"random_seed": RANDOM_SEED, "num_rows": len(real_data)}
    params.update(kwargs)

    run = ExperimentRun(
        experiment_id=f"phase1_synthcity_{model_name}",
        phase="phase1", library="synthcity", model=model_name,
        dataset=dataset_info,
        params=params,
    )
    with run:
        plugin = Plugins().get(model_name, **kwargs)
        plugin.fit(loader)
        synth = plugin.generate(count=len(real_data)).dataframe()
        csv_path = os.path.join(OUTPUT_DIR, f'synthcity_{model_name}.csv')
        synth.to_csv(csv_path, index=False)
        run.set_output(csv_path=csv_path, rows=len(synth), columns=len(synth.columns))

    run.save_meta(META_DIR, library_version=synthcity_version)
    runs.append(run)
    if run.status == "ok":
        print(f"{model_name}: OK ({run.elapsed_sec:.1f}s)")
    else:
        print(f"{model_name}: ERROR - {run.error['message']}")

if not models_to_run:
    print(f"No target models available. Found: {available}")

log = build_run_log(runs, env)
if not models_to_run:
    log['synthcity'] = {'status': 'error', 'error': f'No target models available. Found: {available}'}
with open(os.path.join(OUTPUT_DIR, 'synthcity_run_log.json'), 'w') as f:
    json.dump(log, f, indent=2)

update_manifest(META_DIR)
print("SynthCity Phase1 complete.")
