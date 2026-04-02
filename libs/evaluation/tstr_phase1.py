"""Phase 1 TSTR 評価: 合成データで学習 → 実データでテスト"""
import pandas as pd
import json
import glob
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.preprocessing import LabelEncoder

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..', '..')
REAL_DATA_PATH = os.path.join(ROOT, 'data/processed/d1_adult.csv')
OUTPUT_DIR = os.path.join(ROOT, 'results/phase1')
RANDOM_SEED = 42

real_data = pd.read_csv(REAL_DATA_PATH)

# ターゲット列の自動検出
TARGET = None
for candidate in ['income', 'target', 'label', 'class']:
    if candidate in real_data.columns:
        TARGET = candidate
        break
if TARGET is None:
    TARGET = real_data.columns[-1]
print(f"Target column: {TARGET}")


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


# Real baseline (TRTR)
real_enc = encode_dataframe(real_data)
X_real = real_enc.drop(columns=[TARGET])
y_real = real_enc[TARGET]
X_train, X_test, y_train, y_test = train_test_split(
    X_real, y_real, test_size=0.2, random_state=RANDOM_SEED
)

clf_real = RandomForestClassifier(n_estimators=100, random_state=RANDOM_SEED, n_jobs=-1)
clf_real.fit(X_train, y_train)
baseline_acc = accuracy_score(y_test, clf_real.predict(X_test))
baseline_f1 = f1_score(y_test, clf_real.predict(X_test), average='weighted')

tstr_results = {
    'target_column': TARGET,
    'test_size': int(len(X_test)),
    'random_seed': RANDOM_SEED,
    'baseline_trtr': {'accuracy': round(baseline_acc, 4), 'f1': round(baseline_f1, 4)},
    'models': {}
}
print(f"Baseline TRTR: acc={baseline_acc:.4f}, f1={baseline_f1:.4f}")

# TSTR for each synthetic dataset
for synth_file in sorted(glob.glob(os.path.join(OUTPUT_DIR, '*.csv'))):
    name = os.path.basename(synth_file).replace('.csv', '')
    try:
        synth_df = pd.read_csv(synth_file)
        if set(synth_df.columns) != set(real_data.columns):
            tstr_results['models'][name] = {'status': 'error', 'error': 'Column mismatch'}
            continue

        synth_enc = encode_dataframe(synth_df)
        X_synth = synth_enc.drop(columns=[TARGET])
        y_synth = synth_enc[TARGET]

        clf = RandomForestClassifier(n_estimators=100, random_state=RANDOM_SEED, n_jobs=-1)
        clf.fit(X_synth, y_synth)
        acc = accuracy_score(y_test, clf.predict(X_test))
        f1 = f1_score(y_test, clf.predict(X_test), average='weighted')

        tstr_results['models'][name] = {'accuracy': round(acc, 4), 'f1': round(f1, 4)}
        print(f"{name}: acc={acc:.4f}, f1={f1:.4f}")
    except Exception as e:
        tstr_results['models'][name] = {'status': 'error', 'error': str(e)}
        print(f"{name}: ERROR - {e}")

with open(os.path.join(OUTPUT_DIR, 'tstr_results.json'), 'w') as f:
    json.dump(tstr_results, f, indent=2)

print("TSTR Phase1 complete.")
