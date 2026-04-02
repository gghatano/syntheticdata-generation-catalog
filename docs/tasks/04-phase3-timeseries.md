# 04: Phase 3 — 時系列実験

## 目的

D3（NASDAQ時系列データ）を用いて、4つのライブラリで時系列合成データを生成し、
時系列パターンの再現性・長期依存関係・sequenceの多様性を評価する。

## 前提条件

- 00-setup 完了（各 `libs/*/` で `uv sync` 済み）
- 01-data-preparation 完了（`data/processed/d3_nasdaq.csv`, `data/raw/d3_nasdaq_metadata.json` が存在）

## 対象ライブラリ

| ID   | ライブラリ         | 環境               |
|------|----------------|------------------|
| L-01 | SDV            | `libs/sdv/`      |
| L-02 | SynthCity      | `libs/synthcity/` |
| L-03 | MOSTLY AI      | `libs/mostlyai/` |
| L-04 | ydata-synthetic | `libs/ydata/`    |

スクリプトには Phase 1 と同じ共通ヘルパー（`update_progress`, `get_env_info`）を含める。
全スクリプトで `RANDOM_SEED=42` を使用する。

---

## 実験 4-1: SDV (L-01)

**実行環境**: `libs/sdv/`

### libs/sdv/run_phase3.py

```python
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
REAL_DATA_PATH = os.path.join(ROOT, 'data/processed/d3_nasdaq.csv')
METADATA_PATH = os.path.join(ROOT, 'data/raw/d3_nasdaq_metadata.json')
OUTPUT_DIR = os.path.join(ROOT, 'results/phase3')
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

if not os.path.exists(REAL_DATA_PATH):
    print(f"ERROR: {REAL_DATA_PATH} not found. Run 01-data-preparation first.")
    sys.exit(1)

real_data = pd.read_csv(REAL_DATA_PATH)

from sdv.sequential import PARSynthesizer
from sdv.metadata import Metadata
import sdv

metadata = Metadata.load_from_dict(json.load(open(METADATA_PATH)))

results = {}
env = {
    'python_version': platform.python_version(),
    'sdv_version': sdv.__version__,
    'timestamp': datetime.now().isoformat(),
}

update_progress('04-phase3', 'in_progress', current_step='sdv')

try:
    start = time.time()
    synthesizer = PARSynthesizer(metadata, epochs=128)
    synthesizer.fit(real_data)
    synth_data = synthesizer.sample(num_sequences=real_data[metadata.sequence_key].nunique())
    elapsed = time.time() - start

    synth_data.to_csv(os.path.join(OUTPUT_DIR, 'sdv_par.csv'), index=False)
    results['sdv_par'] = {
        'status': 'ok',
        'time_sec': round(elapsed, 2),
        'rows': len(synth_data),
        'sequences': synth_data[metadata.sequence_key].nunique() if hasattr(metadata, 'sequence_key') else 'unknown'
    }
    print(f"SDV PAR: OK ({elapsed:.1f}s, {len(synth_data)} rows)")
except Exception as e:
    results['sdv_par'] = {'status': 'error', 'error': str(e), 'traceback': traceback.format_exc()}
    print(f"SDV PAR: ERROR - {e}")

results['_env'] = env
with open(os.path.join(OUTPUT_DIR, 'sdv_run_log.json'), 'w') as f:
    json.dump(results, f, indent=2)

print("SDV Phase3 complete.")
```

**実行**:
```bash
cd /home/hatano/works/syntheticdata-catalog/libs/sdv
uv run python run_phase3.py
```

---

## 実験 4-2: SynthCity (L-02)

**実行環境**: `libs/synthcity/`

### libs/synthcity/run_phase3.py

