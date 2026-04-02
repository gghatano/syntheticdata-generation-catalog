"""データセット準備スクリプト

SDV の demo データを取得し、全ライブラリ共通で使える形式に整える。
実行: cd libs/sdv && uv run python prepare_data.py
"""
import pandas as pd
import json
import os
import sys
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..', '..')
RAW_DIR = os.path.join(ROOT, 'data', 'raw')
PROC_DIR = os.path.join(ROOT, 'data', 'processed')
PROGRESS_FILE = os.path.join(ROOT, 'docs', 'tasks', 'progress.json')

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROC_DIR, exist_ok=True)


def update_progress(task_id, status, **kwargs):
    progress = {}
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            progress = json.load(f)
    if 'tasks' not in progress:
        progress['tasks'] = {}
    entry = {'status': status, 'updated_at': datetime.now().isoformat()}
    entry.update(kwargs)
    progress['tasks'][task_id] = entry
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)


def save_profile(df, path):
    """データプロファイルをJSONで保存"""
    profile = {
        'rows': len(df),
        'columns': len(df.columns),
        'column_names': list(df.columns),
        'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
        'missing_counts': {col: int(v) for col, v in df.isnull().sum().items()},
        'missing_rate': {col: round(float(v), 4) for col, v in (df.isnull().sum() / len(df)).items()},
        'numeric_stats': {},
    }
    for col in df.select_dtypes(include=['number']).columns:
        profile['numeric_stats'][col] = {
            'mean': round(float(df[col].mean()), 4),
            'std': round(float(df[col].std()), 4),
            'min': float(df[col].min()),
            'max': float(df[col].max()),
        }
    with open(path, 'w') as f:
        json.dump(profile, f, indent=2, default=str)


errors = []

# --- D1: 単一表データ ---
print("=== D1: 単一表データ (Adult) ===")
update_progress('01-data-preparation', 'in_progress', current_step='D1')
try:
    from sdv.datasets.demo import download_demo

    real_data, metadata = download_demo(modality='single_table', dataset_name='adult')
    real_data.to_csv(os.path.join(RAW_DIR, 'd1_adult.csv'), index=False)
    with open(os.path.join(RAW_DIR, 'd1_adult_metadata.json'), 'w') as f:
        json.dump(metadata.to_dict(), f, indent=2)

    real_data.to_csv(os.path.join(PROC_DIR, 'd1_adult.csv'), index=False)
    save_profile(real_data, os.path.join(PROC_DIR, 'd1_profile.json'))
    print(f"  OK: {len(real_data)} rows, {len(real_data.columns)} columns")
except Exception as e:
    print(f"  ERROR: {e}")
    errors.append(('D1', str(e)))

# --- D2: 複数表データ ---
print("=== D2: 複数表データ (fake_hotels) ===")
update_progress('01-data-preparation', 'in_progress', current_step='D2')
try:
    real_data, metadata = download_demo(modality='multi_table', dataset_name='fake_hotels')
    for table_name, df in real_data.items():
        df.to_csv(os.path.join(RAW_DIR, f'd2_{table_name}.csv'), index=False)
        df.to_csv(os.path.join(PROC_DIR, f'd2_{table_name}.csv'), index=False)
        save_profile(df, os.path.join(PROC_DIR, f'd2_{table_name}_profile.json'))
        print(f"  {table_name}: {len(df)} rows, {len(df.columns)} columns")
    with open(os.path.join(RAW_DIR, 'd2_metadata.json'), 'w') as f:
        json.dump(metadata.to_dict(), f, indent=2)
except Exception as e:
    print(f"  ERROR: {e}")
    errors.append(('D2', str(e)))

# --- D3: 時系列データ ---
print("=== D3: 時系列データ (nasdaq100_2019) ===")
update_progress('01-data-preparation', 'in_progress', current_step='D3')
try:
    real_data, metadata = download_demo(modality='sequential', dataset_name='nasdaq100_2019')
    real_data.to_csv(os.path.join(RAW_DIR, 'd3_nasdaq.csv'), index=False)
    with open(os.path.join(RAW_DIR, 'd3_nasdaq_metadata.json'), 'w') as f:
        json.dump(metadata.to_dict(), f, indent=2)

    real_data.to_csv(os.path.join(PROC_DIR, 'd3_nasdaq.csv'), index=False)
    save_profile(real_data, os.path.join(PROC_DIR, 'd3_profile.json'))
    print(f"  OK: {len(real_data)} rows, {len(real_data.columns)} columns")
except Exception as e:
    print(f"  ERROR: {e}")
    errors.append(('D3', str(e)))

# --- 健全性チェック ---
print("\n=== 健全性チェック ===")
required = {
    'D1': os.path.join(PROC_DIR, 'd1_adult.csv'),
    'D3': os.path.join(PROC_DIR, 'd3_nasdaq.csv'),
}
for label, path in required.items():
    exists = os.path.exists(path)
    rows = len(pd.read_csv(path)) if exists else 0
    status = f"OK ({rows} rows)" if exists and rows > 0 else "MISSING"
    print(f"  {label}: {status}")

d2_files = [f for f in os.listdir(PROC_DIR) if f.startswith('d2_') and f.endswith('.csv')]
print(f"  D2: {len(d2_files)} tables")
if len(d2_files) < 2:
    print("  WARNING: D2 が2テーブル未満")

# --- 結果記録 ---
if errors:
    update_progress('01-data-preparation', 'error', errors=errors)
    print(f"\nCompleted with {len(errors)} error(s)")
    sys.exit(1)
else:
    update_progress('01-data-preparation', 'completed')
    print("\nAll datasets prepared successfully.")
