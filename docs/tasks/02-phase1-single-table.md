# 02: Phase 1 — 単一表実験

## 目的

D1（Adult dataset）を用いて、4つのライブラリで合成データを生成し、
統計的類似性・下流タスク性能・プライバシーを評価する。

## 前提条件

- 00-setup 完了（各 `libs/*/` で `uv sync` 済み）
- 01-data-preparation 完了（`data/processed/d1_adult.csv`、`data/raw/d1_adult_metadata.json` が存在）

## 共通パターン

- 各ライブラリの実験は独立 → 並列実行可能
- スクリプトは `libs/<library>/run_phase1.py` に配置
- 実行: `cd libs/<library> && uv run python run_phase1.py`
- 結果出力先: `results/phase1/`
- 全スクリプトで `RANDOM_SEED=42` を使用
- run_log にはライブラリバージョン・Python バージョンを記録

### 共通ヘルパー（各スクリプト冒頭に含める）

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
REAL_DATA_PATH = os.path.join(ROOT, 'data/processed/d1_adult.csv')
METADATA_PATH = os.path.join(ROOT, 'data/raw/d1_adult_metadata.json')
OUTPUT_DIR = os.path.join(ROOT, 'results/phase1')
PROGRESS_FILE = os.path.join(ROOT, 'docs/tasks/progress.json')
RANDOM_SEED = 42

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

def get_env_info():
    """実行環境情報を取得"""
    return {
        'python_version': platform.python_version(),
        'platform': platform.platform(),
        'timestamp': datetime.now().isoformat(),
    }

# 前提条件チェック
if not os.path.exists(REAL_DATA_PATH):
    print(f"ERROR: {REAL_DATA_PATH} not found. Run 01-data-preparation first.")
    sys.exit(1)

real_data = pd.read_csv(REAL_DATA_PATH)
print(f"Loaded real data: {len(real_data)} rows, {len(real_data.columns)} columns")
```

---

## 実験 2-1: SDV (L-01)

**実行環境**: `libs/sdv/`

### libs/sdv/run_phase1.py

上記共通ヘルパーの後に:

```python
from sdv.single_table import GaussianCopulaSynthesizer, CTGANSynthesizer
from sdv.metadata import Metadata
import sdv

metadata = Metadata.load_from_dict(json.load(open(METADATA_PATH)))

results = {}
env = get_env_info()
env['sdv_version'] = sdv.__version__

update_progress('02-phase1', 'in_progress', current_step='sdv')

# --- GaussianCopula ---
try:
    start = time.time()
    gc = GaussianCopulaSynthesizer(metadata)
    gc.fit(real_data)
    synth_gc = gc.sample(num_rows=len(real_data))
    elapsed = time.time() - start
    synth_gc.to_csv(os.path.join(OUTPUT_DIR, 'sdv_gaussiancopula.csv'), index=False)
    results['sdv_gaussiancopula'] = {'status': 'ok', 'time_sec': round(elapsed, 2), 'rows': len(synth_gc)}
    print(f"GaussianCopula: OK ({elapsed:.1f}s, {len(synth_gc)} rows)")
except Exception as e:
    results['sdv_gaussiancopula'] = {'status': 'error', 'error': str(e), 'traceback': traceback.format_exc()}
    print(f"GaussianCopula: ERROR - {e}")

# --- CTGAN ---
try:
    start = time.time()
    ctgan = CTGANSynthesizer(metadata, epochs=100)
    ctgan.fit(real_data)
    synth_ctgan = ctgan.sample(num_rows=len(real_data))
    elapsed = time.time() - start
    synth_ctgan.to_csv(os.path.join(OUTPUT_DIR, 'sdv_ctgan.csv'), index=False)
    results['sdv_ctgan'] = {'status': 'ok', 'time_sec': round(elapsed, 2), 'rows': len(synth_ctgan)}
    print(f"CTGAN: OK ({elapsed:.1f}s, {len(synth_ctgan)} rows)")
except Exception as e:
    results['sdv_ctgan'] = {'status': 'error', 'error': str(e), 'traceback': traceback.format_exc()}
    print(f"CTGAN: ERROR - {e}")

results['_env'] = env
with open(os.path.join(OUTPUT_DIR, 'sdv_run_log.json'), 'w') as f:
    json.dump(results, f, indent=2)