```python
import pandas as pd
import json
import time
import traceback
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..', '..')
REAL_DATA_PATH = os.path.join(ROOT, 'data/processed/d3_nasdaq.csv')
OUTPUT_DIR = os.path.join(ROOT, 'results/phase3')
os.makedirs(OUTPUT_DIR, exist_ok=True)

real_data = pd.read_csv(REAL_DATA_PATH)

from synthcity.plugins import Plugins
from synthcity.plugins.core.dataloader import TimeSeriesDataLoader

results = {}

# 時系列用のデータローダー設定
# sequence_key と time_key はデータに応じて調整が必要
metadata = json.load(open(os.path.join(ROOT, 'data/raw/d3_nasdaq_metadata.json')))

# SDV metadata から sequence/time key を取得
seq_key = None
time_key = None
if 'columns' in metadata:
    for col_name, col_info in metadata['columns'].items():
        if col_info.get('sdtype') == 'id':
            seq_key = col_name
        if col_info.get('sdtype') == 'datetime':
            time_key = col_name

print(f"Sequence key: {seq_key}, Time key: {time_key}")

# SynthCity の時系列プラグイン
ts_models = ['timegan']
available = Plugins(categories=['time_series']).list()
print(f"Available time series models: {available}")
models_to_run = [m for m in ts_models if m in available]

for model_name in models_to_run:
    try:
        # TimeSeriesDataLoader の構築
        loader = TimeSeriesDataLoader(
            temporal_data=real_data,
            seq_id=seq_key,
        )
        
        start = time.time()
        plugin = Plugins().get(model_name)
        plugin.fit(loader)
        synth = plugin.generate(count=len(real_data))
        elapsed = time.time() - start

        synth_df = synth.dataframe()
        synth_df.to_csv(os.path.join(OUTPUT_DIR, f'synthcity_{model_name}.csv'), index=False)
        results[f'synthcity_{model_name}'] = {'status': 'ok', 'time_sec': round(elapsed, 2), 'rows': len(synth_df)}
        print(f"{model_name}: OK ({elapsed:.1f}s)")
    except Exception as e:
        results[f'synthcity_{model_name}'] = {'status': 'error', 'error': str(e), 'traceback': traceback.format_exc()}
        print(f"{model_name}: ERROR - {e}")

if not models_to_run:
    results['synthcity_timeseries'] = {'status': 'skipped', 'reason': f'No time series models available. Found: {available}'}

with open(os.path.join(OUTPUT_DIR, 'synthcity_run_log.json'), 'w') as f:
    json.dump(results, f, indent=2)

print("SynthCity Phase3 complete.")
```

**実行**:
```bash
cd /home/hatano/works/syntheticdata-catalog/libs/synthcity
uv run python run_phase3.py
```

---

## 実験 4-3: MOSTLY AI (L-03)

**実行環境**: `libs/mostlyai/`

### libs/mostlyai/run_phase3.py

```python
import pandas as pd
import json
import time
import traceback
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..', '..')
REAL_DATA_PATH = os.path.join(ROOT, 'data/processed/d3_nasdaq.csv')
OUTPUT_DIR = os.path.join(ROOT, 'results/phase3')
os.makedirs(OUTPUT_DIR, exist_ok=True)

api_key = os.environ.get('MOSTLY_AI_API_KEY')
results = {}

if not api_key:
    print("SKIP: MOSTLY_AI_API_KEY not set")
    results['mostlyai_ts'] = {'status': 'skipped', 'reason': 'MOSTLY_AI_API_KEY not set'}
else:
    try:
        from mostlyai import MostlyAI
        mostly = MostlyAI(api_key=api_key)
        real_data = pd.read_csv(REAL_DATA_PATH)

        start = time.time()
        sd = mostly.train(data=real_data)
        synth = mostly.generate(sd, size=len(real_data))
        elapsed = time.time() - start

        synth.to_csv(os.path.join(OUTPUT_DIR, 'mostlyai_ts.csv'), index=False)
        results['mostlyai_ts'] = {'status': 'ok', 'time_sec': round(elapsed, 2), 'rows': len(synth)}
        print(f"MOSTLY AI TS: OK ({elapsed:.1f}s)")
    except Exception as e:
        results['mostlyai_ts'] = {'status': 'error', 'error': str(e), 'traceback': traceback.format_exc()}
        print(f"MOSTLY AI TS: ERROR - {e}")

with open(os.path.join(OUTPUT_DIR, 'mostlyai_run_log.json'), 'w') as f:
    json.dump(results, f, indent=2)

print("MOSTLY AI Phase3 complete.")
```

**実行**:
```bash
cd /home/hatano/works/syntheticdata-catalog/libs/mostlyai
MOSTLY_AI_API_KEY=<your-key> uv run python run_phase3.py
```

---

## 実験 4-4: ydata-synthetic (L-04)

**実行環境**: `libs/ydata/`

### libs/ydata/run_phase3.py

```python
import pandas as pd
import json
import time
import traceback
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..', '..')
REAL_DATA_PATH = os.path.join(ROOT, 'data/processed/d3_nasdaq.csv')
OUTPUT_DIR = os.path.join(ROOT, 'results/phase3')
os.makedirs(OUTPUT_DIR, exist_ok=True)

real_data = pd.read_csv(REAL_DATA_PATH)
results = {}

try:
    from ydata_synthetic.synthesizers.timeseries import TimeSeriesSynthesizer
    from ydata_synthetic.synthesizers import ModelParameters, TrainParameters

    # 数値列の特定
    num_cols = real_data.select_dtypes(include=['number']).columns.tolist()

    start = time.time()

    model_params = ModelParameters(batch_size=128, lr=5e-4, betas=(0.5, 0.9))
    train_params = TrainParameters(epochs=100)

    synth = TimeSeriesSynthesizer(modelname='timegan', model_parameters=model_params)
    synth.fit(data=real_data, train_arguments=train_params, num_cols=num_cols)
    synth_data = synth.sample(n_samples=len(real_data))
    elapsed = time.time() - start

    if isinstance(synth_data, pd.DataFrame):
        synth_data.to_csv(os.path.join(OUTPUT_DIR, 'ydata_timegan.csv'), index=False)
        rows = len(synth_data)
    else:
        # numpy array の場合
        import numpy as np
        synth_df = pd.DataFrame(synth_data.reshape(-1, synth_data.shape[-1]), columns=num_cols)
        synth_df.to_csv(os.path.join(OUTPUT_DIR, 'ydata_timegan.csv'), index=False)
        rows = len(synth_df)

    results['ydata_timegan'] = {'status': 'ok', 'time_sec': round(elapsed, 2), 'rows': rows}
    print(f"ydata TimeGAN: OK ({elapsed:.1f}s)")
except Exception as e:
    results['ydata_timegan'] = {'status': 'error', 'error': str(e), 'traceback': traceback.format_exc()}
    print(f"ydata TimeGAN: ERROR - {e}")

with open(os.path.join(OUTPUT_DIR, 'ydata_run_log.json'), 'w') as f:
    json.dump(results, f, indent=2)

print("ydata Phase3 complete.")
```

