# 05: 統合評価・結果JSON生成

## 目的

Phase 1〜3 の実験結果を統合し、ライブラリ横断で比較可能な統一 JSON を生成する。
**可視化・レポート作成は後続フェーズで実施する。ここでは生データの整理と統一フォーマットへの変換に集中する。**

## 前提条件

- Phase 1〜3 のうち、少なくとも1つが完了済み
- `libs/evaluation/` で `uv sync` 済み

## 結果の保管構造

```
results/
├── phase1/
│   ├── sdv_gaussiancopula.csv        # 合成データ（生データ）
│   ├── sdv_ctgan.csv
│   ├── synthcity_ctgan.csv
│   ├── ydata_ctgan.csv
│   ├── sdv_run_log.json              # 実行ログ（バージョン・時間・エラー）
│   ├── synthcity_run_log.json
│   ├── ydata_run_log.json
│   ├── sdmetrics_eval.json           # SDMetrics 統一評価
│   ├── tstr_results.json             # TSTR 下流タスク評価
│   └── privacy_eval.json             # プライバシー評価
├── phase2/
│   ├── sdv_hma_*.csv
│   ├── sdv_run_log.json
│   └── eval_results.json
├── phase3/
│   ├── sdv_par.csv
│   ├── *_run_log.json
│   └── eval_results.json
└── evaluation/
    ├── all_results.json              # 全実験の統合結果
    └── summary.json                  # サマリ
```

## 統一結果スキーマ

各実験は以下のスキーマで `results/evaluation/all_results.json` に集約する。

```json
{
  "experiment_id": "phase1_sdv_gaussiancopula",
  "library_id": "L-01",
  "library_name": "SDV",
  "model_name": "GaussianCopula",
  "phase": "phase1",
  "data_type": "single_table",
  "dataset_id": "D1",
  "run_info": {
    "status": "completed",
    "time_sec": 45.2,
    "rows_generated": 32561,
    "timestamp": "2026-04-02T15:30:00",
    "library_version": "1.x.x",
    "python_version": "3.10.x",
    "error": null
  },
  "metrics": {
    "utility": {
      "sdmetrics_quality_score": 0.91,
      "sdmetrics_diagnostic_score": 0.95,
      "tstr_accuracy": 0.84,
      "tstr_f1": 0.82
    },
    "privacy": {
      "dcr_mean": 0.72,
      "dcr_5th_percentile": 0.15,
      "exact_match_rate": 0.03
    },
    "constraints": {
      "fk_integrity": null
    }
  },
  "raw_output_path": "results/phase1/sdv_gaussiancopula.csv"
}
```

## 手順

### libs/evaluation/aggregate_results.py

