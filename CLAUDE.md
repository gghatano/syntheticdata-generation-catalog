# syntheticdata-generation-catalog

## プロジェクト概要

PythonベースのOSSライブラリを対象に、表形式データの合成データ生成手法を調査・比較するプロジェクト。
検証結果は GitHub Pages で公開予定。

## リポジトリ構成

```
libs/                    # ライブラリごとの独立した uv 環境
  sdv/                   # L-01: SDV（単一表・複数表・時系列）
  synthcity/             # L-02: SynthCity（単一表・時系列）
  mostlyai/              # L-03: MOSTLY AI SDK（API キー必要）
  ydata/                 # L-04: ydata-synthetic（単一表・時系列）
  evaluation/            # 評価専用（SDMetrics, scikit-learn）
data/
  raw/                   # ダウンロードした元データ
  processed/             # 前処理済みデータ（全ライブラリ共通入力）
results/
  phase1/                # 単一表実験の結果
  phase2/                # 複数表実験の結果
  phase3/                # 時系列実験の結果
  evaluation/            # 統合結果（all_results.json）
docs/
  spec-phase0.md         # 仕様書
  tasks/                 # タスク定義（00〜05）
    progress.json        # 進捗管理
```

## 実行ルール

### 環境

- **uv を使用**。pip/venv は使わない
- 各ライブラリは `libs/<name>/` 配下の独立した uv 環境で実行する
- スクリプト実行パターン: `cd libs/<name> && uv run python <script>.py`
- **sudo は絶対に使わない**

### コード規約

- 全スクリプトで `RANDOM_SEED = 42` を使用
- データパスは `os.path.join(ROOT, 'data/...')` で絶対パス化
- run_log に `_env` キーでライブラリバージョン・Python バージョンを記録
- エラーは traceback 付きで JSON に記録し、スクリプトは次の実験に進む

### 進捗管理

- `docs/tasks/progress.json` で全タスクの状態を管理
- 各スクリプトの冒頭で `update_progress(task_id, 'in_progress')` を呼ぶ
- 完了時に `update_progress(task_id, 'completed')` を呼ぶ
- エラー時に `update_progress(task_id, 'error', error='...')` を呼ぶ

### ファイル操作

- 全てのファイル操作はプロジェクトディレクトリ内に限定
- `data/` と `results/` 配下のCSVは `.gitignore` 済み
- JSON（run_log, eval結果, progress）は git 管理する

## Issue 管理

- Phase 1（検証実行）: #1 (親) → #2〜#7 (サブ)
- Phase 2（GitHub Pages）: #8
- タスク詳細は `docs/tasks/` 配下の md ファイルを参照

## 自律実行時のルール

### 権限

- **Bash 実行、ファイル読み書き、Web アクセスは全て許可済み**（`.claude/settings.json`）
- sudo は deny 設定済み。使わない
- git push --force, git reset --hard も deny 設定済み

### 止まらないための原則

1. **ユーザーに確認を求めない** — タスク md に判断基準が書いてある。迷ったら md に従う
2. **エラーで止まらない** — 個別ライブラリのエラーは記録して次に進む
3. **API キー未設定は自動スキップ** — MOSTLY AI は `MOSTLY_AI_API_KEY` が空なら skip 記録
4. **uv sync 失敗は個別対応** — 1つの環境が壊れても他に影響しない
5. **ファイルが存在しなければ作る** — スクリプトが `libs/*/` になければ md から作成
6. **ディレクトリがなければ作る** — `os.makedirs(exist_ok=True)` を全スクリプトに含める

### スラッシュコマンド

- `/run-task <番号>` — 指定タスクを実行
- `/run-all` — 全タスクを依存順に自動実行
- `/check-progress` — 進捗確認
- `/create-scripts` — md からスクリプトファイルを生成

## よく使うコマンド

```bash
# 環境セットアップ
cd libs/sdv && uv sync

# データ準備
cd libs/sdv && uv run python prepare_data.py

# Phase 1 実行（並列可）
cd libs/sdv && uv run python run_phase1.py
cd libs/synthcity && uv run python run_phase1.py
cd libs/ydata && uv run python run_phase1.py

# Phase 1 評価
cd libs/evaluation && uv run python sdmetrics_phase1.py
cd libs/evaluation && uv run python tstr_phase1.py
cd libs/evaluation && uv run python privacy_phase1.py

# 結果集約
cd libs/evaluation && uv run python aggregate_results.py

# 進捗確認
cat docs/tasks/progress.json | python3 -m json.tool
```