print("SDV Phase1 complete.")
```

**実行**:
```bash
cd /home/hatano/works/syntheticdata-catalog/libs/sdv
uv run python run_phase1.py
```

---

## 実験 2-2: SynthCity (L-02)

**実行環境**: `libs/synthcity/`

### libs/synthcity/run_phase1.py

共通ヘルパーの後に:

```python
from synthcity.plugins import Plugins
from synthcity.plugins.core.dataloader import GenericDataLoader

loader = GenericDataLoader(real_data)

# 利用可能モデルの確認
available = Plugins().list()
print(f"Available models: {available}")

target_models = ['marginal_distributions', 'bayesian_network', 'ctgan', 'tvae']
models_to_run = [m for m in target_models if m in available]
print(f"Running: {models_to_run}")

results = {}
env = get_env_info()
try:
    import synthcity
    env['synthcity_version'] = getattr(synthcity, '__version__', 'unknown')
except:
    pass

update_progress('02-phase1', 'in_progress', current_step='synthcity')

for model_name in models_to_run:
    try:
        start = time.time()
        plugin = Plugins().get(model_name)
        plugin.fit(loader)
        synth = plugin.generate(count=len(real_data)).dataframe()
        elapsed = time.time() - start
        synth.to_csv(os.path.join(OUTPUT_DIR, f'synthcity_{model_name}.csv'), index=False)
        results[f'synthcity_{model_name}'] = {'status': 'ok', 'time_sec': round(elapsed, 2), 'rows': len(synth)}
        print(f"{model_name}: OK ({elapsed:.1f}s)")
    except Exception as e:
        results[f'synthcity_{model_name}'] = {'status': 'error', 'error': str(e), 'traceback': traceback.format_exc()}
        print(f"{model_name}: ERROR - {e}")

if not models_to_run:
    results['synthcity'] = {'status': 'error', 'error': f'No target models available. Found: {available}'}

results['_env'] = env
with open(os.path.join(OUTPUT_DIR, 'synthcity_run_log.json'), 'w') as f:
    json.dump(results, f, indent=2)

print("SynthCity Phase1 complete.")
```

**実行**:
```bash
cd /home/hatano/works/syntheticdata-catalog/libs/synthcity
uv run python run_phase1.py
```

---

## 実験 2-3: MOSTLY AI (L-03)

**実行環境**: `libs/mostlyai/`

### libs/mostlyai/run_phase1.py

共通ヘルパーの後に:

```python
api_key = os.environ.get('MOSTLY_AI_API_KEY')
results = {}
env = get_env_info()

update_progress('02-phase1', 'in_progress', current_step='mostlyai')

if not api_key:
    print("SKIP: MOSTLY_AI_API_KEY not set")
    results['mostlyai'] = {'status': 'skipped', 'reason': 'MOSTLY_AI_API_KEY not set'}
else:
    try:
        from mostlyai import MostlyAI
        env['mostlyai_version'] = getattr(MostlyAI, '__version__', 'unknown')
        mostly = MostlyAI(api_key=api_key)

        start = time.time()
        sd = mostly.train(data=real_data)
        synth = mostly.generate(sd, size=len(real_data))
        elapsed = time.time() - start

        synth.to_csv(os.path.join(OUTPUT_DIR, 'mostlyai.csv'), index=False)
        results['mostlyai'] = {'status': 'ok', 'time_sec': round(elapsed, 2), 'rows': len(synth)}
        print(f"MOSTLY AI: OK ({elapsed:.1f}s)")
    except Exception as e:
        results['mostlyai'] = {'status': 'error', 'error': str(e), 'traceback': traceback.format_exc()}
        print(f"MOSTLY AI: ERROR - {e}")

results['_env'] = env
with open(os.path.join(OUTPUT_DIR, 'mostlyai_run_log.json'), 'w') as f:
    json.dump(results, f, indent=2)

print("MOSTLY AI Phase1 complete.")
```

**実行**:
```bash
cd /home/hatano/works/syntheticdata-catalog/libs/mostlyai
MOSTLY_AI_API_KEY=<your-key> uv run python run_phase1.py
```

---

## 実験 2-4: ydata-synthetic (L-04)

**実行環境**: `libs/ydata/`

### libs/ydata/run_phase1.py

共通ヘルパーの後に:

```python
results = {}
env = get_env_info()

update_progress('02-phase1', 'in_progress', current_step='ydata')

