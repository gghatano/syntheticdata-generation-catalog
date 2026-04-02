"""Phase 1 プライバシー評価: DCR, Exact Match, Nearest Neighbor"""
import pandas as pd
import numpy as np
import json
import glob
import os
from sklearn.preprocessing import LabelEncoder
from sklearn.neighbors import NearestNeighbors

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..', '..')
REAL_DATA_PATH = os.path.join(ROOT, 'data/processed/d1_adult.csv')
OUTPUT_DIR = os.path.join(ROOT, 'results/phase1')

real_data = pd.read_csv(REAL_DATA_PATH)


def encode_for_distance(df):
    """距離計算用にエンコード"""
    df_enc = df.copy()
    for col in df_enc.select_dtypes(include=['object', 'category']).columns:
        df_enc[col] = df_enc[col].fillna('_MISSING_')
        le = LabelEncoder()
        df_enc[col] = le.fit_transform(df_enc[col].astype(str))
    for col in df_enc.select_dtypes(include=['number']).columns:
        df_enc[col] = df_enc[col].fillna(df_enc[col].median())
    # 正規化
    for col in df_enc.columns:
        col_range = df_enc[col].max() - df_enc[col].min()
        if col_range > 0:
            df_enc[col] = (df_enc[col] - df_enc[col].min()) / col_range
    return df_enc


def compute_privacy_metrics(real_df, synth_df):
    """プライバシーメトリクスの計算"""
    common_cols = sorted(set(real_df.columns) & set(synth_df.columns))
    real_sub = real_df[common_cols]
    synth_sub = synth_df[common_cols]

    real_enc = encode_for_distance(real_sub)
    synth_enc = encode_for_distance(synth_sub)

    # サンプリング（計算コスト削減）
    max_rows = 5000
    if len(real_enc) > max_rows:
        real_sample = real_enc.sample(max_rows, random_state=42)
    else:
        real_sample = real_enc
    if len(synth_enc) > max_rows:
        synth_sample = synth_enc.sample(max_rows, random_state=42)
    else:
        synth_sample = synth_enc

    # 1. DCR (Distance to Closest Record)
    nn = NearestNeighbors(n_neighbors=1, metric='euclidean', n_jobs=-1)
    nn.fit(real_sample.values)
    distances, _ = nn.kneighbors(synth_sample.values)
    dcr = distances.flatten()

    # 2. Exact Match Rate
    real_tuples = set(map(tuple, real_sub.fillna('_NA_').values))
    synth_tuples = list(map(tuple, synth_sub.fillna('_NA_').values))
    exact_matches = sum(1 for t in synth_tuples if t in real_tuples)
    exact_match_rate = exact_matches / len(synth_tuples)

    # 3. 5th percentile DCR
    dcr_5th = float(np.percentile(dcr, 5))

    return {
        'dcr_mean': round(float(np.mean(dcr)), 6),
        'dcr_median': round(float(np.median(dcr)), 6),
        'dcr_5th_percentile': round(dcr_5th, 6),
        'dcr_min': round(float(np.min(dcr)), 6),
        'exact_match_rate': round(exact_match_rate, 6),
        'exact_match_count': exact_matches,
        'sample_size_real': len(real_sample),
        'sample_size_synth': len(synth_sample),
    }


privacy_results = {}

for synth_file in sorted(glob.glob(os.path.join(OUTPUT_DIR, '*.csv'))):
    name = os.path.basename(synth_file).replace('.csv', '')
    print(f"Privacy eval: {name}")
    try:
        synth_df = pd.read_csv(synth_file)
        if set(synth_df.columns) != set(real_data.columns):
            privacy_results[name] = {'status': 'error', 'error': 'Column mismatch'}
            continue

        metrics = compute_privacy_metrics(real_data, synth_df)
        privacy_results[name] = metrics
        print(f"  DCR mean={metrics['dcr_mean']:.4f}, exact_match={metrics['exact_match_rate']:.4f}")
    except Exception as e:
        privacy_results[name] = {'status': 'error', 'error': str(e)}
        print(f"  ERROR: {e}")

with open(os.path.join(OUTPUT_DIR, 'privacy_eval.json'), 'w') as f:
    json.dump(privacy_results, f, indent=2)

print(f"\nPrivacy evaluation complete. {len(privacy_results)} models evaluated.")
