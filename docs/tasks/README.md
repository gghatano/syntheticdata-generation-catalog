# 検証タスク一覧

合成データ生成ライブラリの比較検証を自律的に実行するためのタスク定義。

## タスク構成

| ファイル | 内容 | 依存 | 推定規模 |
|---------|------|------|---------|
| [00-setup.md](00-setup.md) | 環境構築・依存パッケージ導入・.gitignore | なし | 小 |
| [01-data-preparation.md](01-data-preparation.md) | データセット取得・前処理 | 00 | 小 |
| [02-phase1-single-table.md](02-phase1-single-table.md) | 単一表実験（4ライブラリ） | 00, 01 | 大 |
| [03-phase2-multi-table.md](03-phase2-multi-table.md) | 複数表実験（2ライブラリ） | 00, 01 | 中 |
| [04-phase3-timeseries.md](04-phase3-timeseries.md) | 時系列実験（4ライブラリ） | 00, 01 | 大 |
| [05-evaluation.md](05-evaluation.md) | 統合評価・結果JSON生成 | 02, 03, 04 | 中 |

**注意**: Phase 2 と Phase 3 は互いに独立しており、並列実行可能。
可視化・GitHub Pages 公開は後続フェーズで実施する（本タスク群のスコープ外）。

## 自律実行時の原則

1. **各タスクの冒頭で前提条件チェックを実行する** — 未完了の依存タスクがあれば先にそちらを実行
2. **ファイル操作はプロジェクトディレクトリ内に限定** — `/home/hatano/works/syntheticdata-catalog/` 配下のみ
3. **各ライブラリは `libs/<name>/` 配下の独立した uv 環境で実行** — sudo 不要、依存競合なし
4. **ネットワークアクセスが必要な箇所は明示** — データダウンロード・uv sync
5. **各ステップの完了を `docs/tasks/progress.json` に記録** — 中断・再開時の判定に使用
6. **エラー発生時はスキップせず `progress.json` にエラー内容を記録して次のライブラリ/実験へ進む**
7. **全スクリプトで `RANDOM_SEED=42` を使用** — 再現性の確保
8. **run_log にライブラリバージョンを記録** — 再現環境の特定に必要

## ディレクトリ構成

```
syntheticdata-catalog/
├── libs/                          # ライブラリごとの独立環境
│   ├── sdv/                       # L-01: SDV
│   │   ├── pyproject.toml
│   │   ├── run_phase1.py
│   │   ├── run_phase2.py
│   │   └── run_phase3.py
│   ├── synthcity/                 # L-02: SynthCity
│   │   ├── pyproject.toml
│   │   └── run_phase1.py
│   ├── mostlyai/                  # L-03: MOSTLY AI
│   │   ├── pyproject.toml
│   │   ├── run_phase1.py
│   │   ├── run_phase2.py
│   │   └── run_phase3.py
│   ├── ydata/                     # L-04: ydata-synthetic
│   │   ├── pyproject.toml
│   │   ├── run_phase1.py
│   │   └── run_phase3.py
│   └── evaluation/                # 評価専用環境
│       ├── pyproject.toml
│       ├── tstr_phase1.py
│       ├── eval_phase2.py
│       ├── eval_phase3.py
│       ├── privacy_eval.py
│       └── aggregate_results.py
├── data/
│   ├── raw/                       # ダウンロードしたデータ
│   └── processed/                 # 前処理済みデータ + profile.json
├── results/
│   ├── phase1/                    # 合成データCSV + run_log.json
│   ├── phase2/
│   ├── phase3/
│   └── evaluation/                # 統合結果 all_results.json
├── docs/
│   ├── spec-phase0.md             # 仕様書
│   └── tasks/                     # 本タスク定義群
│       ├── README.md
│       └── progress.json
└── .gitignore
```

## 進捗管理

`progress.json` の構造:

```json
{
  "tasks": {
    "00-setup": { "status": "completed", "completed_at": "2026-04-02T10:00:00" },
    "01-data-preparation": { "status": "in_progress", "current_step": "D1-download" },
    "02-phase1": { "status": "not_started" }
  }
}
```

status: `not_started` | `in_progress` | `completed` | `error`

### progress.json 更新ヘルパー

各スクリプトの冒頭/末尾で使用する共通パターン:

```python
import json, os
from datetime import datetime

PROGRESS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..', 'docs', 'tasks', 'progress.json'
)

def update_progress(task_id, status, **kwargs):
    """progress.json を更新する"""
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

# 使用例:
# update_progress('02-phase1', 'in_progress', current_step='sdv_ctgan')
# update_progress('02-phase1', 'completed')
# update_progress('02-phase1', 'error', error='OOM during CTGAN training')
```

## 実行順序

```
00-setup
  └→ 01-data-preparation
       ├→ 02-phase1 (単一表)  ─→ 05-evaluation
       ├→ 03-phase2 (複数表)  ─→ 05-evaluation
       └→ 04-phase3 (時系列)  ─→ 05-evaluation
```

Phase 2/3 は Phase 1 と独立して並列実行可能。
05-evaluation は完了した Phase の結果のみを集約（全 Phase 完了を待たなくてよい）。
