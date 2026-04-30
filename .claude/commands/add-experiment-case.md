# 新規実験事例の登録

実行・評価済みの合成データ実験を「事例カード」（experiment-cases.json）として登録し、
かつ各 algorithm の `experiments` 配列にも実験ログを追加する。

このスキルは **既に評価が済んでいる** ことを前提とする。
評価 JSON（quality_score / tstr / dcr / time_sec などを含む）が `results/<phase>/*.json` に存在しているはず。
存在しない場合は本スキルを呼ぶ前に評価を実行すること。

## 使い方

`/add-experiment-case <case_id>` — 例: `/add-experiment-case olist-ec-transactions`

引数なしの場合は `case_id` を尋ねる。

## 実行手順

### 1. 入力収集

```
case_id      : <ARGUMENTS> または対話で取得
title        : 事例カードのタイトル（80字以内）
data_category: single_table_master | single_table_transaction | single_table_timeseries | multi_table
scenario.description : 4-6 文の課題設定（業務文脈・元データ・合成の目的）
scenario.use_case    : 短いタグ（例: "テストデータ生成（複数表）"）
dataset.name : データセット表示名
dataset.rows / columns : 元データのサイズ（複数表ならテーブル合計）
dataset.features : 主要カラム or テーブル名+件数の配列
results_source : 評価 JSON のパス（例: results/phase2_olist/olist_eval.json）
recommendation : 1-3 文の所感・推奨。手法ごとの強み・トレードオフを書く
```

`results_source` は複数指定可（その場合は `,` 区切り）。

### 2. 重複チェック

```bash
python3 -c "import json; ids=[c['id'] for c in json.load(open('docs/catalog/public/data/experiment-cases.json'))]; print('OK' if '<case_id>' not in ids else 'DUPLICATE')"
```

重複ならユーザーに確認（既存を更新 or 別 ID）。

### 3. 評価 JSON から `results[]` を構築

`docs/catalog/src/types/experiment-case.ts` の `CaseResult` 型に合わせて生成する:

```ts
type CaseResult = {
  algorithm_id: string;
  algorithm_name: string;
  library: string;
  params: Record<string, unknown>;
  metrics: {
    quality_score?: number;
    tstr_accuracy?: number;
    tstr_f1?: number;
    dcr_mean?: number;
    time_sec?: number;
  };
  privacy_risk: "low" | "medium" | "high" | null;
};
```

抽出ルール:
- `algorithm_id` は `algorithms.json` に存在する ID と一致させる（一致しない場合はスキル中止）
- `algorithm_name` は同 algorithm の `name` フィールドを引く
- `library` は対応する run_log（`<library>_run_log*.json`）から取得（または対話）
- `params` は run_log の `epochs` / `batch_size` 等から拾う。なければ `{}`
- `metrics` は欠けているキーは出力に含めない（フロントは `?` 扱いで「—」を表示）
- `privacy_risk` は DCR と機構の判断:
  - DCR ≥ 0.4 かつ `privacy_mechanism != "none"` → `"low"`
  - DCR ≥ 0.2 → `"medium"`
  - DCR < 0.2 もしくは特殊 (BayesianNetwork 等) → `"high"`
  - 計算不可 → `null`

少数 (3 以内) の場合は対話で全件確認。多数なら一覧を表示してユーザーに削除指示を仰ぐ。

### 4. `experiment-cases.json` への追記

末尾の `]` の直前に新規エントリを挿入。**既存エントリは触らない**。

```json
{
  "id": "<case_id>",
  "title": "<title>",
  "data_category": "<data_category>",
  "scenario": { "description": "...", "use_case": "..." },
  "dataset": { "name": "...", "rows": N, "columns": M, "features": ["..."] },
  "results": [ /* 上で構築した CaseResult[] */ ],
  "recommendation": "..."
}
```

### 5. `algorithms.json` の更新

各 result について、`algorithms.json` の対応 algorithm の `experiments` 配列に以下を追加:

```json
{
  "id": "<algorithm_id>_<dataset_slug>",
  "library": "<library>",
  "library_version": "<version from run_log _env>",
  "params": { ... },
  "dataset": "<dataset_slug>",
  "data_type": "<single_table|multi_table|timeseries>",
  "phase": "<phase id (e.g., phase2_olist)>",
  "metrics": { ...full metrics from eval... }
}
```

`summary_metrics` も再計算（`best_quality_score` / `best_tstr_f1` / `best_dcr_mean` / `fastest_time_sec` の更新）。

### 6. 検証

```bash
# JSON シンタックス
python3 -c "import json; json.load(open('docs/catalog/public/data/experiment-cases.json')); json.load(open('docs/catalog/public/data/algorithms.json')); print('JSON OK')"
# 型チェック + ビルド
cd docs/catalog && npx tsc --noEmit && npm run build 2>&1 | tail -5
```

### 7. 完了サマリ

- 追加した case_id とリンク先 (https://gghatano.github.io/syntheticdata-generation-catalog/case/<case_id>) を表示
- algorithms.json で更新された algorithm 一覧を表示
- `git diff --stat docs/catalog/public/data/` を実行し、変更ファイルを確認

## 重要ルール

- **既存エントリは絶対に書き換えない**（不変性 / append-only。CLAUDE.md の実験結果ルールに準拠）
- 同一条件の再実行（同じ params + dataset）は別 case_id を勧める（条件サフィックス付き）
- メトリクスを「null だがそれっぽい値で埋める」のは禁止。実測値のみ記載
- ビルドが落ちたらコミット・PR を作らない
- 結果が極端に悪い・予想外でも、**事実を歪めない**。recommendation で考察として書く

$ARGUMENTS
