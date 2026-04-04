"""SDV Phase 2: 複数表合成データ生成"""
import pandas as pd
import json
import os
import sys
import glob
import platform
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..', '..')
OUTPUT_DIR = os.path.join(ROOT, 'results/phase2')
META_DIR = os.path.join(ROOT, 'results/metadata')
PROGRESS_FILE = os.path.join(ROOT, 'docs/tasks/progress.json')
os.makedirs(OUTPUT_DIR, exist_ok=True)

sys.path.insert(0, os.path.join(ROOT, 'libs'))
from common.experiment import ExperimentRun, build_run_log, update_progress, update_manifest

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
    if 'profile' in table_name:
        continue
    data[table_name] = pd.read_csv(csv_file)
    print(f"Loaded {table_name}: {len(data[table_name])} rows")

# データセット情報（複数テーブルの合計）
total_rows = sum(len(df) for df in data.values())
dataset_info = {
    "name": "d2_hotel_reservations",
    "path": "data/processed/d2_*.csv",
    "rows": total_rows,
    "columns": sum(len(df.columns) for df in data.values()),
}

env = {
    'python_version': platform.python_version(),
    'sdv_version': sdv.__version__,
    'timestamp': datetime.now().isoformat(),
}

runs = []

update_progress(PROGRESS_FILE, '03-phase2', 'in_progress', current_step='sdv')

run_hma = ExperimentRun(
    experiment_id="phase2_sdv_hma",
    phase="phase2", library="sdv", model="hma",
    dataset=dataset_info,
    params={"random_seed": 42},
)
with run_hma:
    synthesizer = HMASynthesizer(metadata)
    synthesizer.fit(data)
    synth_data = synthesizer.sample()

    table_csv_paths = {}
    for table_name, df in synth_data.items():
        csv_path = os.path.join(OUTPUT_DIR, f'sdv_hma_{table_name}.csv')
        df.to_csv(csv_path, index=False)
        table_csv_paths[table_name] = csv_path

    run_hma.set_multi_table_output(table_csv_paths, synth_data)

run_hma.save_meta(META_DIR, library_version=sdv.__version__)
runs.append(run_hma)
if run_hma.status == "ok":
    print(f"SDV HMA: OK ({run_hma.elapsed_sec:.1f}s)")
else:
    print(f"SDV HMA: ERROR - {run_hma.error['message']}")

log = build_run_log(runs, env)
with open(os.path.join(OUTPUT_DIR, 'sdv_run_log.json'), 'w') as f:
    json.dump(log, f, indent=2)

update_progress(PROGRESS_FILE, '03-phase2', 'completed' if run_hma.status == 'ok' else 'error')
update_manifest(META_DIR)
print("SDV Phase2 complete.")
