# 03: Phase 2 — 複数表実験

## 目的

D2（マスター・トランザクション構造）を用いて、複数表対応の2ライブラリで合成データを生成し、
外部キー整合性・分布再現性・親子関係の保持を評価する。

## 前提条件

- 00-setup 完了（`libs/sdv/`, `libs/mostlyai/` で `uv sync` 済み）
- 01-data-preparation 完了（`data/processed/d2_*.csv` が2ファイル以上存在、`data/raw/d2_metadata.json` が存在）

## 対象ライブラリ

| ID   | ライブラリ   | 環境           |
|------|----------|--------------|
| L-01 | SDV      | `libs/sdv/`  |
| L-03 | MOSTLY AI | `libs/mostlyai/` |

スクリプトには Phase 1 と同じ共通ヘルパー（`update_progress`, `get_env_info`）を含める。

---

## 実験 3-1: SDV (L-01)

**実行環境**: `libs/sdv/`

### libs/sdv/run_phase2.py

```python
import pandas as pd
import json
import time
import traceback
import os
import sys
import glob
import platform
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..', '..')
OUTPUT_DIR = os.path.join(ROOT, 'results/phase2')
PROGRESS_FILE = os.path.join(ROOT, 'docs/tasks/progress.json')
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

from sdv.multi_table import HMASynthesizer
from sdv.metadata import Metadata
import sdv

# D2 データの読み込み
metadata_dict = json.load(open(os.path.join(ROOT, 'data/raw/d2_metadata.json')))
metadata = Metadata.load_from_dict(metadata_dict)

# 複数テーブルを dict で読み込み
data = {}
for csv_file in glob.glob(os.path.join(ROOT, 'data/processed/d2_*.csv')):
    # d2_hotels.csv → hotels
    table_name = os.path.basename(csv_file).replace('d2_', '').replace('.csv', '')
    data[table_name] = pd.read_csv(csv_file)
    print(f"Loaded {table_name}: {len(data[table_name])} rows")

results = {}
env = {
    'python_version': platform.python_version(),
    'sdv_version': sdv.__version__,
    'timestamp': datetime.now().isoformat(),
}

update_progress('03-phase2', 'in_progress', current_step='sdv')

try:
    start = time.time()
    synthesizer = HMASynthesizer(metadata)
    synthesizer.fit(data)
    synth_data = synthesizer.sample()  # dict of DataFrames
    elapsed = time.time() - start

    for table_name, df in synth_data.items():
        df.to_csv(os.path.join(OUTPUT_DIR, f'sdv_hma_{table_name}.csv'), index=False)

    results['sdv_hma'] = {
        'status': 'ok',
        'time_sec': round(elapsed, 2),
        'tables': {name: len(df) for name, df in synth_data.items()}
    }
    print(f"SDV HMA: OK ({elapsed:.1f}s)")
except Exception as e:
    results['sdv_hma'] = {'status': 'error', 'error': str(e), 'traceback': traceback.format_exc()}
    print(f"SDV HMA: ERROR - {e}")

results['_env'] = env
with open(os.path.join(OUTPUT_DIR, 'sdv_run_log.json'), 'w') as f:
    json.dump(results, f, indent=2)

print("SDV Phase2 complete.")
```

**実行**:
```bash
cd /home/hatano/works/syntheticdata-catalog/libs/sdv
uv run python run_phase2.py
```

---

## 実験 3-2: MOSTLY AI (L-03)

**実行環境**: `libs/mostlyai/`

### libs/mostlyai/run_phase2.py

```python
import pandas as pd
import json
import time
import traceback
import os
import glob

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..', '..')
OUTPUT_DIR = os.path.join(ROOT, 'results/phase2')
os.makedirs(OUTPUT_DIR, exist_ok=True)

api_key = os.environ.get('MOSTLY_AI_API_KEY')
results = {}

if not api_key:
    print("SKIP: MOSTLY_AI_API_KEY not set")
    results['mostlyai_multi'] = {'status': 'skipped', 'reason': 'MOSTLY_AI_API_KEY not set'}
else:
    try:
        from mostlyai import MostlyAI
        mostly = MostlyAI(api_key=api_key)

        # 複数テーブルの読み込み
        data = {}
        for csv_file in sorted(glob.glob(os.path.join(ROOT, 'data/processed/d2_*.csv'))):
            table_name = os.path.basename(csv_file).replace('d2_', '').replace('.csv', '')
            data[table_name] = pd.read_csv(csv_file)

        start = time.time()
        # MOSTLY AI の multi-table API（SDK バージョンにより異なる）
        sd = mostly.train(data=data)
        synth = mostly.generate(sd)
        elapsed = time.time() - start

        for table_name, df in synth.items():
            df.to_csv(os.path.join(OUTPUT_DIR, f'mostlyai_{table_name}.csv'), index=False)

        results['mostlyai_multi'] = {
            'status': 'ok',
            'time_sec': round(elapsed, 2),
            'tables': {name: len(df) for name, df in synth.items()}
        }
        print(f"MOSTLY AI Multi: OK ({elapsed:.1f}s)")
    except Exception as e:
        results['mostlyai_multi'] = {'status': 'error', 'error': str(e), 'traceback': traceback.format_exc()}
        print(f"MOSTLY AI Multi: ERROR - {e}")

with open(os.path.join(OUTPUT_DIR, 'mostlyai_run_log.json'), 'w') as f:
    json.dump(results, f, indent=2)

print("MOSTLY AI Phase2 complete.")
```

