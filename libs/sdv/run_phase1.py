"""SDV Phase 1: 単一表合成データ生成"""
import pandas as pd
import json
import os
import sys
import platform
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..', '..')
REAL_DATA_PATH = os.path.join(ROOT, 'data/processed/d1_adult.csv')
METADATA_PATH = os.path.join(ROOT, 'data/raw/d1_adult_metadata.json')
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

from sdv.single_table import GaussianCopulaSynthesizer, CTGANSynthesizer
from sdv.metadata import Metadata
import sdv

metadata = Metadata.load_from_dict(json.load(open(METADATA_PATH)))

env = {
    'python_version': platform.python_version(),
    'sdv_version': sdv.__version__,
    'timestamp': datetime.now().isoformat(),
}

dataset_info = {
    "name": "d1_adult",
    "path": REAL_DATA_PATH,
    "rows": len(real_data),
    "columns": len(real_data.columns),
}

runs = []

update_progress(PROGRESS_FILE, '02-phase1', 'in_progress', current_step='sdv')

# --- GaussianCopula ---
run_gc = ExperimentRun(
    experiment_id="phase1_sdv_gaussiancopula",
    phase="phase1", library="sdv", model="gaussiancopula",
    dataset=dataset_info,
    params={"random_seed": RANDOM_SEED, "num_rows": len(real_data)},
)
with run_gc:
    gc = GaussianCopulaSynthesizer(metadata)
    gc.fit(real_data)
    synth_gc = gc.sample(num_rows=len(real_data))
    csv_path = os.path.join(OUTPUT_DIR, 'sdv_gaussiancopula.csv')
    synth_gc.to_csv(csv_path, index=False)
    run_gc.set_output(csv_path=csv_path, rows=len(synth_gc), columns=len(synth_gc.columns))
run_gc.save_meta(META_DIR, library_version=sdv.__version__)
runs.append(run_gc)
if run_gc.status == "ok":
    print(f"GaussianCopula: OK ({run_gc.elapsed_sec:.1f}s, {run_gc.output['rows']} rows)")
else:
    print(f"GaussianCopula: ERROR - {run_gc.error['message']}")

# --- CTGAN ---
run_ctgan = ExperimentRun(
    experiment_id="phase1_sdv_ctgan",
    phase="phase1", library="sdv", model="ctgan",
    dataset=dataset_info,
    params={"random_seed": RANDOM_SEED, "num_rows": len(real_data), "epochs": 100},
)
with run_ctgan:
    ctgan = CTGANSynthesizer(metadata, epochs=100)
    ctgan.fit(real_data)
    synth_ctgan = ctgan.sample(num_rows=len(real_data))
    csv_path = os.path.join(OUTPUT_DIR, 'sdv_ctgan.csv')
    synth_ctgan.to_csv(csv_path, index=False)
    run_ctgan.set_output(csv_path=csv_path, rows=len(synth_ctgan), columns=len(synth_ctgan.columns))
run_ctgan.save_meta(META_DIR, library_version=sdv.__version__)
runs.append(run_ctgan)
if run_ctgan.status == "ok":
    print(f"CTGAN: OK ({run_ctgan.elapsed_sec:.1f}s, {run_ctgan.output['rows']} rows)")
else:
    print(f"CTGAN: ERROR - {run_ctgan.error['message']}")

# 既存形式の run_log も出力（後方互換）
log = build_run_log(runs, env)
with open(os.path.join(OUTPUT_DIR, 'sdv_run_log.json'), 'w') as f:
    json.dump(log, f, indent=2)

update_manifest(META_DIR)
print("SDV Phase1 complete.")
