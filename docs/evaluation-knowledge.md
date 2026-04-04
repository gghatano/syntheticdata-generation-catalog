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

---

## Issue #29: 企業マスタ（Fake Companies, 単一表）

**データ概要**: 12行 × 12列、SDV download_demo の fake_companies データセット

### 評価結果

| 手法 | Quality Score | TSTR F1 | DCR Mean | Privacy Risk |
|------|-------------|---------|----------|-------------|
| GaussianCopula | 0.5871 | 0.3333 | 1.2460 | low |

### 知見

1. **極小データでの品質評価の限界**: 12行のデータでは Column Pair Trends Score が 41% と大幅に低下。列間の相関を正しく学習するにはデータ量が不足。Quality Score 0.59 は妥当な結果だが、統計的な信頼性は限定的。

2. **TSTR の無意味化**: 12行を train/test 分割すると数件ずつになり、ランダムフォレストの分類精度がほぼランダム（acc=0.33）。**極小データでは TSTR は評価指標として使えない**。DCR と SDMetrics のみで評価すべき。

3. **DCR は極小データでも計算可能**: 12行同士の距離計算は問題なく完了。dcr_mean=1.25 と距離が大きく、exact_match=0 なのでプライバシーリスクは low。GaussianCopula は統計分布からのサンプリングなので、少量データでも元データのコピーにはなりにくい。

4. **小規模データへの合成データ適用の教訓**: 行数が少ないと列間の統計的関係の再現が困難。合成データの主な用途はテスト環境用のダミーデータ生成であり、品質評価は参考程度に留めるべき。

### 注意点の更新
- **12行以下の極小データでは TSTR をスキップまたは注記付きで実施する**
- 品質スコアの解釈には行数を考慮する（少量データでの低スコアは必ずしも手法の問題ではない）
