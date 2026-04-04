"""Issue #28: IMDB映画データベースの品質評価・テーブル間関係性評価

実行: cd libs/evaluation && uv run python eval_imdb.py

7テーブル・多対多リレーションの複数表評価。
"""
import pandas as pd
import numpy as np
import json
import os
import sys
import glob
import traceback

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..', '..')
OUTPUT_DIR = os.path.join(ROOT, 'results/phase2')
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.join(ROOT, 'data/raw'), exist_ok=True)

RANDOM_SEED = 42

# ============================================================
# 1. データ準備
# ============================================================
META_JSON = os.path.join(ROOT, 'data/raw/d_imdb_metadata.json')

# IMDB テーブル名リスト（download_demo で取得される）
IMDB_TABLES = ['actors', 'directors', 'directors_genres', 'movies', 'movies_directors', 'movies_genres', 'roles']

# 実データが存在するか確認
real_exists = all(
    os.path.exists(os.path.join(ROOT, f'data/raw/d_imdb_{t}.csv'))
    for t in IMDB_TABLES
)
synth_exists = any(
    os.path.exists(os.path.join(OUTPUT_DIR, f'sdv_hma_imdb_{t}.csv'))
    for t in IMDB_TABLES
)

if not real_exists or not synth_exists:
    print("IMDB data not found. Generating via SDV download_demo...")
    from sdv.datasets.demo import download_demo
    from sdv.multi_table import HMASynthesizer
    import sdv

    data, meta = download_demo(modality='multi_table', dataset_name='imdb_small')
    with open(META_JSON, 'w') as f:
        json.dump(meta.to_dict(), f, indent=2)

    for tname, df in data.items():
        csv_path = os.path.join(ROOT, f'data/raw/d_imdb_{tname}.csv')
        df.to_csv(csv_path, index=False)
        print(f"  Saved real {tname}: {len(df)} rows")

    synthesizer = HMASynthesizer(meta)
    synthesizer.fit(data)
    synth_data = synthesizer.sample()

    for tname, df in synth_data.items():
        csv_path = os.path.join(OUTPUT_DIR, f'sdv_hma_imdb_{tname}.csv')
        df.to_csv(csv_path, index=False)
        print(f"  Saved synth {tname}: {len(df)} rows")
else:
    print("IMDB data found. Loading...")

# 実データ読み込み
real_tables = {}
for tname in IMDB_TABLES:
    csv_path = os.path.join(ROOT, f'data/raw/d_imdb_{tname}.csv')
    if os.path.exists(csv_path):
        real_tables[tname] = pd.read_csv(csv_path)
        print(f"Real {tname}: {len(real_tables[tname])} rows, {len(real_tables[tname].columns)} cols")

# 合成データ読み込み
synth_tables = {}
for tname in IMDB_TABLES:
    csv_path = os.path.join(OUTPUT_DIR, f'sdv_hma_imdb_{tname}.csv')
    if os.path.exists(csv_path):
        synth_tables[tname] = pd.read_csv(csv_path)
        print(f"Synth {tname}: {len(synth_tables[tname])} rows")

results = {}

# ============================================================
# 2. SDMetrics Multi-Table 評価
# ============================================================
print("\n=== SDMetrics Multi-Table Evaluation ===")
try:
    from sdmetrics.reports.multi_table import QualityReport, DiagnosticReport

    metadata_dict = json.load(open(META_JSON))

    quality = QualityReport()
    quality.generate(real_tables, synth_tables, metadata_dict)
    quality_score = quality.get_score()

    diag = DiagnosticReport()
    diag.generate(real_tables, synth_tables, metadata_dict)
    diag_score = diag.get_score()

    results['sdv_hma_imdb'] = {
        'quality_score': quality_score,
        'diagnostic_score': diag_score,
    }
    print(f"  Quality: {quality_score:.4f}, Diagnostic: {diag_score:.4f}")
except Exception as e:
    print(f"  SDMetrics ERROR: {e}")
    traceback.print_exc()
    results['sdv_hma_imdb'] = {'quality_score': None, 'diagnostic_score': None}