try:
    from ydata_synthetic.synthesizers.regular import RegularSynthesizer
    from ydata_synthetic.synthesizers import ModelParameters, TrainParameters
    import ydata_synthetic
    env['ydata_version'] = getattr(ydata_synthetic, '__version__', 'unknown')

    cat_cols = real_data.select_dtypes(include=['object', 'category']).columns.tolist()
    num_cols = real_data.select_dtypes(include=['number']).columns.tolist()

    start = time.time()
    model_params = ModelParameters(batch_size=500, lr=2e-4, betas=(0.5, 0.9))
    train_params = TrainParameters(epochs=100)

    synth = RegularSynthesizer(modelname='ctgan', model_parameters=model_params)
    synth.fit(data=real_data, train_arguments=train_params, num_cols=num_cols, cat_cols=cat_cols)
    synth_data = synth.sample(len(real_data))
    elapsed = time.time() - start

    synth_data.to_csv(os.path.join(OUTPUT_DIR, 'ydata_ctgan.csv'), index=False)
    results['ydata_ctgan'] = {'status': 'ok', 'time_sec': round(elapsed, 2), 'rows': len(synth_data)}
    print(f"ydata CTGAN: OK ({elapsed:.1f}s)")
except Exception as e:
    results['ydata_ctgan'] = {'status': 'error', 'error': str(e), 'traceback': traceback.format_exc()}
    print(f"ydata CTGAN: ERROR - {e}")

results['_env'] = env
with open(os.path.join(OUTPUT_DIR, 'ydata_run_log.json'), 'w') as f:
    json.dump(results, f, indent=2)

print("ydata Phase1 complete.")
```

**実行**:
```bash
cd /home/hatano/works/syntheticdata-catalog/libs/ydata
uv run python run_phase1.py
```

---

## 評価 2-5: SDMetrics 統一評価（全ライブラリ共通）

**実行環境**: `libs/evaluation/`

Phase 1 で生成された全合成データに対して SDMetrics の QualityReport / DiagnosticReport を実行する。

### libs/evaluation/sdmetrics_phase1.py

```python
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
metadata_dict = json.load(open(METADATA_PATH))

from sdmetrics.reports.single_table import QualityReport, DiagnosticReport

eval_results = {}

for synth_file in sorted(glob.glob(os.path.join(OUTPUT_DIR, '*.csv'))):
    name = os.path.basename(synth_file).replace('.csv', '')
    print(f"Evaluating: {name}")
    try:
        synth = pd.read_csv(synth_file)

        # カラム一致チェック
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
            'quality_details': quality.get_properties().to_dict() if hasattr(quality.get_properties(), 'to_dict') else str(quality.get_properties()),
        }
        print(f"  Quality: {quality.get_score():.4f}, Diagnostic: {diag.get_score():.4f}")
    except Exception as e:
        eval_results[name] = {'status': 'error', 'error': str(e)}
        print(f"  ERROR: {e}")

with open(os.path.join(OUTPUT_DIR, 'sdmetrics_eval.json'), 'w') as f:
    json.dump(eval_results, f, indent=2, default=str)

print(f"\nEvaluated {len(eval_results)} models. Saved to results/phase1/sdmetrics_eval.json")
```

**実行**:
```bash
cd /home/hatano/works/syntheticdata-catalog/libs/evaluation
uv run python sdmetrics_phase1.py
```

---

## 評価 2-6: TSTR（Train on Synthetic, Test on Real）

**実行環境**: `libs/evaluation/`

### libs/evaluation/tstr_phase1.py

```python
"""Phase 1 TSTR 評価: 合成データで学習 → 実データでテスト"""
import pandas as pd
import json
import glob
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.preprocessing import LabelEncoder

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..', '..')
REAL_DATA_PATH = os.path.join(ROOT, 'data/processed/d1_adult.csv')
OUTPUT_DIR = os.path.join(ROOT, 'results/phase1')
RANDOM_SEED = 42

real_data = pd.read_csv(REAL_DATA_PATH)

# ターゲット列の自動検出
TARGET = None
for candidate in ['income', 'target', 'label', 'class']:
    if candidate in real_data.columns:
        TARGET = candidate
        break
if TARGET is None:
    TARGET = real_data.columns[-1]
print(f"Target column: {TARGET}")

def encode_dataframe(df):
    df_enc = df.copy()
    for col in df_enc.select_dtypes(include=['object', 'category']).columns:
        df_enc[col] = df_enc[col].fillna('_MISSING_')
    for col in df_enc.select_dtypes(include=['number']).columns:
        df_enc[col] = df_enc[col].fillna(df_enc[col].median())
    for col in df_enc.select_dtypes(include=['object', 'category']).columns:
        le = LabelEncoder()
        df_enc[col] = le.fit_transform(df_enc[col].astype(str))
    return df_enc

