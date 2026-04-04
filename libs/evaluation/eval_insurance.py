"""Issue #27: 保険契約データの品質評価（SDMetrics/TSTR/DCR）

実行: cd libs/evaluation && uv run python eval_insurance.py

前提: libs/sdv/ で run_additional_experiments.py を実行済み
（Insurance の合成データCSVが results/phase1/ に存在すること）
もし存在しなければ、SDV の download_demo で再生成する。
"""
import pandas as pd
import numpy as np
import json
import os
import sys
import traceback

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..', '..')
OUTPUT_DIR = os.path.join(ROOT, 'results/phase1')
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.join(ROOT, 'data/raw'), exist_ok=True)

RANDOM_SEED = 42

# ============================================================
# 1. データ準備: Insurance データをダウンロードまたはロード
# ============================================================
RAW_CSV = os.path.join(ROOT, 'data/raw/d_insurance.csv')
META_JSON = os.path.join(ROOT, 'data/raw/d_insurance_metadata.json')
SYNTH_GC = os.path.join(OUTPUT_DIR, 'sdv_gaussiancopula_insurance.csv')
SYNTH_CTGAN = os.path.join(OUTPUT_DIR, 'sdv_ctgan_50ep_insurance.csv')

# データがなければ再生成
if not os.path.exists(RAW_CSV) or not os.path.exists(SYNTH_GC):
    print("Insurance data not found. Generating via SDV download_demo...")
    sys.path.insert(0, os.path.join(ROOT, 'libs'))

    from sdv.datasets.demo import download_demo
    from sdv.single_table import GaussianCopulaSynthesizer, CTGANSynthesizer
    import sdv

    ins_data, ins_meta = download_demo(modality='single_table', dataset_name='insurance')
    ins_data.to_csv(RAW_CSV, index=False)
    with open(META_JSON, 'w') as f:
        json.dump(ins_meta.to_dict(), f, indent=2)
    print(f"  Downloaded: {len(ins_data)} rows, {len(ins_data.columns)} cols")

    # GaussianCopula
    gc = GaussianCopulaSynthesizer(ins_meta)
    gc.fit(ins_data)
    synth_gc = gc.sample(num_rows=len(ins_data))
    synth_gc.to_csv(SYNTH_GC, index=False)
    print(f"  GaussianCopula generated: {len(synth_gc)} rows")

    # CTGAN 50ep
    ctgan = CTGANSynthesizer(ins_meta, epochs=50)
    ctgan.fit(ins_data)
    synth_ctgan = ctgan.sample(num_rows=len(ins_data))
    synth_ctgan.to_csv(SYNTH_CTGAN, index=False)
    print(f"  CTGAN 50ep generated: {len(synth_ctgan)} rows")
else:
    print("Insurance data found. Loading...")

real_data = pd.read_csv(RAW_CSV)
print(f"Real data: {len(real_data)} rows, {len(real_data.columns)} cols")

# メタデータ読み込み
metadata_raw = json.load(open(META_JSON))
if 'tables' in metadata_raw:
    table_name = list(metadata_raw['tables'].keys())[0]
    metadata_dict = metadata_raw['tables'][table_name]
else:
    metadata_dict = metadata_raw

# 評価対象
synth_files = {
    'sdv_gaussiancopula_insurance': SYNTH_GC,
    'sdv_ctgan_50ep_insurance': SYNTH_CTGAN,
}

results = {}

# ============================================================
# 2. SDMetrics 評価
# ============================================================
print("\n=== SDMetrics Evaluation ===")
from sdmetrics.reports.single_table import QualityReport, DiagnosticReport

for name, path in synth_files.items():
    try:
        synth = pd.read_csv(path)
        quality = QualityReport()
        quality.generate(real_data, synth, metadata_dict)
        diag = DiagnosticReport()
        diag.generate(real_data, synth, metadata_dict)

        results.setdefault(name, {})['quality_score'] = quality.get_score()
        results[name]['diagnostic_score'] = diag.get_score()
        print(f"  {name}: quality={quality.get_score():.4f}, diagnostic={diag.get_score():.4f}")
    except Exception as e:
        print(f"  {name}: SDMetrics ERROR - {e}")
        traceback.print_exc()

# ============================================================
# 3. TSTR 評価
# ============================================================
print("\n=== TSTR Evaluation ===")
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.preprocessing import LabelEncoder


def encode_dataframe(df):
    df_enc = df.copy()
    for col in df_enc.select_dtypes(include=['object', 'category']).columns:
        df_enc[col] = df_enc[col].fillna('_MISSING_')
    for col in df_enc.select_dtypes(include=['number']).columns:
        df_enc[col] = df_enc[col].fillna(df_enc[col].median())
    for col in df_enc.select_dtypes(include=['object', 'category']).columns:
        le = LabelEncoder()
        df_enc[col] = le.fit_transform(df_enc[col].astype(str))
    return df_enc


