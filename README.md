# syntheticdata-generation-catalog

Python 製 OSS ライブラリを対象に、**表形式データの合成データ生成手法**を調査・比較するプロジェクト。
単一表 / 複数表（リレーション付き）/ 時系列の 3 種類のデータ構造について、有用性・安全性・実装の扱いやすさを実験ベースで評価する。

検証結果はカタログサイトとして公開している:
**https://gghatano.github.io/syntheticdata-generation-catalog/**

## 何を比較しているか

### 対象ライブラリ

| ID   | ライブラリ                | 単一表 | 複数表 | 時系列 | 備考                           |
| ---- | ------------------------ | :----: | :----: | :----: | ------------------------------ |
| L-01 | [SDV](https://sdv.dev/)                  |   ○    |   ○    |   ○    | 基盤ライブラリ。GaussianCopula / CTGAN / TVAE / HMA / PAR を網羅 |
| L-02 | [SynthCity](https://github.com/vanderschaarlab/synthcity)            |   ○    |   △    |   ○    | 研究比較・評価指標が豊富 (ADS-GAN, Normalizing Flow など) |
| L-03 | [MOSTLY AI SDK](https://mostly.ai/) |   ○    |   ○    |   ○    | 実務志向。API キー必要 |
| L-04 | [ydata-synthetic](https://github.com/ydataai/ydata-synthetic)      |   ○    |   ×    |   ○    | 時系列比較用 |
| L-05 | [RealTabFormer](https://github.com/worldbank/REaLTabFormer)        |   ○    |   ○    |   ×    | Transformer ベース複数表合成 |

### 評価軸

- **統計的類似度** — SDMetrics（Column Shapes / Column Pair Trends）
- **機械学習有用性** — TSTR（Train on Synthetic, Test on Real）
- **プライバシー** — 最近傍距離・再識別リスク
- **実装の成熟度** — 学習時間・依存関係・ドキュメント量

### 実験データセット

UCI Adult / Insurance / Companies / Hotel Reservation / IMDB / Olist EC / 株価時系列 / IoT センサー の 8 ケース。詳細はカタログサイトの「実験事例」を参照。

## リポジトリ構成

```
libs/                  各ライブラリの uv 環境（独立）
  common/              実験管理ヘルパー（experiment.py）
  sdv/                 SDV 実験スクリプト（phase1/2/3）
  synthcity/           SynthCity 実験スクリプト
  mostlyai/            MOSTLY AI SDK 実験スクリプト
  ydata/               ydata-synthetic 実験スクリプト
  realtabformer/       RealTabFormer 実験スクリプト
  evaluation/          評価専用環境（SDMetrics / scikit-learn）
data/
  raw/                 ダウンロード元データ（gitignore）
  processed/           前処理済みデータ（gitignore）
results/
  phase1/              単一表実験の結果
  phase2/              複数表実験の結果
  phase3/              時系列実験の結果
  evaluation/          統合結果（all_results.json, summary.json）
  metadata/            実験メタデータ（git 管理）
docs/
  spec-phase0.md       仕様書
  tasks/               タスク定義 + progress.json
  catalog/             カタログサイト（React + Vite + TS）
```

## クイックスタート

### 前提

- [uv](https://docs.astral.sh/uv/) がインストール済み（pip / venv は使用しない）
- Python 3.10 以上

### 1 つのライブラリで実験を回す例（SDV）

```bash
# 環境セットアップ
cd libs/sdv && uv sync

# データ準備（data/processed/ に共通入力を配置）
uv run python prepare_data.py

# Phase 1（単一表）実行 → results/phase1/sdv_*.csv が出力される
uv run python run_phase1.py
```

他のライブラリも同じパターンで `cd libs/<name> && uv run python run_phase<N>.py`。

### 評価とまとめ

```bash
cd libs/evaluation && uv sync

# 全ライブラリの CSV を走査して評価指標を再計算
uv run python sdmetrics_phase1.py
uv run python tstr_phase1.py
uv run python privacy_phase1.py

# 全 Phase の結果を統合
uv run python aggregate_results.py
```

### 進捗確認

```bash
cat docs/tasks/progress.json | python3 -m json.tool
```

## カタログサイト（GitHub Pages）

```bash
cd docs/catalog
npm install
npm run dev          # ローカル開発サーバー
npm test -- --run    # Unit テスト
npm run test:e2e     # E2E テスト（初回は npx playwright install --with-deps chromium）
```

`main` への push で `.github/workflows/deploy-pages.yml` が走り、自動デプロイされる。

## ブランチ戦略

```
main          安定版（develop からのマージのみ）
  └ develop   統合・動作確認用
      └ feature/issue-<番号>-<概要>   個別タスクの作業ブランチ
```

`main` への直接 push は禁止。feature → develop → main の順で PR を作成する。

## 実験結果の不変性

合成データ CSV は **append-only**（同一条件の再実行を除き上書き禁止）。
パラメータやデータセットを変えた追加実験は新しいファイル名で保存する:

```
results/<phase>/<library>_<model>_<条件サフィックス>.csv
例: sdv_ctgan_100ep.csv, sdv_ctgan_10ep_census.csv
```

詳細なルールは [CLAUDE.md](./CLAUDE.md#実験結果の命名規則と不変性) を参照。

## ドキュメント

- [`CLAUDE.md`](./CLAUDE.md) — プロジェクト規約・コーディングルール・自律実行時の判断基準
- [`docs/spec-phase0.md`](./docs/spec-phase0.md) — 仕様書（対象・スコープ・データ・評価軸）
- [`docs/tasks/`](./docs/tasks/) — タスク定義（00 setup → 05 evaluation）
- [`docs/evaluation-knowledge.md`](./docs/evaluation-knowledge.md) — 評価指標の解釈ガイド
- [`docs/catalog/README.md`](./docs/catalog/README.md) — カタログサイトの開発・SPA ルーティングの制約
