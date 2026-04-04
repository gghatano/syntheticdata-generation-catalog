# syntheticdata-generation-catalog

## プロジェクト概要

PythonベースのOSSライブラリを対象に、表形式データの合成データ生成手法を調査・比較するプロジェクト。
検証結果は GitHub Pages で公開予定。

## リポジトリ構成

```
libs/                    # ライブラリごとの独立した uv 環境
  common/                # 共通ヘルパー（experiment.py: メタデータ管理）
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
  metadata/              # 実験メタデータ（.meta.json, manifest.json）← git管理
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

### 実験管理基盤

- `libs/common/experiment.py` に共通ヘルパーを集約（標準ライブラリのみ依存）
- 各スクリプトから `sys.path.insert(0, os.path.join(ROOT, 'libs'))` で import
- 主要API:
  - `ExperimentRun` — context manager で1実験を追跡（タイミング・エラーキャプチャ・メタデータ生成）
  - `build_run_log(runs, env)` — 既存 run_log 互換の辞書を生成
  - `update_manifest(meta_root)` — `results/metadata/manifest.json` を再生成
  - `update_progress(progress_file, task_id, status)` — 進捗更新（全スクリプト共通）
  - `file_sha256(path)` — ファイルのSHA-256計算
- メタデータは `results/metadata/<phase>/<experiment_id>.meta.json` に保存（git管理）
- experiment_id 命名: `<phase>_<library>_<model>[_<suffix>]`（例: `phase1_sdv_ctgan`）

### ファイル操作

- 全てのファイル操作はプロジェクトディレクトリ内に限定
- `data/` と `results/` 配下のCSVは `.gitignore` 済み
- JSON（run_log, eval結果, progress）は git 管理する

### 実験結果の命名規則と不変性

**原則: 実験結果は上書きしない（append-only）。**

データ・アルゴリズム・パラメータの組み合わせごとに一意なファイル名を付与する。
条件を変えた追加実験は新しいファイルとして保存し、既存結果を破壊しない。

#### 合成データ CSV の命名規則

```
results/<phase>/<library>_<model>_<条件サフィックス>.csv
```

- `<library>`: `sdv`, `synthcity`, `ydata`, `mostlyai`
- `<model>`: `gaussiancopula`, `ctgan`, `bayesian_network`, `tvae`, `hma`, `par` 等
- `<条件サフィックス>`: パラメータや条件を識別する文字列。省略可（デフォルト条件の場合）

**条件サフィックスの例:**
- epochs 変更: `sdv_ctgan_100ep.csv`, `sdv_ctgan_10ep.csv`
- データセット変更: `sdv_ctgan_100ep_census.csv`
- サンプルサイズ変更: `sdv_ctgan_100ep_10k.csv`
- 複数条件: アンダースコアで連結 `sdv_ctgan_100ep_10k_seed123.csv`

#### run_log の命名規則

```
results/<phase>/<library>_run_log_<条件サフィックス>.json
```

条件サフィックスが空の場合は `<library>_run_log.json`。
run_log には必ず以下を含める:
- `epochs` や `batch_size` 等の主要ハイパーパラメータ
- `dataset`: 使用したデータセット名
- `_env`: ライブラリバージョン・Python バージョン・タイムスタンプ

#### 評価結果 JSON の命名規則

```
results/<phase>/sdmetrics_eval.json      # 全モデル横断（再生成OK）
results/<phase>/tstr_results.json        # 全モデル横断（再生成OK）
results/<phase>/privacy_eval.json        # 全モデル横断（再生成OK）
```

評価JSONは全モデルの結果をまとめたもので、合成データCSVが増えたら再生成する。
キーはCSVファイル名（拡張子なし）と一致させる。

#### 統合結果

```
results/evaluation/all_results.json      # 全Phase統合（再生成OK）
results/evaluation/summary.json          # サマリ（再生成OK）
```

#### ルールまとめ

1. **合成データ CSV は上書き禁止** — 条件が異なるなら別ファイル名にする
2. **同一条件の再実行は上書きOK** — 同じパラメータでの再実行は同名ファイルに出力してよい
3. **評価 JSON は再生成OK** — results 配下の CSV を走査して毎回再生成する設計
4. **run_log にパラメータを記録** — どの条件で生成したか後から追跡可能にする
5. **ファイル名から条件が読み取れること** — ファイル名だけで実験条件が分かるようにする

## ブランチ戦略

```
main          ← 安定版。develop からのマージのみ
  └→ develop  ← 統合・動作確認用。feature ブランチをここにマージ
       └→ feature/*  ← 個別タスクの作業ブランチ
```

- **feature ブランチは develop から作成**する
- **feature → develop** に PR を作成してマージ
- **develop で動作確認**後、**develop → main** にマージ
- main への直接 push は禁止
- feature ブランチ名: `feature/issue-<番号>-<概要>` (例: `feature/issue-8-catalog`)

## カタログサイト（GitHub Pages）

- 技術スタック: React + Vite + TypeScript + Tailwind CSS
- ソース: `docs/catalog/`
- 事例データ: `docs/catalog/public/data/experiment-cases.json`
- アルゴリズムデータ: `docs/catalog/public/data/algorithms.json`
- デプロイ: GitHub Actions (`.github/workflows/deploy-pages.yml`)
- 開発: `cd docs/catalog && npm run dev`

## Issue 管理

- Phase 1（検証実行）: #1 (親) → #2〜#7 — **完了・クローズ済み**
- Phase 2（GitHub Pages）: #8 → #10〜#13 — **完了・クローズ済み**
- 現在のオープン Issue:
  - UI強化: #18(横並び比較), #19(CSV/MDエクスポート), #22(棒グラフ), #26(グラフ可視化)
  - 品質評価: #27(保険), #28(IMDB), #29(企業), #30(ホテル), #31(株価), #32(IoT)
  - データ管理: #33(データ元URL), #34(実験管理基盤)
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

#### Issue 対応ワークフロー
- `/1_issue_plan <issue番号>` — Issue を読み、コード調査→実装計画を策定→Issue にコメント
- `/2_issue_impl <issue番号>` — 確定した計画に基づき worktree で実装→コミット→PR 作成
- `/3_issue_review <issue番号>` — PR をレビューエージェントで検査→P0/P1 指摘を修正→結果を PR にコメント

#### 検証タスク実行
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
