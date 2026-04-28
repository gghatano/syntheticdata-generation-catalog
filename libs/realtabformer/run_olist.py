"""REaLTabFormer による Olist 親子テーブル合成。

REaLTabFormer は1親-1子の関係のみサポートするため、
Olist の主要関係 (orders → order_items) を対象に学習する。

CPU 環境では学習が非常に遅いため、サブサンプリング + 少エポックで実行する。
学習が完了しない場合はその旨を結果に記録して終了する。

実行: cd libs/realtabformer && uv run python run_olist.py
"""
import json
import os
import platform
import shutil
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..', '..')
PROC_DIR = os.path.join(ROOT, 'data', 'processed', 'olist')
OUTPUT_DIR = os.path.join(ROOT, 'results', 'phase2_olist')
PROGRESS_FILE = os.path.join(ROOT, 'docs', 'tasks', 'progress.json')
MODEL_DIR = os.path.join(BASE, 'models')
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

# 設定: CPU で動かすために大幅に縮小
SAMPLE_ORDERS = 800
PARENT_EPOCHS = 30
CHILD_EPOCHS = 30
RANDOM_SEED = 42


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


def main():
    update_progress('issue-65-realtabformer', 'in_progress')

    import realtabformer
    import torch
    from realtabformer import REaLTabFormer

    env = {
        'python_version': platform.python_version(),
        'realtabformer_version': getattr(realtabformer, '__version__', 'unknown'),
        'torch_version': torch.__version__,
        'cuda_available': torch.cuda.is_available(),
        'timestamp': datetime.now().isoformat(),
    }

    # parent: orders, child: order_items を中心に
    orders_df = pd.read_csv(os.path.join(PROC_DIR, 'orders.csv'))
    items_df = pd.read_csv(os.path.join(PROC_DIR, 'order_items.csv'))

    # サブサンプリング（CPU 学習用）
    orders_sub = orders_df.sample(n=min(SAMPLE_ORDERS, len(orders_df)), random_state=RANDOM_SEED)
    order_ids = set(orders_sub['order_id'])
    items_sub = items_df[items_df['order_id'].isin(order_ids)]

    print(f"sub orders: {len(orders_sub)}, sub items: {len(items_sub)}")

    # 親に必要な列のみ（id, customer_id を除外して合成対象を絞る）
    # join_key として order_id を残す
    parent_features = orders_sub[['order_id', 'order_status']].copy()

    # 子は order_id（join_key） + 数値列
    child_features = items_sub[['order_id', 'order_item_id', 'price', 'freight_value']].copy()

    join_key = 'order_id'

    results = {'_env': env, 'config': {
        'sample_orders': SAMPLE_ORDERS,
        'parent_epochs': PARENT_EPOCHS,
        'child_epochs': CHILD_EPOCHS,
        'parent_features': list(parent_features.columns),
        'child_features': list(child_features.columns),
        'random_seed': RANDOM_SEED,
    }}

    # parent モデルの保存先（既存があれば消す）
    parent_dir = os.path.join(MODEL_DIR, 'rtf_parent')
    if os.path.exists(parent_dir):
        shutil.rmtree(parent_dir)
    os.makedirs(parent_dir, exist_ok=True)

    try:
        print("\n=== 親モデル (orders) 学習 ===")
        fit_p_start = time.time()
        parent_model = REaLTabFormer(
            model_type='tabular',
            epochs=PARENT_EPOCHS,
            batch_size=8,
            random_state=RANDOM_SEED,
            train_size=1.0,
        )
        parent_model.fit(parent_features.drop(join_key, axis=1), n_critic=0)
        fit_p_elapsed = time.time() - fit_p_start
        print(f"  親学習時間: {fit_p_elapsed:.1f}s")

        # rtf 0.2.4 の save() バグ: full_save_dir (Path) を JSON dumps できない
        # save() は checkpoints_dir / samples_save_dir のみ as_posix 変換するため
        # full_save_dir を手動で文字列化する。
        if isinstance(getattr(parent_model, 'full_save_dir', None), Path):
            parent_model.full_save_dir = parent_model.full_save_dir.as_posix()
        parent_model.save(parent_dir)
        # 最新サブディレクトリを取得
        parent_path = sorted(
            [p for p in Path(parent_dir).glob('id*') if p.is_dir()],
            key=lambda p: p.stat().st_mtime,
        )[-1]
        print(f"  parent_path: {parent_path}")

        print("\n=== 子モデル (order_items) 学習 ===")
        fit_c_start = time.time()
        child_model = REaLTabFormer(
            model_type='relational',
            parent_realtabformer_path=parent_path,
            output_max_length=None,
            train_size=1.0,
            epochs=CHILD_EPOCHS,
            batch_size=8,
            random_state=RANDOM_SEED,
        )
        child_model.fit(
            df=child_features,
            in_df=parent_features,
            join_on=join_key,
        )
        fit_c_elapsed = time.time() - fit_c_start
        print(f"  子学習時間: {fit_c_elapsed:.1f}s")

        print("\n=== サンプリング ===")
        sample_start = time.time()
        n_parent = len(parent_features)
        parent_synth = parent_model.sample(n_parent)
        parent_synth.index.name = join_key
        parent_synth = parent_synth.reset_index()

        # join_key は親モデルから生成された連番。子サンプリングに渡す。
        child_synth = child_model.sample(
            input_unique_ids=parent_synth[join_key],
            input_df=parent_synth.drop(join_key, axis=1),
            gen_batch=32,
        )
        sample_elapsed = time.time() - sample_start
        print(f"  生成時間: {sample_elapsed:.1f}s")

        # 保存
        parent_synth.to_csv(os.path.join(OUTPUT_DIR, 'realtabformer_orders.csv'), index=False)
        child_synth.to_csv(os.path.join(OUTPUT_DIR, 'realtabformer_order_items.csv'), index=False)

        results['realtabformer'] = {
            'status': 'ok',
            'fit_parent_time_sec': round(fit_p_elapsed, 2),
            'fit_child_time_sec': round(fit_c_elapsed, 2),
            'sample_time_sec': round(sample_elapsed, 2),
            'time_sec': round(fit_p_elapsed + fit_c_elapsed + sample_elapsed, 2),
            'tables': {
                'orders': len(parent_synth),
                'order_items': len(child_synth),
            },
            'dataset': 'olist',
            'model': 'REaLTabFormer',
            'note': 'Sub-sampled and reduced epochs due to CPU-only environment. Only orders→order_items relation modeled.',
        }
        print(f"\n親 {len(parent_synth)} 行 / 子 {len(child_synth)} 行を生成")

    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()
        results['realtabformer'] = {
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc(),
            'dataset': 'olist',
        }

    with open(os.path.join(OUTPUT_DIR, 'realtabformer_run_log.json'), 'w') as f:
        json.dump(results, f, indent=2, default=str)

    update_progress(
        'issue-65-realtabformer',
        'completed' if results.get('realtabformer', {}).get('status') == 'ok' else 'error',
    )
    print("\nREaLTabFormer Olist 完了。")


if __name__ == '__main__':
    main()
