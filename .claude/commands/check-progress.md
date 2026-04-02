# 進捗確認

検証タスクの進捗状況を確認して表示する。

## 実行手順

1. `docs/tasks/progress.json` を読み込む
2. 各タスクのステータスを一覧表示
3. `results/` ディレクトリの実際のファイル存在状況も確認
4. 次に実行すべきタスクを提案

## 表示内容

- 各タスク（00〜05）のステータス（not_started / in_progress / completed / error）
- `results/phase1/`, `results/phase2/`, `results/phase3/` の合成データCSV数
- `results/evaluation/all_results.json` の有無
- エラーがあればエラー内容の要約
- install_check.json のライブラリ導入状況