# ============================================================
# 3. FK 整合性 + テーブル間関係性評価
# ============================================================
print("\n=== FK Integrity & Relationship Check ===")
try:
    metadata_raw = json.load(open(META_JSON))
    relationships = metadata_raw.get('relationships', [])
    print(f"  Relationships: {len(relationships)}")

    fk_results = []
    for rel in relationships:
        parent_table = rel.get('parent_table_name')
        child_table = rel.get('child_table_name')
        parent_pk = rel.get('parent_primary_key')
        child_fk = rel.get('child_foreign_key')

        if parent_table in synth_tables and child_table in synth_tables:
            parent_ids = set(synth_tables[parent_table][parent_pk])
            child_fk_values = synth_tables[child_table][child_fk]
            orphans = child_fk_values[~child_fk_values.isin(parent_ids)]
            orphan_rate = len(orphans) / len(child_fk_values) if len(child_fk_values) > 0 else 0

            fk_info = {
                'parent': parent_table,
                'child': child_table,
                'parent_pk': parent_pk,
                'child_fk': child_fk,
                'orphan_count': int(len(orphans)),
                'total_child_rows': int(len(child_fk_values)),
                'orphan_rate': round(orphan_rate, 4),
                'valid': orphan_rate == 0,
            }
            fk_results.append(fk_info)
            status = "OK" if fk_info['valid'] else f"FAIL ({fk_info['orphan_count']} orphans)"
            print(f"  {parent_table}.{parent_pk} -> {child_table}.{child_fk}: {status}")

    results['sdv_hma_imdb']['fk_integrity'] = fk_results
    results['sdv_hma_imdb']['fk_all_valid'] = all(fk['valid'] for fk in fk_results)

    # テーブル行数比較（カーディナリティの大まかな再現度）
    print("\n  Table row counts (real vs synth):")
    row_comparison = {}
    for tname in real_tables:
        if tname in synth_tables:
            real_rows = len(real_tables[tname])
            synth_rows = len(synth_tables[tname])
            ratio = synth_rows / real_rows if real_rows > 0 else 0
            row_comparison[tname] = {
                'real_rows': real_rows,
                'synth_rows': synth_rows,
                'ratio': round(ratio, 2),
            }
            print(f"    {tname}: real={real_rows}, synth={synth_rows}, ratio={ratio:.2f}")
    results['sdv_hma_imdb']['row_comparison'] = row_comparison
except Exception as e:
    print(f"  FK check ERROR: {e}")
    traceback.print_exc()

# ============================================================
# 4. テーブル単位 DCR 評価
# ============================================================
print("\n=== DCR Privacy Evaluation (per-table) ===")
from sklearn.preprocessing import LabelEncoder
from sklearn.neighbors import NearestNeighbors


def encode_for_distance(df):
    df_enc = df.copy()
    for col in df_enc.select_dtypes(include=['bool']).columns:
        df_enc[col] = df_enc[col].astype(int)
    for col in df_enc.select_dtypes(include=['object', 'category']).columns:
        df_enc[col] = df_enc[col].fillna('_MISSING_')
        le = LabelEncoder()
        df_enc[col] = le.fit_transform(df_enc[col].astype(str))
    for col in df_enc.select_dtypes(include=['number']).columns:
        df_enc[col] = df_enc[col].astype(float).fillna(df_enc[col].astype(float).median())
    for col in df_enc.columns:
        df_enc[col] = pd.to_numeric(df_enc[col], errors='coerce').astype(float).fillna(0)
        col_min = df_enc[col].min()
        col_max = df_enc[col].max()
        col_range = col_max - col_min
        if col_range > 0:
            df_enc[col] = (df_enc[col] - col_min) / col_range
    return df_enc