# Real baseline (TRTR)
real_enc = encode_dataframe(real_data)
X_real = real_enc.drop(columns=[TARGET])
y_real = real_enc[TARGET]
X_train, X_test, y_train, y_test = train_test_split(
    X_real, y_real, test_size=0.2, random_state=RANDOM_SEED
)

clf_real = RandomForestClassifier(n_estimators=100, random_state=RANDOM_SEED, n_jobs=-1)
clf_real.fit(X_train, y_train)
baseline_acc = accuracy_score(y_test, clf_real.predict(X_test))
baseline_f1 = f1_score(y_test, clf_real.predict(X_test), average='weighted')

tstr_results = {
    'target_column': TARGET,
    'test_size': len(X_test),
    'random_seed': RANDOM_SEED,
    'baseline_trtr': {'accuracy': round(baseline_acc, 4), 'f1': round(baseline_f1, 4)},
    'models': {}
}
print(f"Baseline TRTR: acc={baseline_acc:.4f}, f1={baseline_f1:.4f}")

# TSTR for each synthetic dataset
for synth_file in sorted(glob.glob(os.path.join(OUTPUT_DIR, '*.csv'))):
    name = os.path.basename(synth_file).replace('.csv', '')
    try:
        synth_df = pd.read_csv(synth_file)
        if set(synth_df.columns) != set(real_data.columns):
            tstr_results['models'][name] = {'status': 'error', 'error': 'Column mismatch'}
            continue

        synth_enc = encode_dataframe(synth_df)
        X_synth = synth_enc.drop(columns=[TARGET])
        y_synth = synth_enc[TARGET]

        clf = RandomForestClassifier(n_estimators=100, random_state=RANDOM_SEED, n_jobs=-1)
        clf.fit(X_synth, y_synth)
        acc = accuracy_score(y_test, clf.predict(X_test))
        f1 = f1_score(y_test, clf.predict(X_test), average='weighted')

        tstr_results['models'][name] = {'accuracy': round(acc, 4), 'f1': round(f1, 4)}
        print(f"{name}: acc={acc:.4f}, f1={f1:.4f}")
    except Exception as e:
        tstr_results['models'][name] = {'status': 'error', 'error': str(e)}
        print(f"{name}: ERROR - {e}")

with open(os.path.join(OUTPUT_DIR, 'tstr_results.json'), 'w') as f:
    json.dump(tstr_results, f, indent=2)

print("TSTR Phase1 complete.")
```

**実行**:
```bash
cd /home/hatano/works/syntheticdata-catalog/libs/evaluation
uv run python tstr_phase1.py
```

---

## 評価 2-7: プライバシー評価

**実行環境**: `libs/evaluation/`

### libs/evaluation/privacy_phase1.py

```python
"""Phase 1 プライバシー評価: DCR, Exact Match, Nearest Neighbor"""
import pandas as pd
import numpy as np
import json
import glob
import os
from sklearn.preprocessing import LabelEncoder
from sklearn.neighbors import NearestNeighbors

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..', '..')
REAL_DATA_PATH = os.path.join(ROOT, 'data/processed/d1_adult.csv')
OUTPUT_DIR = os.path.join(ROOT, 'results/phase1')

real_data = pd.read_csv(REAL_DATA_PATH)

def encode_for_distance(df):
    """距離計算用にエンコード"""
    df_enc = df.copy()
    for col in df_enc.select_dtypes(include=['object', 'category']).columns:
        df_enc[col] = df_enc[col].fillna('_MISSING_')
        le = LabelEncoder()
        df_enc[col] = le.fit_transform(df_enc[col].astype(str))
    for col in df_enc.select_dtypes(include=['number']).columns:
        df_enc[col] = df_enc[col].fillna(df_enc[col].median())
    # 正規化
    for col in df_enc.columns:
        col_range = df_enc[col].max() - df_enc[col].min()
        if col_range > 0:
            df_enc[col] = (df_enc[col] - df_enc[col].min()) / col_range
    return df_enc

