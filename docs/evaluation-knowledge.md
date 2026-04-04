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

---

## Issue #30: ホテル予約データ（Hotel Reservations, 複数表）

**データ概要**: 2テーブル（hotels: 10行, guests: 658行）、1:N リレーション

### 評価結果

| 指標 | 値 |
|------|-----|
| Quality Score（Multi-Table） | 0.6477 |
| Diagnostic Score | 1.0000 |
| FK 整合性 | 完全維持（orphan=0） |
| DCR Mean (guests) | 0.3190 |
| DCR Mean (hotels) | 0.5810 |
| DCR Mean (overall) | 0.4500 |
| Privacy Risk | low |

### 知見

1. **Multi-Table QualityReport の活用**: `sdmetrics.reports.multi_table.QualityReport` を使用。Column Shapes (86.6%), Column Pair Trends (53.1%), Cardinality (60.0%), Intertable Trends (59.4%) の4軸評価。全体スコアは 64.8%。単一表より低くなる傾向がある。

2. **FK 整合性は SDV HMA で完全維持**: `relationships` をメタデータから読み取り、合成データの orphan record を検証。SDV の HMA は親テーブルから子テーブルを階層的に生成するため、FK 違反は発生しない。

3. **DCR の overflow 問題**: guests テーブルに大きな整数値（ID等）が含まれる場合、int の範囲を超えて overflow する。`astype(float)` で float64 に変換してから正規化することで解決。**全評価スクリプトで数値列を float64 に統一すべき。**

4. **テーブル間の品質差**: hotels（10行）は行数が極小のため DCR=0.58 と距離が大きい。guests（658行）は DCR=0.32 とやや近い。

5. **Cardinality Score が 60%**: 各 hotel に紐づく guest の数（カーディナリティ）の分布再現度。10ホテル中6件が実データの分布範囲内。小規模データでは改善余地あり。

### 複数表評価のパターン（#28 IMDB にも適用）
- `sdmetrics.reports.multi_table` を使用
- FK 整合性は `metadata['relationships']` から自動検証
- DCR はテーブル単位で計算し、平均を全体指標とする
- TSTR は複数表には直接適用困難（テーブル結合が必要）→ スキップ

---

## Issue #28: IMDB映画データベース（複数表, 7テーブル）

**データ概要**: 7テーブル（actors: 1907, roles: 1989, movies: 36, directors: 34 等）、6リレーション（多対多含む）

### 評価結果

| 指標 | 値 |
|------|-----|
| Quality Score（Multi-Table） | 0.5187 |
| Diagnostic Score | 1.0000 |
| FK 整合性 | 全6関係で維持 |
| Cardinality Score | 91.88% |
| DCR Mean (overall) | 0.3846 |
| Privacy Risk | low |

### 知見

1. **複雑スキーマでの品質低下**: 7テーブル・6リレーションの複雑スキーマでは Quality Score が 0.52 に低下。特に Column Pair Trends (22.6%) と Intertable Trends (23.8%) が低い。テーブル数が増えるほどテーブル間の統計的関係性の再現が困難になる。

2. **Cardinality Score は高い (91.9%)**: ホテル（60%）に比べて大幅に高い。テーブルあたりの行数が多い（actors: 1907行）方がカーディナリティ分布の学習が容易。

3. **行数の完全再現**: HMA は全テーブルで元データと同じ行数を生成（ratio=1.00）。これは HMA の設計上の特性。

4. **テーブル間 DCR の差異**: actors (1.37) は距離が大きく安全、directors_genres (0.09) は近い。中間テーブル（多対多リレーションの結合テーブル）は組み合わせパターンが限られるため DCR が低くなりやすい。

5. **FK 整合性は複雑スキーマでも完全維持**: 6つの FK 関係すべてで orphan=0。HMA の階層的生成が複雑な依存関係でも機能する。

---

## Issue #31: 株価時系列データ（NASDAQ 100, 時系列）

**データ概要**: 25,784行 × 8列、103銘柄の日次データ（2019年）、PAR 128ep で10シーケンス生成

### 評価結果

| 指標 | 値 |
|------|-----|
| Quality Score | 0.4985 |
| DCR Mean | 0.5709 |
| Privacy Risk | low |

### 時系列特性

| 列 | 実データ平均 | 合成平均 | 実データ自己相関(lag1) | 合成自己相関(lag1) |
|----|------------|---------|---------------------|-------------------|
| Open | 183.4 | 318.9 | 0.9962 | 0.6155 |
| Close | 183.5 | 324.4 | 0.9963 | 0.6659 |
| Volume | 6.57M | 3.68M | 0.9036 | 0.3167 |
| MarketCap | 70.6B | 82.2B | 0.9989 | 0.7623 |

### 知見

1. **時系列の自己相関再現が不十分**: 実データの自己相関は 0.90〜0.99 と非常に高い（株価の連続性）が、合成データは 0.32〜0.76 に低下。PAR は時系列パターンの「方向性」は捉えるが、**連続性の強さ（粘性）を過小評価**する傾向がある。

2. **シーケンス数の制約**: 実データは103銘柄だが、PAR は `num_sequences=10` で生成（run_phase3.py の設定に従う）。合成データは2,201行 vs 実データ25,784行と大幅に少ない。Quality Score 0.50 の一因。

3. **平均値のずれ**: Open/Close の合成平均が実データの約1.7倍。PAR は各シーケンスの分布を独立に学習するため、銘柄のサンプリングバイアスが出やすい。

4. **時系列評価の追加指標**: SDMetrics の QualityReport は時系列構造を直接評価しない（行単位の分布比較）。自己相関・トレンド再現度・ボラティリティ比較を別途実装した。今後は **DTW（Dynamic Time Warping）距離** や **時系列クラスタリングの再現度** も検討の余地がある。

### 時系列評価のパターン（#32 IoT にも適用）
- SDMetrics は single_table として評価（時系列固有の構造は捉えない）
- 自己相関 (lag=1) の比較で時系列の連続性を評価
- 銘柄/拠点ごとの統計量比較（平均・標準偏差）
- シーケンス数の比較
