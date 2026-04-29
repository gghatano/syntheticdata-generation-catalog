"""ydata-synthetic Phase 1: 単一表合成データ生成"""
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

env = {
    'python_version': platform.python_version(),
    'timestamp': datetime.now().isoformat(),
}

dataset_info = {
    "name": "d1_adult",
    "path": REAL_DATA_PATH,
    "rows": len(real_data),
    "columns": len(real_data.columns),
}

runs = []

update_progress(PROGRESS_FILE, '02-phase1', 'in_progress', current_step='ydata')

run_ydata = ExperimentRun(
    experiment_id="phase1_ydata_ctgan",
    phase="phase1", library="ydata", model="ctgan",
    dataset=dataset_info,
    params={"random_seed": RANDOM_SEED, "num_rows": len(real_data),
            "epochs": 100, "batch_size": 500, "lr": 2e-4, "betas": [0.5, 0.9]},
)
with run_ydata:
    from ydata_synthetic.synthesizers.regular import RegularSynthesizer
    from ydata_synthetic.synthesizers import ModelParameters, TrainParameters
    import ydata_synthetic
    env['ydata_version'] = getattr(ydata_synthetic, '__version__', 'unknown')

    cat_cols = real_data.select_dtypes(include=['object', 'category']).columns.tolist()
    num_cols = real_data.select_dtypes(include=['number']).columns.tolist()

    model_params = ModelParameters(batch_size=500, lr=2e-4, betas=(0.5, 0.9))
    train_params = TrainParameters(epochs=100)

    synth = RegularSynthesizer(modelname='ctgan', model_parameters=model_params)
    synth.fit(data=real_data, train_arguments=train_params, num_cols=num_cols, cat_cols=cat_cols)
    synth_data = synth.sample(len(real_data))
    csv_path = os.path.join(OUTPUT_DIR, 'ydata_ctgan.csv')
    synth_data.to_csv(csv_path, index=False)
    run_ydata.set_output(csv_path=csv_path, rows=len(synth_data), columns=len(synth_data.columns))

ydata_version = env.get('ydata_version', 'unknown')
run_ydata.save_meta(META_DIR, library_version=ydata_version)
runs.append(run_ydata)
if run_ydata.status == "ok":
    print(f"ydata CTGAN: OK ({run_ydata.elapsed_sec:.1f}s)")
else:
    print(f"ydata CTGAN: ERROR - {run_ydata.error['message']}")

log = build_run_log(runs, env)
with open(os.path.join(OUTPUT_DIR, 'ydata_run_log.json'), 'w') as f:
    json.dump(log, f, indent=2)

update_manifest(META_DIR)
print("ydata Phase1 complete.")
