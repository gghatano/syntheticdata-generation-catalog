"""追加実験: IMDB (multi-table), Insurance (single-table)

実行: cd libs/sdv && uv run --no-project python run_additional_experiments.py
"""
import pandas as pd
import json
import os
import sys
import platform
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..', '..')
os.makedirs(os.path.join(ROOT, 'results/phase1'), exist_ok=True)
os.makedirs(os.path.join(ROOT, 'results/phase2'), exist_ok=True)
META_DIR = os.path.join(ROOT, 'results/metadata')

sys.path.insert(0, os.path.join(ROOT, 'libs'))
from common.experiment import ExperimentRun, build_run_log, update_manifest

from sdv.datasets.demo import download_demo
from sdv.single_table import GaussianCopulaSynthesizer, CTGANSynthesizer
from sdv.multi_table import HMASynthesizer
from sdv.metadata import Metadata
import sdv

env = {
    'python_version': platform.python_version(),
    'sdv_version': sdv.__version__,
    'timestamp': datetime.now().isoformat(),
}

runs = []

# === 1. Insurance (single_table) ===
print("=== Insurance (single_table) ===")
try:
    ins_data, ins_meta = download_demo(modality='single_table', dataset_name='insurance')
    ins_data.to_csv(os.path.join(ROOT, 'data/raw/d_insurance.csv'), index=False)
    with open(os.path.join(ROOT, 'data/raw/d_insurance_metadata.json'), 'w') as f:
        json.dump(ins_meta.to_dict(), f, indent=2)
    print(f"  Downloaded: {len(ins_data)} rows, {len(ins_data.columns)} cols")

    ins_dataset = {
        "name": "d_insurance",
        "path": os.path.join(ROOT, 'data/raw/d_insurance.csv'),
        "rows": len(ins_data),
        "columns": len(ins_data.columns),
    }

    # GaussianCopula
    run_ins_gc = ExperimentRun(
        experiment_id="phase1_sdv_gaussiancopula_insurance",
        phase="phase1", library="sdv", model="gaussiancopula",
        dataset=ins_dataset,
        params={"random_seed": 42, "num_rows": len(ins_data)},
    )
    with run_ins_gc:
        gc = GaussianCopulaSynthesizer(ins_meta)
        gc.fit(ins_data)
        synth = gc.sample(num_rows=len(ins_data))
        csv_path = os.path.join(ROOT, 'results/phase1/sdv_gaussiancopula_insurance.csv')
        synth.to_csv(csv_path, index=False)
        run_ins_gc.set_output(csv_path=csv_path, rows=len(synth), columns=len(synth.columns))
    run_ins_gc.save_meta(META_DIR, library_version=sdv.__version__)
    runs.append(run_ins_gc)
    print(f"  GaussianCopula: {'OK' if run_ins_gc.status == 'ok' else 'ERROR'} ({run_ins_gc.elapsed_sec:.1f}s)")

    # CTGAN 50ep
    run_ins_ctgan = ExperimentRun(
        experiment_id="phase1_sdv_ctgan_50ep_insurance",
        phase="phase1", library="sdv", model="ctgan",
        dataset=ins_dataset,
        params={"random_seed": 42, "num_rows": len(ins_data), "epochs": 50},
    )
    with run_ins_ctgan:
        ctgan = CTGANSynthesizer(ins_meta, epochs=50)
        ctgan.fit(ins_data)
        synth = ctgan.sample(num_rows=len(ins_data))
        csv_path = os.path.join(ROOT, 'results/phase1/sdv_ctgan_50ep_insurance.csv')
        synth.to_csv(csv_path, index=False)
        run_ins_ctgan.set_output(csv_path=csv_path, rows=len(synth), columns=len(synth.columns))
    run_ins_ctgan.save_meta(META_DIR, library_version=sdv.__version__)
    runs.append(run_ins_ctgan)
    print(f"  CTGAN 50ep: {'OK' if run_ins_ctgan.status == 'ok' else 'ERROR'} ({run_ins_ctgan.elapsed_sec:.1f}s)")
except Exception as e:
    print(f"  ERROR: {e}")

