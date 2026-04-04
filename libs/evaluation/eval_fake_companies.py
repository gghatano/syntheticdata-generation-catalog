"""Issue #29: 企業マスタの品質評価（SDMetrics/TSTR/DCR）

実行: cd libs/evaluation && uv run python eval_fake_companies.py

特記: 極小規模データ（12行）のため、評価指標の信頼性に注意が必要
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
# 1. データ準備
# ============================================================
RAW_CSV = os.path.join(ROOT, 'data/raw/d_fake_companies.csv')
SYNTH_GC = os.path.join(OUTPUT_DIR, 'sdv_gaussiancopula_fake_companies.csv')

if not os.path.exists(RAW_CSV) or not os.path.exists(SYNTH_GC):
    print("Fake Companies data not found. Generating via SDV download_demo...")
    from sdv.datasets.demo import download_demo
    from sdv.single_table import GaussianCopulaSynthesizer
    import sdv

    fc_data, fc_meta = download_demo(modality='single_table', dataset_name='fake_companies')
    fc_data.to_csv(RAW_CSV, index=False)
    meta_json_path = os.path.join(ROOT, 'data/raw/d_fake_companies_metadata.json')
    with open(meta_json_path, 'w') as f:
        json.dump(fc_meta.to_dict(), f, indent=2)
    print(f"  Downloaded: {len(fc_data)} rows, {len(fc_data.columns)} cols")

    gc = GaussianCopulaSynthesizer(fc_meta)
    gc.fit(fc_data)
    synth = gc.sample(num_rows=len(fc_data))
    synth.to_csv(SYNTH_GC, index=False)
    print(f"  GaussianCopula generated: {len(synth)} rows")
else:
    print("Fake Companies data found. Loading...")

real_data = pd.read_csv(RAW_CSV)
print(f"Real data: {len(real_data)} rows, {len(real_data.columns)} cols")
print(f"WARNING: Only {len(real_data)} rows - evaluation metrics have limited reliability")

# メタデータ
meta_json_path = os.path.join(ROOT, 'data/raw/d_fake_companies_metadata.json')
if os.path.exists(meta_json_path):
    metadata_raw = json.load(open(meta_json_path))
else:
    # メタデータがなければ再生成
    from sdv.datasets.demo import download_demo
    _, fc_meta = download_demo(modality='single_table', dataset_name='fake_companies')
    metadata_raw = fc_meta.to_dict()
    with open(meta_json_path, 'w') as f:
        json.dump(metadata_raw, f, indent=2)

if 'tables' in metadata_raw:
    table_name = list(metadata_raw['tables'].keys())[0]
    metadata_dict = metadata_raw['tables'][table_name]
else:
    metadata_dict = metadata_raw

synth_files = {
    'sdv_gaussiancopula_fake_companies': SYNTH_GC,
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

# 極小データ（12行）のため TSTR は信頼性が低い
# ターゲット列を検出
TARGET = None
for candidate in ['type', 'category', 'label', 'class']:
    if candidate in real_data.columns:
        TARGET = candidate
        break
if TARGET is None:
    # 数値以外でユニーク数が少ない列をターゲットに
    for col in real_data.select_dtypes(include=['object']).columns:
        if 1 < real_data[col].nunique() < len(real_data):
            TARGET = col
            break
if TARGET is None:
    TARGET = real_data.columns[-1]

print(f"  Target column: {TARGET} (unique={real_data[TARGET].nunique()})")
print(f"  WARNING: {len(real_data)} rows is too small for reliable TSTR")


def encode_dataframe(df):
    df_enc = df.copy()
    for col in df_enc.select_dtypes(include=['bool']).columns:
        df_enc[col] = df_enc[col].astype(int)
    for col in df_enc.select_dtypes(include=['object', 'category']).columns:
        df_enc[col] = df_enc[col].fillna('_MISSING_')
    for col in df_enc.select_dtypes(include=['number']).columns:
        df_enc[col] = df_enc[col].fillna(df_enc[col].median())
    for col in df_enc.select_dtypes(include=['object', 'category']).columns:
        le = LabelEncoder()
        df_enc[col] = le.fit_transform(df_enc[col].astype(str))
    return df_enc


try:
    real_enc = encode_dataframe(real_data)
    X_real = real_enc.drop(columns=[TARGET])
    y_real = real_enc[TARGET]

    # 極小データのため test_size を大きめに（ただし最低2件は必要）
    test_size = max(2, int(len(real_data) * 0.3))
    if len(real_data) - test_size < 2:
        test_size = len(real_data) // 2

    X_train, X_test, y_train, y_test = train_test_split(
        X_real, y_real, test_size=test_size, random_state=RANDOM_SEED
    )

    clf_real = RandomForestClassifier(n_estimators=100, random_state=RANDOM_SEED, n_jobs=-1)
    clf_real.fit(X_train, y_train)
    baseline_acc = accuracy_score(y_test, clf_real.predict(X_test))
    baseline_f1 = f1_score(y_test, clf_real.predict(X_test), average='weighted')
    print(f"  Baseline TRTR: acc={baseline_acc:.4f}, f1={baseline_f1:.4f}")

    for name, path in synth_files.items():
        try:
            synth_df = pd.read_csv(path)
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
except Exception as e:
    print(f"  TSTR SKIP: {e}")

# ============================================================
# 4. DCR プライバシー評価
# ============================================================
print("\n=== DCR Privacy Evaluation ===")
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
        df_enc[col] = df_enc[col].fillna(df_enc[col].median())
    for col in df_enc.columns:
        df_enc[col] = pd.to_numeric(df_enc[col], errors='coerce').fillna(0)
        col_range = float(df_enc[col].max() - df_enc[col].min())
        if col_range > 0:
            df_enc[col] = (df_enc[col] - df_enc[col].min()) / col_range
    return df_enc


for name, path in synth_files.items():
    try:
        synth_df = pd.read_csv(path)
        common_cols = sorted(set(real_data.columns) & set(synth_df.columns))
        real_sub = real_data[common_cols]
        synth_sub = synth_df[common_cols]

        real_enc = encode_for_distance(real_sub)
        synth_enc = encode_for_distance(synth_sub)

        nn = NearestNeighbors(n_neighbors=1, metric='euclidean', n_jobs=-1)
        nn.fit(real_enc.values)
        distances, _ = nn.kneighbors(synth_enc.values)
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
eval_output = os.path.join(OUTPUT_DIR, 'fake_companies_eval.json')
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
    if case['id'] != 'company-directory':
        continue

    for r in case['results']:
        if r['algorithm_id'] == 'gaussiancopula' and r['library'] == 'SDV':
            m = results.get('sdv_gaussiancopula_fake_companies', {})
            r['metrics']['quality_score'] = round(m.get('quality_score', 0), 4) if m.get('quality_score') else None
            r['metrics']['tstr_accuracy'] = m.get('tstr_accuracy')
            r['metrics']['tstr_f1'] = m.get('tstr_f1')
            r['metrics']['dcr_mean'] = m.get('dcr_mean')
            r['privacy_risk'] = m.get('privacy_risk', 'unknown')

    m = results.get('sdv_gaussiancopula_fake_companies', {})
    qs = m.get('quality_score')
    pr = m.get('privacy_risk', '')
    parts = []
    if qs:
        parts.append(f"GaussianCopulaの品質スコアは{qs:.2f}。")
    parts.append(f"12行の極小データのため、評価指標の統計的信頼性は限定的。")
    if pr:
        parts.append(f"プライバシーリスクは{pr}。")
    parts.append("テスト環境用のダミーデータとしては十分な品質。少量データへの合成データ適用の参考事例。")
    case['recommendation'] = ' '.join(parts)
    print(f"  Updated recommendation: {case['recommendation']}")
    break

with open(cases_path, 'w') as f:
    json.dump(cases, f, indent=2, ensure_ascii=False)
print("experiment-cases.json updated.")

# サマリ
print("\n=== Summary ===")
for name, m in results.items():
    print(f"  {name}:")
    for k in ['quality_score', 'tstr_f1', 'dcr_mean', 'privacy_risk']:
        print(f"    {k}={m.get(k, 'N/A')}")