def compute_privacy_metrics(real_df, synth_df):
    """プライバシーメトリクスの計算"""
    # 共通カラムのみ使用
    common_cols = sorted(set(real_df.columns) & set(synth_df.columns))
    real_sub = real_df[common_cols]
    synth_sub = synth_df[common_cols]

    real_enc = encode_for_distance(real_sub)
    synth_enc = encode_for_distance(synth_sub)

    # サンプリング（計算コスト削減）
    max_rows = 5000
    if len(real_enc) > max_rows:
        real_sample = real_enc.sample(max_rows, random_state=42)
    else:
        real_sample = real_enc
    if len(synth_enc) > max_rows:
        synth_sample = synth_enc.sample(max_rows, random_state=42)
    else:
        synth_sample = synth_enc

    # 1. DCR (Distance to Closest Record)
    nn = NearestNeighbors(n_neighbors=1, metric='euclidean', n_jobs=-1)
    nn.fit(real_sample.values)
    distances, _ = nn.kneighbors(synth_sample.values)
    dcr = distances.flatten()

    # 2. Exact Match Rate
    real_tuples = set(map(tuple, real_sub.fillna('_NA_').values))
    synth_tuples = list(map(tuple, synth_sub.fillna('_NA_').values))
    exact_matches = sum(1 for t in synth_tuples if t in real_tuples)
    exact_match_rate = exact_matches / len(synth_tuples)

    # 3. 5th percentile DCR (低いほど危険)
    dcr_5th = float(np.percentile(dcr, 5))

    return {
        'dcr_mean': round(float(np.mean(dcr)), 6),
        'dcr_median': round(float(np.median(dcr)), 6),
        'dcr_5th_percentile': round(dcr_5th, 6),
        'dcr_min': round(float(np.min(dcr)), 6),
        'exact_match_rate': round(exact_match_rate, 6),
        'exact_match_count': exact_matches,
        'sample_size_real': len(real_sample),
        'sample_size_synth': len(synth_sample),
    }

privacy_results = {}

for synth_file in sorted(glob.glob(os.path.join(OUTPUT_DIR, '*.csv'))):
    name = os.path.basename(synth_file).replace('.csv', '')
    print(f"Privacy eval: {name}")
    try:
        synth_df = pd.read_csv(synth_file)
        if set(synth_df.columns) != set(real_data.columns):
            privacy_results[name] = {'status': 'error', 'error': 'Column mismatch'}
            continue

        metrics = compute_privacy_metrics(real_data, synth_df)
        privacy_results[name] = metrics
        print(f"  DCR mean={metrics['dcr_mean']:.4f}, exact_match={metrics['exact_match_rate']:.4f}")
    except Exception as e:
        privacy_results[name] = {'status': 'error', 'error': str(e)}
        print(f"  ERROR: {e}")

with open(os.path.join(OUTPUT_DIR, 'privacy_eval.json'), 'w') as f:
    json.dump(privacy_results, f, indent=2)

print(f"\nPrivacy evaluation complete. {len(privacy_results)} models evaluated.")
```

**実行**:
```bash
cd /home/hatano/works/syntheticdata-catalog/libs/evaluation
uv run python privacy_phase1.py
```

---

## 実行順序まとめ

```bash
cd /home/hatano/works/syntheticdata-catalog

# Step 1: 合成データ生成（並列実行可能）
(cd libs/sdv && uv run python run_phase1.py) &
(cd libs/synthcity && uv run python run_phase1.py) &
(cd libs/ydata && uv run python run_phase1.py) &
# mostlyai は API キー設定時のみ
# (cd libs/mostlyai && MOSTLY_AI_API_KEY=xxx uv run python run_phase1.py) &
wait

# Step 2: 評価（全合成データ生成後に実行）
cd libs/evaluation
uv run python sdmetrics_phase1.py
uv run python tstr_phase1.py
uv run python privacy_phase1.py
```

## 完了条件

- [ ] 各ライブラリの合成データ CSV が `results/phase1/` に存在（エラーは run_log に記録）
- [ ] 各ライブラリの `*_run_log.json` が存在し、`_env` にバージョン情報を含む
- [ ] `results/phase1/sdmetrics_eval.json` が存在（全合成データの統一評価）
- [ ] `results/phase1/tstr_results.json` が存在
- [ ] `results/phase1/privacy_eval.json` が存在

## 権限・エラー対策

| 問題 | 対応 |
|------|------|
| 各ライブラリは独立 venv | 依存競合なし。1つのエラーが他に波及しない |
| メモリ不足 | epochs を 50 に削減。またはデータを先頭 10000 行にサンプリング |
| MOSTLY AI | API キー未設定なら自動スキップ |
| SynthCity モデル未対応 | `Plugins().list()` で事前確認、未対応モデルはスキップ |
| TSTR カラム不一致 | スキップしてエラー記録 |
| プライバシー評価の計算コスト | 5000行にサンプリングして実行 |
| タイムアウト | 各モデル1時間超なら epochs 削減 |