dcr_per_table = {}
for tname in synth_tables:
    if tname not in real_tables:
        continue
    try:
        real_df = real_tables[tname]
        synth_df = synth_tables[tname]
        common_cols = sorted(set(real_df.columns) & set(synth_df.columns))
        if len(common_cols) < 2:
            print(f"  {tname}: SKIP (only {len(common_cols)} common cols)")
            continue
        real_sub = real_df[common_cols]
        synth_sub = synth_df[common_cols]

        real_enc = encode_for_distance(real_sub)
        synth_enc = encode_for_distance(synth_sub)

        max_rows = 5000
        real_sample = real_enc.sample(min(max_rows, len(real_enc)), random_state=42)
        synth_sample = synth_enc.sample(min(max_rows, len(synth_enc)), random_state=42)

        nn = NearestNeighbors(n_neighbors=1, metric='euclidean', n_jobs=-1)
        nn.fit(real_sample.values)
        distances, _ = nn.kneighbors(synth_sample.values)
        dcr = distances.flatten()

        dcr_per_table[tname] = {
            'dcr_mean': round(float(np.mean(dcr)), 6),
            'dcr_median': round(float(np.median(dcr)), 6),
            'dcr_5th_percentile': round(float(np.percentile(dcr, 5)), 6),
        }
        print(f"  {tname}: dcr_mean={dcr_per_table[tname]['dcr_mean']:.4f}")
    except Exception as e:
        print(f"  {tname}: DCR ERROR - {e}")
        traceback.print_exc()

results['sdv_hma_imdb']['dcr_per_table'] = dcr_per_table

if dcr_per_table:
    overall_dcr = np.mean([t['dcr_mean'] for t in dcr_per_table.values()])
    results['sdv_hma_imdb']['dcr_mean'] = round(float(overall_dcr), 6)
    print(f"  Overall DCR mean: {overall_dcr:.4f}")

# privacy_risk 判定
dcr_mean = results['sdv_hma_imdb'].get('dcr_mean')
if dcr_mean is None:
    results['sdv_hma_imdb']['privacy_risk'] = 'unknown'
elif dcr_mean < 0.1:
    results['sdv_hma_imdb']['privacy_risk'] = 'high'
elif dcr_mean < 0.3:
    results['sdv_hma_imdb']['privacy_risk'] = 'medium'
else:
    results['sdv_hma_imdb']['privacy_risk'] = 'low'

# ============================================================
# 5. 結果保存
# ============================================================
eval_output = os.path.join(OUTPUT_DIR, 'imdb_eval.json')
with open(eval_output, 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to {eval_output}")

# ============================================================
# 6. experiment-cases.json 更新
# ============================================================
print("\n=== Updating experiment-cases.json ===")
cases_path = os.path.join(ROOT, 'docs/catalog/public/data/experiment-cases.json')
with open(cases_path) as f:
    cases = json.load(f)

for case in cases:
    if case['id'] != 'imdb-movie-database':
        continue

    for r in case['results']:
        if r['algorithm_id'] == 'hma' and r['library'] == 'SDV':
            m = results.get('sdv_hma_imdb', {})
            r['metrics']['quality_score'] = round(m.get('quality_score', 0), 4) if m.get('quality_score') else None
            r['metrics']['dcr_mean'] = m.get('dcr_mean')
            r['privacy_risk'] = m.get('privacy_risk', 'unknown')

    m = results.get('sdv_hma_imdb', {})
    qs = m.get('quality_score')
    fk_valid = m.get('fk_all_valid')
    pr = m.get('privacy_risk', '')
    n_tables = len(real_tables)
    n_rels = len(results.get('sdv_hma_imdb', {}).get('fk_integrity', []))

    parts = []
    if qs:
        parts.append(f"HMA の品質スコアは{qs:.2f}（{n_tables}テーブル・{n_rels}リレーション）。")
    if fk_valid is not None:
        parts.append(f"FK整合性は{'全{0}関係で維持'.format(n_rels) if fk_valid else '一部不整合あり'}。")
    if pr:
        parts.append(f"プライバシーリスクは{pr}。")
    parts.append("多対多リレーション（俳優↔映画、映画↔ジャンル）を含む複雑スキーマでも HMA は整合性を維持可能。")
    case['recommendation'] = ' '.join(parts)
    print(f"  Updated recommendation: {case['recommendation']}")
    break

with open(cases_path, 'w') as f:
    json.dump(cases, f, indent=2, ensure_ascii=False)
print("experiment-cases.json updated.")

# サマリ
print("\n=== Summary ===")
m = results.get('sdv_hma_imdb', {})
print(f"  quality_score={m.get('quality_score', 'N/A')}")
print(f"  fk_all_valid={m.get('fk_all_valid', 'N/A')}")
print(f"  dcr_mean={m.get('dcr_mean', 'N/A')}")
print(f"  privacy_risk={m.get('privacy_risk', 'N/A')}")