# ターゲット列の検出 — Insurance データでは回帰タスク(charges)が自然
# ただし TSTR は分類タスクで行うため、charges を 中央値で2値化
TARGET = None
# 明示的な分類列がないため、charges を中央値で二値化
if 'charges' in real_data.columns:
    TARGET = 'charges_bin'
    median_charges = real_data['charges'].median()
    real_data['charges_bin'] = (real_data['charges'] > median_charges).astype(int)
    real_data_tstr = real_data.drop(columns=['charges'])
else:
    # fallback: 最終列をターゲットに
    TARGET = real_data.columns[-1]
    real_data_tstr = real_data.copy()

real_enc = encode_dataframe(real_data_tstr)
X_real = real_enc.drop(columns=[TARGET])
y_real = real_enc[TARGET]
X_train, X_test, y_train, y_test = train_test_split(
    X_real, y_real, test_size=0.2, random_state=RANDOM_SEED
)

clf_real = RandomForestClassifier(n_estimators=100, random_state=RANDOM_SEED, n_jobs=-1)
clf_real.fit(X_train, y_train)
baseline_acc = accuracy_score(y_test, clf_real.predict(X_test))
baseline_f1 = f1_score(y_test, clf_real.predict(X_test), average='weighted')
print(f"  Baseline TRTR: acc={baseline_acc:.4f}, f1={baseline_f1:.4f}")

tstr_info = {
    'target_column': TARGET,
    'baseline_trtr': {'accuracy': round(baseline_acc, 4), 'f1': round(baseline_f1, 4)},
}

for name, path in synth_files.items():
    try:
        synth_df = pd.read_csv(path)
        if 'charges' in synth_df.columns:
            synth_df['charges_bin'] = (synth_df['charges'] > median_charges).astype(int)
            synth_df = synth_df.drop(columns=['charges'])

        synth_enc = encode_dataframe(synth_df)
        X_synth = synth_enc.drop(columns=[TARGET])
        y_synth = synth_enc[TARGET]

        clf = RandomForestClassifier(n_estimators=100, random_state=RANDOM_SEED, n_jobs=-1)
        clf.fit(X_synth, y_synth)
        acc = accuracy_score(y_test, clf.predict(X_test))
        f1 = f1_score(y_test, clf.predict(X_test), average='weighted')

        results.setdefault(name, {})['tstr_accuracy'] = round(acc, 4)
        results[name]['tstr_f1'] = round(f1, 4)
        print(f"  {name}: acc={acc:.4f}, f1={f1:.4f}")
    except Exception as e:
        print(f"  {name}: TSTR ERROR - {e}")
        traceback.print_exc()

# ============================================================
# 4. DCR プライバシー評価
# ============================================================
print("\n=== DCR Privacy Evaluation ===")
from sklearn.neighbors import NearestNeighbors


def encode_for_distance(df):
    df_enc = df.copy()
    # bool列を int に変換
    for col in df_enc.select_dtypes(include=['bool']).columns:
        df_enc[col] = df_enc[col].astype(int)
    for col in df_enc.select_dtypes(include=['object', 'category']).columns:
        df_enc[col] = df_enc[col].fillna('_MISSING_')
        le = LabelEncoder()
        df_enc[col] = le.fit_transform(df_enc[col].astype(str))
    for col in df_enc.select_dtypes(include=['number']).columns:
        df_enc[col] = df_enc[col].fillna(df_enc[col].median())
    for col in df_enc.columns:
        df_enc[col] = pd.to_numeric(df_enc[col], errors='coerce').fillna(0)
        col_range = float(df_enc[col].max() - df_enc[col].min())
        if col_range > 0:
            df_enc[col] = (df_enc[col] - df_enc[col].min()) / col_range
    return df_enc


# 元データ（charges_bin を除いた状態で評価）
real_orig = pd.read_csv(RAW_CSV)

for name, path in synth_files.items():
    try:
        synth_df = pd.read_csv(path)
        common_cols = sorted(set(real_orig.columns) & set(synth_df.columns))
        real_sub = real_orig[common_cols]
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

        real_tuples = set(map(tuple, real_sub.fillna('_NA_').values))
        synth_tuples = list(map(tuple, synth_sub.fillna('_NA_').values))
        exact_matches = sum(1 for t in synth_tuples if t in real_tuples)

        results.setdefault(name, {})['dcr_mean'] = round(float(np.mean(dcr)), 6)
        results[name]['dcr_median'] = round(float(np.median(dcr)), 6)
        results[name]['dcr_5th_percentile'] = round(float(np.percentile(dcr, 5)), 6)
        results[name]['dcr_min'] = round(float(np.min(dcr)), 6)
        results[name]['exact_match_rate'] = round(exact_matches / len(synth_tuples), 6)
        results[name]['exact_match_count'] = exact_matches

        print(f"  {name}: dcr_mean={results[name]['dcr_mean']:.4f}, exact_match={results[name]['exact_match_rate']:.4f}")
    except Exception as e:
        print(f"  {name}: DCR ERROR - {e}")
        traceback.print_exc()