```python
"""全 Phase の実験結果を統合 JSON に集約する。

完了した Phase のみ集約する（全 Phase 完了を待たない）。
実行: cd libs/evaluation && uv run python aggregate_results.py
"""
import json
import os
import glob
import platform
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..', '..')
EVAL_DIR = os.path.join(ROOT, 'results/evaluation')
PROGRESS_FILE = os.path.join(ROOT, 'docs/tasks/progress.json')
os.makedirs(EVAL_DIR, exist_ok=True)

LIB_MAP = {
    'sdv': ('L-01', 'SDV'),
    'synthcity': ('L-02', 'SynthCity'),
    'mostlyai': ('L-03', 'MOSTLY AI'),
    'ydata': ('L-04', 'ydata-synthetic'),
}

def load_json_safe(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        print(f"WARNING: Failed to load {path}: {e}")
        return {}

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

all_results = []

def extract_lib_info(model_key):
    """モデルキーからライブラリ情報を取得"""
    for prefix, (lib_id, lib_name) in LIB_MAP.items():
        if model_key.startswith(prefix):
            model_name = model_key[len(prefix)+1:] if len(model_key) > len(prefix) else model_key
            return lib_id, lib_name, model_name
    return 'unknown', model_key.split('_')[0], model_key

def collect_phase(phase_name, data_type, dataset_id):
    """各 Phase のデータ収集"""
    phase_dir = os.path.join(ROOT, 'results', phase_name)
    if not os.path.isdir(phase_dir):
        print(f"SKIP: {phase_dir} not found")
        return

    # run_log の収集
    for log_file in sorted(glob.glob(os.path.join(phase_dir, '*_run_log.json'))):
        run_log = load_json_safe(log_file)
        env_info = run_log.pop('_env', {})

        for model_key, info in run_log.items():
            if model_key.startswith('_'):
                continue
            lib_id, lib_name, model_name = extract_lib_info(model_key)

            entry = {
                'experiment_id': f'{phase_name}_{model_key}',
                'library_id': lib_id,
                'library_name': lib_name,
                'model_name': model_name,
                'phase': phase_name,
                'data_type': data_type,
                'dataset_id': dataset_id,
                'run_info': {
                    'status': info.get('status', 'unknown'),
                    'time_sec': info.get('time_sec'),
                    'rows_generated': info.get('rows') or info.get('tables'),
                    'library_version': env_info.get(f'{model_key.split("_")[0]}_version',
                                                    env_info.get('sdv_version', 'unknown')),
                    'python_version': env_info.get('python_version', 'unknown'),
                    'timestamp': env_info.get('timestamp', ''),
                    'error': info.get('error'),
                },
                'metrics': {'utility': {}, 'privacy': {}, 'constraints': {}},
                'raw_output_path': f'results/{phase_name}/{model_key}.csv',
            }
            all_results.append(entry)

    return phase_dir

# Phase 1
phase1_dir = collect_phase('phase1', 'single_table', 'D1')
if phase1_dir:
    # SDMetrics
    sdmetrics = load_json_safe(os.path.join(phase1_dir, 'sdmetrics_eval.json'))
    for entry in all_results:
        if entry['phase'] != 'phase1':
            continue
        key = entry['experiment_id'].replace('phase1_', '')
        if key in sdmetrics and 'status' not in sdmetrics[key]:
            entry['metrics']['utility']['sdmetrics_quality_score'] = sdmetrics[key].get('quality_score')
            entry['metrics']['utility']['sdmetrics_diagnostic_score'] = sdmetrics[key].get('diagnostic_score')

    # TSTR
    tstr = load_json_safe(os.path.join(phase1_dir, 'tstr_results.json'))
    for entry in all_results:
        if entry['phase'] != 'phase1':
            continue
        key = entry['experiment_id'].replace('phase1_', '')
        if key in tstr.get('models', {}):
            m = tstr['models'][key]
            if 'status' not in m:
                entry['metrics']['utility']['tstr_accuracy'] = m.get('accuracy')
                entry['metrics']['utility']['tstr_f1'] = m.get('f1')

    # Privacy
    privacy = load_json_safe(os.path.join(phase1_dir, 'privacy_eval.json'))
    for entry in all_results:
        if entry['phase'] != 'phase1':
            continue
        key = entry['experiment_id'].replace('phase1_', '')
        if key in privacy and 'status' not in privacy[key]:
            entry['metrics']['privacy'] = privacy[key]

# Phase 2
collect_phase('phase2', 'multi_table', 'D2')

# Phase 3
collect_phase('phase3', 'timeseries', 'D3')

# 保存
with open(os.path.join(EVAL_DIR, 'all_results.json'), 'w') as f:
    json.dump(all_results, f, indent=2, default=str)

# サマリ
status_counts = {}
for r in all_results:
    s = r['run_info']['status']
    status_counts[s] = status_counts.get(s, 0) + 1

phase_counts = {}
for r in all_results:
    p = r['phase']
    if p not in phase_counts:
        phase_counts[p] = {}
    s = r['run_info']['status']
    phase_counts[p][s] = phase_counts[p].get(s, 0) + 1

summary = {
    'total_experiments': len(all_results),
    'status_counts': status_counts,
    'by_phase': phase_counts,
    'generated_at': datetime.now().isoformat(),
}

with open(os.path.join(EVAL_DIR, 'summary.json'), 'w') as f:
    json.dump(summary, f, indent=2)

update_progress('05-evaluation', 'completed')

print(json.dumps(summary, indent=2))
print(f"\nSaved: {EVAL_DIR}/all_results.json ({len(all_results)} entries)")
```

**実行**:
```bash
cd /home/hatano/works/syntheticdata-catalog/libs/evaluation
uv run python aggregate_results.py
```

## 完了条件

- [ ] `results/evaluation/all_results.json` が存在し、完了した実験のエントリを含む
- [ ] `results/evaluation/summary.json` が存在
- [ ] 各エントリの `run_info` にライブラリバージョン・Python バージョンが記録されている
- [ ] Phase 1 のエントリには `metrics.utility`（SDMetrics, TSTR）と `metrics.privacy`（DCR, exact match）が含まれる

## 権限・エラー対策

| 問題 | 対応 |
|------|------|
| 部分実行 | 完了した Phase の結果のみ集約。全 Phase 完了を待たない |
| ファイル不在 | `load_json_safe` で個別の読み込み失敗を吸収 |
| スキーマ不整合 | `_env` キーを除外し、ライブラリごとの run_log 差異を吸収 |
| 再実行 | 冪等。実行のたびに `all_results.json` を再生成 |