**実行**:
```bash
cd /home/hatano/works/syntheticdata-catalog/libs/mostlyai
MOSTLY_AI_API_KEY=<your-key> uv run python run_phase2.py
```

---

## 実験 3-3: 複数表評価

**実行環境**: `libs/evaluation/`

### libs/evaluation/eval_phase2.py

```python
import pandas as pd
import json
import os
import glob

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..', '..')
OUTPUT_DIR = os.path.join(ROOT, 'results/phase2')

metadata_dict = json.load(open(os.path.join(ROOT, 'data/raw/d2_metadata.json')))

from sdmetrics.reports.multi_table import QualityReport

# 元データの読み込み
real_data = {}
for csv_file in sorted(glob.glob(os.path.join(ROOT, 'data/processed/d2_*.csv'))):
    table_name = os.path.basename(csv_file).replace('d2_', '').replace('.csv', '')
    real_data[table_name] = pd.read_csv(csv_file)

eval_results = {}

# SDV HMA の評価
sdv_synth = {}
for csv_file in sorted(glob.glob(os.path.join(OUTPUT_DIR, 'sdv_hma_*.csv'))):
    table_name = os.path.basename(csv_file).replace('sdv_hma_', '').replace('.csv', '')
    sdv_synth[table_name] = pd.read_csv(csv_file)

if sdv_synth:
    try:
        report = QualityReport()
        report.generate(real_data, sdv_synth, metadata_dict)
        eval_results['sdv_hma'] = {
            'quality_score': report.get_score(),
            'properties': report.get_properties().to_dict(),
        }
        print(f"SDV HMA quality: {report.get_score():.4f}")
    except Exception as e:
        eval_results['sdv_hma'] = {'status': 'error', 'error': str(e)}

# FK 整合性チェック（汎用）
def check_fk_integrity(parent_df, child_df, parent_key, child_fk):
    """外部キーの整合性を検証"""
    parent_ids = set(parent_df[parent_key])
    child_fks = set(child_df[child_fk])
    orphans = child_fks - parent_ids
    return {
        'parent_unique_keys': len(parent_ids),
        'child_fk_unique': len(child_fks),
        'orphan_count': len(orphans),
        'orphan_rate': round(len(orphans) / len(child_fks), 4) if child_fks else 0,
        'integrity': len(orphans) == 0,
    }

# FK チェック結果は metadata の relationships から自動取得
if 'relationships' in metadata_dict:
    for rel in metadata_dict['relationships']:
        parent_table = rel.get('parent_table_name')
        child_table = rel.get('child_table_name')
        parent_key = rel.get('parent_primary_key')
        child_fk = rel.get('child_foreign_key')

        for prefix, synth_data in [('sdv_hma', sdv_synth)]:
            if parent_table in synth_data and child_table in synth_data:
                fk_result = check_fk_integrity(
                    synth_data[parent_table], synth_data[child_table],
                    parent_key, child_fk
                )
                eval_results[f'{prefix}_fk_{parent_table}_{child_table}'] = fk_result
                print(f"FK {prefix} {parent_table}->{child_table}: orphans={fk_result['orphan_count']}")

with open(os.path.join(OUTPUT_DIR, 'eval_results.json'), 'w') as f:
    json.dump(eval_results, f, indent=2, default=str)

print("Phase2 evaluation complete.")
```

**実行**:
```bash
cd /home/hatano/works/syntheticdata-catalog/libs/evaluation
uv run python eval_phase2.py
```

---

## 完了条件

- [ ] SDV: `results/phase2/sdv_hma_*.csv` が存在（テーブル数分）
- [ ] MOSTLY AI: 実行またはスキップ記録
- [ ] `results/phase2/eval_results.json` が存在
- [ ] FK 整合性チェックが完了

## 権限・エラー対策

- **HMA の学習時間**: テーブル間関係が複雑だと時間がかかる。SDV の demo dataset なら数分以内
- **メモリ**: 複数表の同時保持が必要。大規模データの場合はサンプリングを検討
- **MOSTLY AI**: API キー未設定なら自動スキップ
- **metadata フォーマット**: SDV バージョンにより metadata の構造が異なる場合がある。`Metadata.detect_from_dataframes(data)` で自動検出も可能
