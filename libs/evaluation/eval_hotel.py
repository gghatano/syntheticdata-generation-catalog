"""Issue #30: ホテル予約データの品質評価・FK整合性評価

実行: cd libs/evaluation && uv run python eval_hotel.py

複数表（hotels 1:N guests）の品質評価。
SDMetrics Multi-Table QualityReport + FK整合性検証 + テーブル単位の DCR。
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
os.makedirs(os.path.join(ROOT, 'data/processed'), exist_ok=True)

RANDOM_SEED = 42

# ============================================================
# 1. データ準備
# ============================================================
# Phase 2 のホテル予約データ
HOTEL_CSV = os.path.join(ROOT, 'data/processed/d2_hotels.csv')
GUEST_CSV = os.path.join(ROOT, 'data/processed/d2_guests.csv')
METADATA_PATH = os.path.join(ROOT, 'data/raw/d2_metadata.json')
SYNTH_HOTEL_CSV = os.path.join(OUTPUT_DIR, 'sdv_hma_hotels.csv')
SYNTH_GUEST_CSV = os.path.join(OUTPUT_DIR, 'sdv_hma_guests.csv')

need_generate = (
    not os.path.exists(HOTEL_CSV) or
    not os.path.exists(SYNTH_HOTEL_CSV)
)

if need_generate:
    print("Hotel data not found. Generating via SDV...")
    sys.path.insert(0, os.path.join(ROOT, 'libs'))

    from sdv.datasets.demo import download_demo
    from sdv.multi_table import HMASynthesizer
    from sdv.metadata import Metadata
    import sdv

    data, meta = download_demo(modality='multi_table', dataset_name='fake_hotels')
    os.makedirs(os.path.join(ROOT, 'data/raw'), exist_ok=True)
    with open(METADATA_PATH, 'w') as f:
        json.dump(meta.to_dict(), f, indent=2)

    for tname, df in data.items():
        csv_path = os.path.join(ROOT, f'data/processed/d2_{tname}.csv')
        df.to_csv(csv_path, index=False)
        print(f"  Saved real {tname}: {len(df)} rows")

    synthesizer = HMASynthesizer(meta)
    synthesizer.fit(data)
    synth_data = synthesizer.sample()

    for tname, df in synth_data.items():
        csv_path = os.path.join(OUTPUT_DIR, f'sdv_hma_{tname}.csv')
        df.to_csv(csv_path, index=False)
        print(f"  Saved synth {tname}: {len(df)} rows")
else:
    print("Hotel data found. Loading...")

# 実データ読み込み
real_tables = {}
for csv_file in sorted(glob.glob(os.path.join(ROOT, 'data/processed/d2_*.csv'))):
    tname = os.path.basename(csv_file).replace('d2_', '').replace('.csv', '')
    if 'profile' in tname:
        continue
    real_tables[tname] = pd.read_csv(csv_file)
    print(f"Real {tname}: {len(real_tables[tname])} rows, {len(real_tables[tname].columns)} cols")

# 合成データ読み込み
synth_tables = {}
for csv_file in sorted(glob.glob(os.path.join(OUTPUT_DIR, 'sdv_hma_*.csv'))):
    # sdv_hma_imdb_* を除外（IMDB は別 Issue）
    basename = os.path.basename(csv_file).replace('sdv_hma_', '').replace('.csv', '')
    if 'imdb' in basename:
        continue
    if basename in real_tables:
        synth_tables[basename] = pd.read_csv(csv_file)
        print(f"Synth {basename}: {len(synth_tables[basename])} rows")

results = {}

# ============================================================
# 2. SDMetrics Multi-Table 評価
# ============================================================
print("\n=== SDMetrics Multi-Table Evaluation ===")
try:
    from sdmetrics.reports.multi_table import QualityReport, DiagnosticReport

    metadata_raw = json.load(open(METADATA_PATH))
    # metadata_dict は tables を含む形式
    metadata_dict = metadata_raw

    quality = QualityReport()
    quality.generate(real_tables, synth_tables, metadata_dict)
    quality_score = quality.get_score()

    diag = DiagnosticReport()
    diag.generate(real_tables, synth_tables, metadata_dict)
    diag_score = diag.get_score()

    results['sdv_hma'] = {
        'quality_score': quality_score,
        'diagnostic_score': diag_score,
    }
    print(f"  Quality: {quality_score:.4f}, Diagnostic: {diag_score:.4f}")
except Exception as e:
    print(f"  SDMetrics ERROR: {e}")
    traceback.print_exc()
    results['sdv_hma'] = {'quality_score': None, 'diagnostic_score': None}

# ============================================================
# 3. FK 整合性評価
# ============================================================
print("\n=== FK Integrity Check ===")
try:
    metadata_raw = json.load(open(METADATA_PATH))
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

    results['sdv_hma']['fk_integrity'] = fk_results
    results['sdv_hma']['fk_all_valid'] = all(fk['valid'] for fk in fk_results)
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

results['sdv_hma']['dcr_per_table'] = dcr_per_table

# 全テーブルの DCR 平均を算出
if dcr_per_table:
    overall_dcr = np.mean([t['dcr_mean'] for t in dcr_per_table.values()])
    results['sdv_hma']['dcr_mean'] = round(float(overall_dcr), 6)
    print(f"  Overall DCR mean: {overall_dcr:.4f}")

# privacy_risk 判定
dcr_mean = results['sdv_hma'].get('dcr_mean')
if dcr_mean is None:
    results['sdv_hma']['privacy_risk'] = 'unknown'
elif dcr_mean < 0.1:
    results['sdv_hma']['privacy_risk'] = 'high'
elif dcr_mean < 0.3:
    results['sdv_hma']['privacy_risk'] = 'medium'
else:
    results['sdv_hma']['privacy_risk'] = 'low'

# ============================================================
# 5. 結果保存
# ============================================================
eval_output = os.path.join(OUTPUT_DIR, 'hotel_eval.json')
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
    if case['id'] != 'hotel-reservation-multitable':
        continue

    for r in case['results']:
        if r['algorithm_id'] == 'hma' and r['library'] == 'SDV':
            m = results.get('sdv_hma', {})
            r['metrics']['quality_score'] = round(m.get('quality_score', 0), 4) if m.get('quality_score') else None
            r['metrics']['dcr_mean'] = m.get('dcr_mean')
            r['privacy_risk'] = m.get('privacy_risk', 'unknown')

    m = results.get('sdv_hma', {})
    qs = m.get('quality_score')
    fk_valid = m.get('fk_all_valid')
    pr = m.get('privacy_risk', '')
    parts = []
    if qs:
        parts.append(f"HMA の品質スコアは{qs:.2f}。")
    if fk_valid is not None:
        parts.append(f"FK整合性は{'完全維持' if fk_valid else '一部不整合あり'}。")
    if pr:
        parts.append(f"プライバシーリスクは{pr}。")
    parts.append("SDV の HMA は複数表の外部キー関係を自動学習し、整合性を維持した合成データを生成可能。")
    case['recommendation'] = ' '.join(parts)
    print(f"  Updated recommendation: {case['recommendation']}")
    break

with open(cases_path, 'w') as f:
    json.dump(cases, f, indent=2, ensure_ascii=False)
print("experiment-cases.json updated.")

# サマリ
print("\n=== Summary ===")
m = results.get('sdv_hma', {})
print(f"  quality_score={m.get('quality_score', 'N/A')}")
print(f"  fk_all_valid={m.get('fk_all_valid', 'N/A')}")
print(f"  dcr_mean={m.get('dcr_mean', 'N/A')}")
print(f"  privacy_risk={m.get('privacy_risk', 'N/A')}")
