# 新規アルゴリズム登録

合成データ生成アルゴリズム（ライブラリ）をカタログに登録する。
ライブラリ環境のスキャフォールディングと `algorithms.json` への新規エントリ追加を行う。
**実験結果のメトリクスは扱わない**（それは `/add-experiment-case` の責務）。

## 使い方

`/add-algorithm <algorithm_id>` — 例: `/add-algorithm realtabformer`

引数なしの場合はインタラクティブに ID を尋ねる。

## 実行手順

### 1. 入力収集

以下を順に確認する。CLAUDE.md と既存 `algorithms.json` の値域を参照しながら聞き、不明な点だけ質問する。

| 項目 | 用途 | 値の例 |
|---|---|---|
| `id` | スラッグ（小文字 + ハイフン or アンダースコア） | `realtabformer` |
| `name` | UI 表示名 | `REaLTabFormer` |
| `libraries` | 提供ライブラリ配列 | `["realtabformer"]` / `["SDV"]` |
| `category` | `gan` / `copula` / `vae` / `bayesian` / `transformer` / `sequential` / `diffusion` / `flow` | `transformer` |
| `supported_data` | `single_table` / `multi_table` / `timeseries` の配列 | `["single_table","multi_table"]` |
| `tags` | 3〜4 個のキーワード | `["Transformer","親子テーブル"]` |
| `use_cases` | 想定ユースケース 2〜4 件 | `["親子テーブル合成"]` |
| `input_requirements` | 入力要件 | `["GPU推奨"]` |
| `privacy_mechanism` | `none` / `dp` / `pate` / 個別記述 | `none` |
| `privacy_risk_level` | `low` / `medium` / `high` / `null` | `medium` |
| `description` | 3〜4 文の説明 | (本文) |
| `strengths` | 3〜4 件 | (本文) |
| `weaknesses` | 2〜3 件 | (本文) |
| `reference` | 主要論文 / docs URL | `https://...` |
| `pypi_or_git` | PyPI 名 or `git+https://...` | `realtabformer` |
| `python_constraint` | `requires-python` 値 | `>=3.10,<3.12` |
| `extra_dependencies` | pin が必要な依存 | `["transformers>=4.46,<5"]` |

### 2. 重複チェック

```bash
python3 -c "import json; ids=[a['id'] for a in json.load(open('docs/catalog/public/data/algorithms.json'))]; print('OK' if '<id>' not in ids else 'DUPLICATE: <id>')"
```

重複していたら処理中止し、ユーザーに既存エントリを更新するか別 ID にするか確認する。

### 3. ライブラリ環境の作成

`libs/<library_dir>/pyproject.toml` を以下のテンプレで作成（既存と同じ書式）:

```toml
[project]
name = "synth-<library_dir>"
version = "0.1.0"
requires-python = "<python_constraint>"
dependencies = [
    "<pypi_or_git>",
    "pandas",
    "numpy",
    # extra_dependencies があればここに追加
]

[tool.uv]
package = false
```

**重要**: `[build-system]` セクションは入れない（uv で hatch ビルドが走り失敗する事例あり）。

### 4. 環境構築 + 動作確認

```bash
cd libs/<library_dir> && uv sync
uv run python -c "import <module>; print('<module>', getattr(<module>, '__version__', 'OK'))"
```

失敗したら traceback を共有しユーザーに対処を求める（バージョン pin の追加など）。
sudo は使わない。

### 5. `algorithms.json` への追記

新規エントリを以下の形で追加（categoryと近い位置に挿入し、ファイル全体の流れを崩さない）:

```json
{
  "id": "<id>",
  "name": "<name>",
  "libraries": ["..."],
  "category": "...",
  "supported_data": ["..."],
  "tags": ["..."],
  "use_cases": ["..."],
  "input_requirements": ["..."],
  "privacy_mechanism": "...",
  "privacy_risk_level": "...",
  "description": "...",
  "strengths": ["..."],
  "weaknesses": ["..."],
  "reference": "...",
  "experiments": [],
  "summary_metrics": {}
}
```

`experiments` と `summary_metrics` は空でよい（後で `/add-experiment-case` で埋める）。

### 6. 検証

```bash
# JSON シンタックス
python3 -c "import json; json.load(open('docs/catalog/public/data/algorithms.json')); print('JSON OK')"
# フロントエンドのビルド (TS 型チェック含む)
cd docs/catalog && npx tsc --noEmit && npm run build 2>&1 | tail -5
```

ビルド失敗なら原因を特定して修正する。

### 7. 完了サマリ

以下を表示:
- 作成したファイルパス
- 追加した `algorithms.json` のエントリ ID
- 動作確認した import バージョン
- 次の推奨アクション: 「`/add-experiment-case <case_id>` で実験結果を登録」

## 重要ルール（CLAUDE.md 準拠）

- uv のみ使用、pip/venv/sudo 禁止
- ファイル名・ディレクトリ名は既存規約に合わせる（`libs/<lib_name>/`）
- 既存のフォーマットを変更しない（インデント、キー順）
- インタラクティブ入力は最小限（CLAUDE.md にあるルールで決められる項目は聞かない）
- スクリプト雛形（`run_<dataset>.py`）は **このスキルでは作らない**。データセット依存だから

$ARGUMENTS