# ============================================================
# 5. privacy_risk 判定
# ============================================================
for name in results:
    dcr_mean = results[name].get('dcr_mean')
    exact_rate = results[name].get('exact_match_rate', 0)
    if dcr_mean is None:
        results[name]['privacy_risk'] = 'unknown'
    elif exact_rate > 0.01 or dcr_mean < 0.1:
        results[name]['privacy_risk'] = 'high'
    elif dcr_mean < 0.3:
        results[name]['privacy_risk'] = 'medium'
    else:
        results[name]['privacy_risk'] = 'low'

# ============================================================
# 6. 結果保存
# ============================================================
eval_output = os.path.join(OUTPUT_DIR, 'insurance_eval.json')
with open(eval_output, 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to {eval_output}")

# ============================================================
# 7. experiment-cases.json 更新
# ============================================================
print("\n=== Updating experiment-cases.json ===")
cases_path = os.path.join(ROOT, 'docs/catalog/public/data/experiment-cases.json')
with open(cases_path) as f:
    cases = json.load(f)

for case in cases:
    if case['id'] != 'insurance-risk-modeling':
        continue

    for r in case['results']:
        # GaussianCopula
        if r['algorithm_id'] == 'gaussiancopula' and r['library'] == 'SDV':
            m = results.get('sdv_gaussiancopula_insurance', {})
            r['metrics']['quality_score'] = round(m.get('quality_score', 0), 4) if m.get('quality_score') else None
            r['metrics']['tstr_accuracy'] = m.get('tstr_accuracy')
            r['metrics']['tstr_f1'] = m.get('tstr_f1')
            r['metrics']['dcr_mean'] = m.get('dcr_mean')
            r['privacy_risk'] = m.get('privacy_risk', 'unknown')
        # CTGAN 50ep
        elif r['algorithm_id'] == 'ctgan' and r['library'] == 'SDV':
            m = results.get('sdv_ctgan_50ep_insurance', {})
            r['metrics']['quality_score'] = round(m.get('quality_score', 0), 4) if m.get('quality_score') else None
            r['metrics']['tstr_accuracy'] = m.get('tstr_accuracy')
            r['metrics']['tstr_f1'] = m.get('tstr_f1')
            r['metrics']['dcr_mean'] = m.get('dcr_mean')
            r['privacy_risk'] = m.get('privacy_risk', 'unknown')

    # recommendation 更新
    gc_qs = results.get('sdv_gaussiancopula_insurance', {}).get('quality_score')
    ct_qs = results.get('sdv_ctgan_50ep_insurance', {}).get('quality_score')
    gc_f1 = results.get('sdv_gaussiancopula_insurance', {}).get('tstr_f1')
    ct_f1 = results.get('sdv_ctgan_50ep_insurance', {}).get('tstr_f1')
    gc_pr = results.get('sdv_gaussiancopula_insurance', {}).get('privacy_risk', '')
    ct_pr = results.get('sdv_ctgan_50ep_insurance', {}).get('privacy_risk', '')

    parts = []
    if gc_qs and ct_qs:
        if gc_qs > ct_qs:
            parts.append(f"GaussianCopulaが品質スコア{gc_qs:.2f}でCTGAN({ct_qs:.2f})を上回る。")
        else:
            parts.append(f"CTGANが品質スコア{ct_qs:.2f}でGaussianCopula({gc_qs:.2f})を上回る。")
    if gc_f1 and ct_f1:
        parts.append(f"TSTR F1はGC={gc_f1:.4f}, CTGAN={ct_f1:.4f}。")
    if gc_pr or ct_pr:
        parts.append(f"プライバシーリスクはGC={gc_pr}, CTGAN={ct_pr}。")
    parts.append("保険料（charges）が連続値のため、回帰タスクでの評価も検討の余地あり。")

    case['recommendation'] = ' '.join(parts)
    print(f"  Updated recommendation: {case['recommendation']}")
    break

with open(cases_path, 'w') as f:
    json.dump(cases, f, indent=2, ensure_ascii=False)
print("experiment-cases.json updated.")

# サマリ出力
print("\n=== Summary ===")
for name, m in results.items():
    print(f"  {name}:")
    print(f"    quality={m.get('quality_score', 'N/A')}")
    print(f"    tstr_f1={m.get('tstr_f1', 'N/A')}")
    print(f"    dcr_mean={m.get('dcr_mean', 'N/A')}")
    print(f"    privacy_risk={m.get('privacy_risk', 'N/A')}")
