# 全検証タスクの順次実行

Phase 1 の全検証タスク（00〜05）を依存順に自動実行する。

## 実行手順

1. `docs/tasks/progress.json` を確認し、未完了タスクを特定
2. 依存順（00 → 01 → 02/03/04 → 05）でタスクを実行
3. 02/03/04 は独立しているため、1つずつ順に実行する（並列はしない — 安定性優先）
4. 各タスクの完了後に `progress.json` を更新
5. エラーが発生したタスクは記録して次のタスクに進む
6. 全タスク完了後、サマリを表示

## 各タスクの実行方法

### 00: 環境構築
- `docs/tasks/00-setup.md` に従い、.gitignore・ディレクトリ・pyproject.toml を作成
- `libs/*/` で `uv sync` を実行

### 01: データ準備
- `libs/sdv/prepare_data.py` を作成して実行
- スクリプトがなければ `docs/tasks/01-data-preparation.md` の内容から作成

### 02: 単一表実験
- `libs/sdv/run_phase1.py` → `libs/synthcity/run_phase1.py` → `libs/ydata/run_phase1.py` の順に実行
- 各スクリプトがなければ `docs/tasks/02-phase1-single-table.md` から作成
- 全合成データ生成後、`libs/evaluation/` で評価スクリプト3本を実行

### 03: 複数表実験
- `libs/sdv/run_phase2.py` を実行
- `libs/evaluation/eval_phase2.py` を実行

### 04: 時系列実験
- `libs/sdv/run_phase3.py` → `libs/synthcity/run_phase3.py` → `libs/ydata/run_phase3.py` の順に実行
- `libs/evaluation/eval_phase3.py` を実行

### 05: 統合評価
- `libs/evaluation/aggregate_results.py` を実行

## 重要ルール

- 各ライブラリは `libs/<name>/` 配下で `uv run python <script>.py` で実行
- sudo は絶対に使わない
- MOSTLY AI は API キー（`MOSTLY_AI_API_KEY`）未設定なら自動スキップ
- 個別ライブラリのエラーではタスク全体を止めない（記録して次へ）
- `uv sync` のエラーでも、他の環境に影響しないので続行
- 完了タスクは再実行しない（progress.json の status が completed のもの）
