"""Phase 1 の全合成データに対する SDMetrics 統一評価"""
import pandas as pd
import json
import glob
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..', '..')
REAL_DATA_PATH = os.path.join(ROOT, 'data/processed/d1_adult.csv')
METADATA_PATH = os.path.join(ROOT, 'data/raw/d1_adult_metadata.json')
OUTPUT_DIR = os.path.join(ROOT, 'results/phase1')

real_data = pd.read_csv(REAL_DATA_PATH)
metadata_raw = json.load(open(METADATA_PATH))

# SDV v1+ metadata は multi-table 形式。single_table 部分を抽出
if 'tables' in metadata_raw:
    table_name = list(metadata_raw['tables'].keys())[0]
    metadata_dict = metadata_raw['tables'][table_name]
else:
    metadata_dict = metadata_raw

from sdmetrics.reports.single_table import QualityReport, DiagnosticReport

eval_results = {}

for synth_file in sorted(glob.glob(os.path.join(OUTPUT_DIR, '*.csv'))):
    name = os.path.basename(synth_file).replace('.csv', '')
    print(f"Evaluating: {name}")
    try:
        synth = pd.read_csv(synth_file)

        if set(synth.columns) != set(real_data.columns):
            eval_results[name] = {'status': 'error', 'error': 'Column mismatch'}
            print(f"  SKIP: column mismatch")
            continue

        quality = QualityReport()
        quality.generate(real_data, synth, metadata_dict)

        diag = DiagnosticReport()
        diag.generate(real_data, synth, metadata_dict)

        eval_results[name] = {
            'quality_score': quality.get_score(),
            'diagnostic_score': diag.get_score(),
        }
        print(f"  Quality: {quality.get_score():.4f}, Diagnostic: {diag.get_score():.4f}")
    except Exception as e:
        eval_results[name] = {'status': 'error', 'error': str(e)}
        print(f"  ERROR: {e}")

with open(os.path.join(OUTPUT_DIR, 'sdmetrics_eval.json'), 'w') as f:
    json.dump(eval_results, f, indent=2, default=str)

print(f"\nEvaluated {len(eval_results)} models. Saved to results/phase1/sdmetrics_eval.json")
