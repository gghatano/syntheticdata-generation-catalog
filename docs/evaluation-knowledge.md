# 品質評価の知見ログ

各データセットの品質評価で得られた知見を蓄積し、後続の評価に��用する。

---

## Issue #27: 保険契約データ（Insurance, 単一表）

**データ概要**: 20,000行 × 27���、SDV download_demo の insurance データセット

### 評価結果

| 手法 | Quality Score | TSTR F1 | DCR Mean | Privacy Risk |
|------|-------------|---------|----------|-------------|
| GaussianCopula | 0.9049 | 0.6285 | 1.1546 | low |
| CTGAN 50ep | 0.8794 | 0.6956 | 0.9144 | high |

### 知見

1. **boolean 列の正規化エラー**: Insurance データには boolean 型の列が含まれ、DCR 計算時に `numpy boolean subtract` エラーが発生。`df_enc[col].astype(int)` で事前変換が必要。今後の評価スクリプトでも boolean 列の前処理を忘れずに入れること。

2. **TSTR のターゲッ��列選択**: Insurance データには明確な分類ターゲット列がなく、`charges`（保険料）が連続値。中央値で二値化して分類タスクに変換した。TSTR F1 が低め（0.63〜0.70）なのはこの二値化の影響もある。回帰���スク（MAE/RMSE）での評価も将来的に追加すべき。

3. **CTGAN のプライバシーリスク**: exact_match_rate が 4.78% と高く、privacy_risk=high と判定。50 epochs ではまだ学習が不十分で、元データに近いレコードを多く生成している可能性。epoch 数を増やすと改善する可能性あり。一方 GaussianCopula ���統計分布ベースのため exact_match は低い。

4. **evaluation 環境の問題**: `libs/evaluation/pyproject.toml` で `packages = []` だと hatchling がビルド失敗する。`synth_evaluation` ダミーパッケージを作成し `packages = ["synth_evaluation"]` に修正。また SDV も依存に追加（download_demo でのデータ取得に必要）。

### 今後の課題に向けた注意点
- **boolean 列対策を encode_for_distance に含める**（#29, #30 等でも同様の問題が起こる可能性）
- **回帰タスクの評価フレームワーク**を別途検討（charges のような連続ターゲットに対応）
- **evaluation 環境に SDV を追加済み**なので、他の評価スクリプトも同環境で実行可能