**実行**:
```bash
cd /home/hatano/works/syntheticdata-catalog/libs/ydata
uv run python run_phase3.py
```

---

## 実験 4-5: 時系列評価

**実行環境**: `libs/evaluation/`

### libs/evaluation/eval_phase3.py

```python
import pandas as pd
import numpy as np
import json
import glob
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..', '..')
REAL_DATA_PATH = os.path.join(ROOT, 'data/processed/d3_nasdaq.csv')
OUTPUT_DIR = os.path.join(ROOT, 'results/phase3')

real_data = pd.read_csv(REAL_DATA_PATH)
num_cols = real_data.select_dtypes(include=['number']).columns.tolist()

eval_results = {}

def compute_ts_metrics(real_df, synth_df, num_cols):
    """時系列固有の評価指標"""
    metrics = {}
    
    for col in num_cols:
        if col not in synth_df.columns:
            continue
        real_vals = real_df[col].dropna()
        synth_vals = synth_df[col].dropna()
        
        # 基本統計量の比較
        metrics[col] = {
            'mean_diff': abs(real_vals.mean() - synth_vals.mean()),
            'std_diff': abs(real_vals.std() - synth_vals.std()),
            'real_mean': round(real_vals.mean(), 4),
            'synth_mean': round(synth_vals.mean(), 4),
            'real_std': round(real_vals.std(), 4),
            'synth_std': round(synth_vals.std(), 4),
        }
        
        # 自己相関の比較（lag=1）
        if len(real_vals) > 1 and len(synth_vals) > 1:
            real_autocorr = real_vals.autocorr(lag=1)
            synth_autocorr = synth_vals.autocorr(lag=1)
            metrics[col]['autocorr_lag1_real'] = round(real_autocorr, 4) if not np.isnan(real_autocorr) else None
            metrics[col]['autocorr_lag1_synth'] = round(synth_autocorr, 4) if not np.isnan(synth_autocorr) else None
    
    return metrics

for synth_file in sorted(glob.glob(os.path.join(OUTPUT_DIR, '*.csv'))):
    name = os.path.basename(synth_file).replace('.csv', '')
    if '_log' in name or '_eval' in name:
        continue
    try:
        synth_df = pd.read_csv(synth_file)
        metrics = compute_ts_metrics(real_data, synth_df, num_cols)
        eval_results[name] = {'status': 'ok', 'metrics': metrics}
        print(f"{name}: evaluated {len(metrics)} columns")
    except Exception as e:
        eval_results[name] = {'status': 'error', 'error': str(e)}
        print(f"{name}: ERROR - {e}")

with open(os.path.join(OUTPUT_DIR, 'eval_results.json'), 'w') as f:
    json.dump(eval_results, f, indent=2, default=str)

print("Phase3 evaluation complete.")
```

**実行**:
```bash
cd /home/hatano/works/syntheticdata-catalog/libs/evaluation
uv run python eval_phase3.py
```

---

## 完了条件

- [ ] 各ライブラリの合成データ CSV が `results/phase3/` に存在（エラー時は run_log に記録）
- [ ] 各ライブラリの `*_run_log.json` が存在
- [ ] `results/phase3/eval_results.json` が存在

## 権限・エラー対策

- **TimeGAN の学習時間**: CPU 環境では数十分〜数時間かかる場合がある。epochs を 50 に削減して対応
- **SynthCity 時系列**: `TimeSeriesDataLoader` のインターフェースはバージョン依存が強い。エラー時は `GenericDataLoader` にフォールバック
- **ydata の出力形式**: numpy array で返る場合があるため、DataFrame への変換処理を含む
- **PAR (SDV)**: sequence_key の自動検出に失敗する場合は、metadata の手動設定が必要
- **メモリ**: 時系列データは系列長×特徴量でメモリを消費。OOM 時はデータをサンプリング