# === 2. IMDB Small (multi_table) ===
print("\n=== IMDB Small (multi_table) ===")
try:
    imdb_data, imdb_meta = download_demo(modality='multi_table', dataset_name='imdb_small')
    for tname, df in imdb_data.items():
        df.to_csv(os.path.join(ROOT, f'data/raw/d_imdb_{tname}.csv'), index=False)
        print(f"  {tname}: {len(df)} rows, {len(df.columns)} cols")
    with open(os.path.join(ROOT, 'data/raw/d_imdb_metadata.json'), 'w') as f:
        json.dump(imdb_meta.to_dict(), f, indent=2)

    total_rows = sum(len(df) for df in imdb_data.values())
    imdb_dataset = {
        "name": "d_imdb_small",
        "path": "data/raw/d_imdb_*.csv",
        "rows": total_rows,
        "columns": sum(len(df.columns) for df in imdb_data.values()),
    }

    run_imdb = ExperimentRun(
        experiment_id="phase2_sdv_hma_imdb",
        phase="phase2", library="sdv", model="hma",
        dataset=imdb_dataset,
        params={"random_seed": 42},
    )
    with run_imdb:
        synthesizer = HMASynthesizer(imdb_meta)
        synthesizer.fit(imdb_data)
        synth_data = synthesizer.sample()

        table_csv_paths = {}
        for tname, df in synth_data.items():
            csv_path = os.path.join(ROOT, f'results/phase2/sdv_hma_imdb_{tname}.csv')
            df.to_csv(csv_path, index=False)
            table_csv_paths[tname] = csv_path
            print(f"  Synth {tname}: {len(df)} rows")

        run_imdb.set_multi_table_output(table_csv_paths, synth_data)

    run_imdb.save_meta(META_DIR, library_version=sdv.__version__)
    runs.append(run_imdb)
    print(f"  HMA: {'OK' if run_imdb.status == 'ok' else 'ERROR'} ({run_imdb.elapsed_sec:.1f}s)")
except Exception as e:
    print(f"  ERROR: {e}")

# === 3. Fake Companies (single_table) ===
print("\n=== Fake Companies (single_table) ===")
try:
    fc_data, fc_meta = download_demo(modality='single_table', dataset_name='fake_companies')
    fc_data.to_csv(os.path.join(ROOT, 'data/raw/d_fake_companies.csv'), index=False)
    print(f"  Downloaded: {len(fc_data)} rows, cols={list(fc_data.columns)}")

    fc_dataset = {
        "name": "d_fake_companies",
        "path": os.path.join(ROOT, 'data/raw/d_fake_companies.csv'),
        "rows": len(fc_data),
        "columns": len(fc_data.columns),
    }

    run_fc = ExperimentRun(
        experiment_id="phase1_sdv_gaussiancopula_fake_companies",
        phase="phase1", library="sdv", model="gaussiancopula",
        dataset=fc_dataset,
        params={"random_seed": 42, "num_rows": len(fc_data)},
    )
    with run_fc:
        gc = GaussianCopulaSynthesizer(fc_meta)
        gc.fit(fc_data)
        synth = gc.sample(num_rows=len(fc_data))
        csv_path = os.path.join(ROOT, 'results/phase1/sdv_gaussiancopula_fake_companies.csv')
        synth.to_csv(csv_path, index=False)
        run_fc.set_output(csv_path=csv_path, rows=len(synth), columns=len(synth.columns))
    run_fc.save_meta(META_DIR, library_version=sdv.__version__)
    runs.append(run_fc)
    print(f"  GaussianCopula: {'OK' if run_fc.status == 'ok' else 'ERROR'} ({run_fc.elapsed_sec:.1f}s)")
except Exception as e:
    print(f"  ERROR: {e}")

# 既存形式の run_log も出力（後方互換）
# additional_run_log は既存キー名を維持するため build_run_log ではなく手動構築
all_results = {}
key_map = {
    "phase1_sdv_gaussiancopula_insurance": "insurance_gaussiancopula",
    "phase1_sdv_ctgan_50ep_insurance": "insurance_ctgan_50ep",
    "phase2_sdv_hma_imdb": "imdb_hma",
    "phase1_sdv_gaussiancopula_fake_companies": "fake_companies_gaussiancopula",
}
for run in runs:
    key = key_map.get(run.experiment_id, run.experiment_id)
    entry = {"status": run.status, "time_sec": run.elapsed_sec}
    if run.status == "ok":
        if "rows" in run.output:
            entry["rows"] = run.output["rows"]
        if "tables" in run.output:
            entry["tables"] = {t: info["rows"] for t, info in run.output["tables"].items()}
    else:
        if run.error:
            entry["error"] = run.error["message"]
            entry["traceback"] = run.error["traceback"]
    all_results[key] = entry

all_results['_env'] = env
with open(os.path.join(ROOT, 'results/phase1/additional_run_log.json'), 'w') as f:
    json.dump(all_results, f, indent=2)

update_manifest(META_DIR)

print("\n=== All done ===")
print(json.dumps({k: v.get('status', v) if isinstance(v, dict) else v for k, v in all_results.items()}, indent=2))
