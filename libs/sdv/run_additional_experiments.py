"""追加実験: IMDB (multi-table), Insurance (single-table)

実行: cd libs/sdv && uv run --no-project python run_additional_experiments.py
"""
import pandas as pd
import json
import time
import traceback
import os
import platform
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..', '..')
os.makedirs(os.path.join(ROOT, 'results/phase1'), exist_ok=True)
os.makedirs(os.path.join(ROOT, 'results/phase2'), exist_ok=True)

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

all_results = {}

# === 1. Insurance (single_table) ===
print("=== Insurance (single_table) ===")
try:
    ins_data, ins_meta = download_demo(modality='single_table', dataset_name='insurance')
    ins_data.to_csv(os.path.join(ROOT, 'data/raw/d_insurance.csv'), index=False)
    with open(os.path.join(ROOT, 'data/raw/d_insurance_metadata.json'), 'w') as f:
        json.dump(ins_meta.to_dict(), f, indent=2)
    print(f"  Downloaded: {len(ins_data)} rows, {len(ins_data.columns)} cols")

    # GaussianCopula
    start = time.time()
    gc = GaussianCopulaSynthesizer(ins_meta)
    gc.fit(ins_data)
    synth = gc.sample(num_rows=len(ins_data))
    elapsed = time.time() - start
    synth.to_csv(os.path.join(ROOT, 'results/phase1/sdv_gaussiancopula_insurance.csv'), index=False)
    all_results['insurance_gaussiancopula'] = {'status': 'ok', 'time_sec': round(elapsed, 2), 'rows': len(synth)}
    print(f"  GaussianCopula: OK ({elapsed:.1f}s)")

    # CTGAN 50ep (smaller dataset)
    start = time.time()
    ctgan = CTGANSynthesizer(ins_meta, epochs=50)
    ctgan.fit(ins_data)
    synth = ctgan.sample(num_rows=len(ins_data))
    elapsed = time.time() - start
    synth.to_csv(os.path.join(ROOT, 'results/phase1/sdv_ctgan_50ep_insurance.csv'), index=False)
    all_results['insurance_ctgan_50ep'] = {'status': 'ok', 'time_sec': round(elapsed, 2), 'rows': len(synth)}
    print(f"  CTGAN 50ep: OK ({elapsed:.1f}s)")
except Exception as e:
    all_results['insurance'] = {'status': 'error', 'error': str(e), 'traceback': traceback.format_exc()}
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

    start = time.time()
    synthesizer = HMASynthesizer(imdb_meta)
    synthesizer.fit(imdb_data)
    synth_data = synthesizer.sample()
    elapsed = time.time() - start

    for tname, df in synth_data.items():
        df.to_csv(os.path.join(ROOT, f'results/phase2/sdv_hma_imdb_{tname}.csv'), index=False)
        print(f"  Synth {tname}: {len(df)} rows")

    all_results['imdb_hma'] = {
        'status': 'ok',
        'time_sec': round(elapsed, 2),
        'tables': {name: len(df) for name, df in synth_data.items()}
    }
    print(f"  HMA: OK ({elapsed:.1f}s)")
except Exception as e:
    all_results['imdb_hma'] = {'status': 'error', 'error': str(e), 'traceback': traceback.format_exc()}
    print(f"  ERROR: {e}")

# === 3. Fake Companies (single_table) ===
print("\n=== Fake Companies (single_table) ===")
try:
    fc_data, fc_meta = download_demo(modality='single_table', dataset_name='fake_companies')
    fc_data.to_csv(os.path.join(ROOT, 'data/raw/d_fake_companies.csv'), index=False)
    print(f"  Downloaded: {len(fc_data)} rows, cols={list(fc_data.columns)}")

    start = time.time()
    gc = GaussianCopulaSynthesizer(fc_meta)
    gc.fit(fc_data)
    synth = gc.sample(num_rows=len(fc_data))
    elapsed = time.time() - start
    synth.to_csv(os.path.join(ROOT, 'results/phase1/sdv_gaussiancopula_fake_companies.csv'), index=False)
    all_results['fake_companies_gaussiancopula'] = {'status': 'ok', 'time_sec': round(elapsed, 2), 'rows': len(synth)}
    print(f"  GaussianCopula: OK ({elapsed:.1f}s)")
except Exception as e:
    all_results['fake_companies'] = {'status': 'error', 'error': str(e), 'traceback': traceback.format_exc()}
    print(f"  ERROR: {e}")

# Save results
all_results['_env'] = env
with open(os.path.join(ROOT, 'results/phase1/additional_run_log.json'), 'w') as f:
    json.dump(all_results, f, indent=2)

print("\n=== All done ===")
print(json.dumps({k: v.get('status', v) if isinstance(v, dict) else v for k, v in all_results.items()}, indent=2))
