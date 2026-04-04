"""SDV Phase 3: 時系列合成データ生成"""
import pandas as pd
import json
import os
import sys
import platform
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..', '..')
REAL_DATA_PATH = os.path.join(ROOT, 'data/processed/d3_nasdaq.csv')
METADATA_PATH = os.path.join(ROOT, 'data/raw/d3_nasdaq_metadata.json')
OUTPUT_DIR = os.path.join(ROOT, 'results/phase3')
META_DIR = os.path.join(ROOT, 'results/metadata')
PROGRESS_FILE = os.path.join(ROOT, 'docs/tasks/progress.json')
os.makedirs(OUTPUT_DIR, exist_ok=True)

sys.path.insert(0, os.path.join(ROOT, 'libs'))
from common.experiment import ExperimentRun, build_run_log, update_progress, update_manifest

if not os.path.exists(REAL_DATA_PATH):
    print(f"ERROR: {REAL_DATA_PATH} not found. Run prepare_data.py first.")
    sys.exit(1)

real_data = pd.read_csv(REAL_DATA_PATH)

from sdv.sequential import PARSynthesizer
from sdv.metadata import Metadata
import sdv

metadata = Metadata.load_from_dict(json.load(open(METADATA_PATH)))

env = {
    'python_version': platform.python_version(),
    'sdv_version': sdv.__version__,
    'timestamp': datetime.now().isoformat(),
}

dataset_info = {
    "name": "d3_nasdaq",
    "path": REAL_DATA_PATH,
    "rows": len(real_data),
    "columns": len(real_data.columns),
}

runs = []

update_progress(PROGRESS_FILE, '04-phase3', 'in_progress', current_step='sdv')

# sequence_key を取得
seq_key = None
meta_dict = metadata.to_dict()
if 'columns' in meta_dict:
    for col_name, col_info in meta_dict['columns'].items():
        if col_info.get('sdtype') == 'id':
            seq_key = col_name
            break

num_seq = real_data[seq_key].nunique() if seq_key else 10

run_par = ExperimentRun(
    experiment_id="phase3_sdv_par",
    phase="phase3", library="sdv", model="par",
    dataset=dataset_info,
    params={"random_seed": 42, "epochs": 128, "num_sequences": int(num_seq)},
)
with run_par:
    synthesizer = PARSynthesizer(metadata, epochs=128)
    synthesizer.fit(real_data)
    synth_data = synthesizer.sample(num_sequences=num_seq)
    csv_path = os.path.join(OUTPUT_DIR, 'sdv_par.csv')
    synth_data.to_csv(csv_path, index=False)
    run_par.set_output(csv_path=csv_path, rows=len(synth_data),
                       columns=len(synth_data.columns), sequences=int(num_seq))

run_par.save_meta(META_DIR, library_version=sdv.__version__)
runs.append(run_par)
if run_par.status == "ok":
    print(f"SDV PAR: OK ({run_par.elapsed_sec:.1f}s, {run_par.output['rows']} rows)")
else:
    print(f"SDV PAR: ERROR - {run_par.error['message']}")

log = build_run_log(runs, env)
with open(os.path.join(OUTPUT_DIR, 'sdv_run_log.json'), 'w') as f:
    json.dump(log, f, indent=2)

update_manifest(META_DIR)
print("SDV Phase3 complete.")
