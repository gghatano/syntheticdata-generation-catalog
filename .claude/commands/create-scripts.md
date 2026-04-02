# スクリプトファイルの作成

`docs/tasks/` の md ファイルに記載されたスクリプトを、実際の Python ファイルとして `libs/*/` に作成する。

## 実行手順

1. `docs/tasks/02-phase1-single-table.md` 等のタスク定義を読む
2. 記載されたスクリプトコードを抽出
3. 対応する `libs/<name>/run_phase*.py` や `libs/evaluation/*.py` として書き出す
4. 共通ヘルパー（update_progress, get_env_info）を各スクリプトに含める

## 対象スクリプト一覧

### データ準備
- `libs/sdv/prepare_data.py`

### Phase 1
- `libs/sdv/run_phase1.py`
- `libs/synthcity/run_phase1.py`
- `libs/mostlyai/run_phase1.py`
- `libs/ydata/run_phase1.py`
- `libs/evaluation/sdmetrics_phase1.py`
- `libs/evaluation/tstr_phase1.py`
- `libs/evaluation/privacy_phase1.py`

### Phase 2
- `libs/sdv/run_phase2.py`
- `libs/mostlyai/run_phase2.py`
- `libs/evaluation/eval_phase2.py`

### Phase 3
- `libs/sdv/run_phase3.py`
- `libs/synthcity/run_phase3.py`
- `libs/mostlyai/run_phase3.py`
- `libs/ydata/run_phase3.py`
- `libs/evaluation/eval_phase3.py`

### 統合評価
- `libs/evaluation/aggregate_results.py`

$ARGUMENTS
