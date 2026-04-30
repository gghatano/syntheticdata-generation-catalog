"""Olist (Brazilian E-Commerce) データセット取得・前処理

kagglehub から Olist データを取得し、FK 整合性を維持したサンプリングと
PK/FK 定義（SDV multi-table 形式）を出力する。

実行: cd libs/sdv && uv run python prepare_olist.py
"""
import json
import os
import shutil
import sys
import traceback
from datetime import datetime

import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..', '..')
RAW_DIR = os.path.join(ROOT, 'data', 'raw', 'olist')
PROC_DIR = os.path.join(ROOT, 'data', 'processed', 'olist')
PROGRESS_FILE = os.path.join(ROOT, 'docs', 'tasks', 'progress.json')

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROC_DIR, exist_ok=True)

RANDOM_SEED = 42
TARGET_ORDERS = 5000  # 初期検証用サンプリング件数（orders 起点）


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
    profile = {
        'rows': len(df),
        'columns': len(df.columns),
        'column_names': list(df.columns),
        'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
        'missing_counts': {col: int(v) for col, v in df.isnull().sum().items()},
    }
    with open(path, 'w') as f:
        json.dump(profile, f, indent=2, default=str)


def download_olist():
    """kagglehub で Olist を取得。既に DL 済みなら再利用。"""
    print("=== Olist ダウンロード ===")
    expected_files = ['olist_customers_dataset.csv', 'olist_orders_dataset.csv']
    if all(os.path.exists(os.path.join(RAW_DIR, f)) for f in expected_files):
        print(f"  既に取得済み: {RAW_DIR}")
        return RAW_DIR

    import kagglehub
    path = kagglehub.dataset_download("olistbr/brazilian-ecommerce")
    print(f"  kagglehub path: {path}")

    for fname in os.listdir(path):
        if fname.endswith('.csv'):
            src = os.path.join(path, fname)
            dst = os.path.join(RAW_DIR, fname)
            if not os.path.exists(dst):
                shutil.copy(src, dst)
    print(f"  raw データ配置: {RAW_DIR}")
    return RAW_DIR


def load_tables(raw_dir):
    """Olist のテーブルを読み込む。geolocation は除外、reviews のテキストは短縮。"""
    print("=== テーブル読み込み ===")
    tables = {
        'customers': pd.read_csv(os.path.join(raw_dir, 'olist_customers_dataset.csv')),
        'orders': pd.read_csv(os.path.join(raw_dir, 'olist_orders_dataset.csv')),
        'order_items': pd.read_csv(os.path.join(raw_dir, 'olist_order_items_dataset.csv')),
        'order_payments': pd.read_csv(os.path.join(raw_dir, 'olist_order_payments_dataset.csv')),
        'order_reviews': pd.read_csv(os.path.join(raw_dir, 'olist_order_reviews_dataset.csv')),
        'products': pd.read_csv(os.path.join(raw_dir, 'olist_products_dataset.csv')),
        'sellers': pd.read_csv(os.path.join(raw_dir, 'olist_sellers_dataset.csv')),
    }
    for name, df in tables.items():
        print(f"  {name}: {len(df)} rows, {len(df.columns)} cols")
    return tables


def sample_with_fk_integrity(tables, target_orders=TARGET_ORDERS, seed=RANDOM_SEED):
    """orders を起点に、FK で繋がる行のみを抽出して整合性を維持。"""
    print(f"=== サンプリング（orders {target_orders} 件起点）===")
    sampled = {}

    # 1. orders をサンプリング
    orders = tables['orders'].sample(n=min(target_orders, len(tables['orders'])), random_state=seed)
    sampled['orders'] = orders.copy()
    customer_ids = set(orders['customer_id'])
    order_ids = set(orders['order_id'])

    # 2. customers: orders から参照される customer_id のみ
    customers = tables['customers'][tables['customers']['customer_id'].isin(customer_ids)]
    sampled['customers'] = customers.copy()

    # 3. order_items: orders から参照される order_id のみ
    order_items = tables['order_items'][tables['order_items']['order_id'].isin(order_ids)]
    sampled['order_items'] = order_items.copy()
    product_ids = set(order_items['product_id'])
    seller_ids = set(order_items['seller_id'])

    # 4. order_payments
    payments = tables['order_payments'][tables['order_payments']['order_id'].isin(order_ids)]
    sampled['order_payments'] = payments.copy()

    # 5. order_reviews
    reviews = tables['order_reviews'][tables['order_reviews']['order_id'].isin(order_ids)]
    sampled['order_reviews'] = reviews.copy()

    # 6. products: order_items から参照されるもの
    products = tables['products'][tables['products']['product_id'].isin(product_ids)]
    sampled['products'] = products.copy()

    # 7. sellers: order_items から参照されるもの
    sellers = tables['sellers'][tables['sellers']['seller_id'].isin(seller_ids)]
    sampled['sellers'] = sellers.copy()

    for name, df in sampled.items():
        print(f"  {name}: {len(df)} rows")
    return sampled


def clean_for_synthesis(tables):
    """合成データ生成用の整形。日付変換・テキスト除外・カテゴリ整理。"""
    print("=== 整形 ===")

    # orders: 日付を datetime に
    orders = tables['orders'].copy()
    date_cols = [
        'order_purchase_timestamp', 'order_approved_at',
        'order_delivered_carrier_date', 'order_delivered_customer_date',
        'order_estimated_delivery_date',
    ]
    for col in date_cols:
        orders[col] = pd.to_datetime(orders[col], errors='coerce')
    tables['orders'] = orders

    # order_items: shipping_limit_date
    oi = tables['order_items'].copy()
    oi['shipping_limit_date'] = pd.to_datetime(oi['shipping_limit_date'], errors='coerce')
    tables['order_items'] = oi

    # order_reviews: テキスト列は除外（合成対象外、評価のみ残す）
    rv = tables['order_reviews'].copy()
    drop_cols = [c for c in ['review_comment_title', 'review_comment_message'] if c in rv.columns]
    rv = rv.drop(columns=drop_cols)
    rv['review_creation_date'] = pd.to_datetime(rv['review_creation_date'], errors='coerce')
    rv['review_answer_timestamp'] = pd.to_datetime(rv['review_answer_timestamp'], errors='coerce')
    tables['order_reviews'] = rv

    # products: テキスト系の name を除外（lengthのみ残す）
    pr = tables['products'].copy()
    if 'product_category_name' in pr.columns:
        # カテゴリは欠損を 'unknown' に
        pr['product_category_name'] = pr['product_category_name'].fillna('unknown')
    # 数値欠損は中央値補完
    for col in pr.select_dtypes(include='number').columns:
        if pr[col].isnull().any():
            pr[col] = pr[col].fillna(pr[col].median())
    tables['products'] = pr

    # 重複除去（PK の重複があれば）
    for name, pk in [
        ('customers', 'customer_id'),
        ('orders', 'order_id'),
        ('products', 'product_id'),
        ('sellers', 'seller_id'),
    ]:
        before = len(tables[name])
        tables[name] = tables[name].drop_duplicates(subset=[pk])
        if len(tables[name]) != before:
            print(f"  {name}: 重複除去 {before} -> {len(tables[name])}")

    # order_reviews の review_id 重複を除去
    if 'review_id' in tables['order_reviews'].columns:
        tables['order_reviews'] = tables['order_reviews'].drop_duplicates(subset=['review_id'])

    return tables


def build_metadata():
    """SDV multi-table の metadata 辞書を構築。"""
    metadata = {
        'METADATA_SPEC_VERSION': 'V1',
        'tables': {
            'customers': {
                'primary_key': 'customer_id',
                'columns': {
                    'customer_id': {'sdtype': 'id'},
                    'customer_unique_id': {'sdtype': 'id'},
                    'customer_zip_code_prefix': {'sdtype': 'categorical'},
                    'customer_city': {'sdtype': 'categorical'},
                    'customer_state': {'sdtype': 'categorical'},
                },
            },
            'orders': {
                'primary_key': 'order_id',
                'columns': {
                    'order_id': {'sdtype': 'id'},
                    'customer_id': {'sdtype': 'id'},
                    'order_status': {'sdtype': 'categorical'},
                    'order_purchase_timestamp': {'sdtype': 'datetime'},
                    'order_approved_at': {'sdtype': 'datetime'},
                    'order_delivered_carrier_date': {'sdtype': 'datetime'},
                    'order_delivered_customer_date': {'sdtype': 'datetime'},
                    'order_estimated_delivery_date': {'sdtype': 'datetime'},
                },
            },
            'order_items': {
                'columns': {
                    'order_id': {'sdtype': 'id'},
                    'order_item_id': {'sdtype': 'numerical'},
                    'product_id': {'sdtype': 'id'},
                    'seller_id': {'sdtype': 'id'},
                    'shipping_limit_date': {'sdtype': 'datetime'},
                    'price': {'sdtype': 'numerical'},
                    'freight_value': {'sdtype': 'numerical'},
                },
            },
            'order_payments': {
                'columns': {
                    'order_id': {'sdtype': 'id'},
                    'payment_sequential': {'sdtype': 'numerical'},
                    'payment_type': {'sdtype': 'categorical'},
                    'payment_installments': {'sdtype': 'numerical'},
                    'payment_value': {'sdtype': 'numerical'},
                },
            },
            'order_reviews': {
                'primary_key': 'review_id',
                'columns': {
                    'review_id': {'sdtype': 'id'},
                    'order_id': {'sdtype': 'id'},
                    'review_score': {'sdtype': 'numerical'},
                    'review_creation_date': {'sdtype': 'datetime'},
                    'review_answer_timestamp': {'sdtype': 'datetime'},
                },
            },
            'products': {
                'primary_key': 'product_id',
                'columns': {
                    'product_id': {'sdtype': 'id'},
                    'product_category_name': {'sdtype': 'categorical'},
                    'product_name_lenght': {'sdtype': 'numerical'},
                    'product_description_lenght': {'sdtype': 'numerical'},
                    'product_photos_qty': {'sdtype': 'numerical'},
                    'product_weight_g': {'sdtype': 'numerical'},
                    'product_length_cm': {'sdtype': 'numerical'},
                    'product_height_cm': {'sdtype': 'numerical'},
                    'product_width_cm': {'sdtype': 'numerical'},
                },
            },
            'sellers': {
                'primary_key': 'seller_id',
                'columns': {
                    'seller_id': {'sdtype': 'id'},
                    'seller_zip_code_prefix': {'sdtype': 'categorical'},
                    'seller_city': {'sdtype': 'categorical'},
                    'seller_state': {'sdtype': 'categorical'},
                },
            },
        },
        'relationships': [
            {
                'parent_table_name': 'customers',
                'parent_primary_key': 'customer_id',
                'child_table_name': 'orders',
                'child_foreign_key': 'customer_id',
            },
            {
                'parent_table_name': 'orders',
                'parent_primary_key': 'order_id',
                'child_table_name': 'order_items',
                'child_foreign_key': 'order_id',
            },
            {
                'parent_table_name': 'orders',
                'parent_primary_key': 'order_id',
                'child_table_name': 'order_payments',
                'child_foreign_key': 'order_id',
            },
            {
                'parent_table_name': 'orders',
                'parent_primary_key': 'order_id',
                'child_table_name': 'order_reviews',
                'child_foreign_key': 'order_id',
            },
            {
                'parent_table_name': 'products',
                'parent_primary_key': 'product_id',
                'child_table_name': 'order_items',
                'child_foreign_key': 'product_id',
            },
            {
                'parent_table_name': 'sellers',
                'parent_primary_key': 'seller_id',
                'child_table_name': 'order_items',
                'child_foreign_key': 'seller_id',
            },
        ],
    }
    return metadata


def keep_metadata_columns(tables, metadata):
    """metadata に定義された列のみを残す。"""
    for tname, tdef in metadata['tables'].items():
        if tname not in tables:
            continue
        keep = [c for c in tdef['columns'].keys() if c in tables[tname].columns]
        tables[tname] = tables[tname][keep]
    return tables


def verify_fk_integrity(tables, metadata):
    """FK 整合性チェック。"""
    print("=== FK 整合性チェック ===")
    issues = []
    for rel in metadata['relationships']:
        parent = tables[rel['parent_table_name']]
        child = tables[rel['child_table_name']]
        pk = rel['parent_primary_key']
        fk = rel['child_foreign_key']
        parent_set = set(parent[pk])
        child_fks = child[fk].dropna()
        orphans = (~child_fks.isin(parent_set)).sum()
        rate = orphans / max(len(child_fks), 1)
        marker = 'OK' if orphans == 0 else 'WARN'
        msg = f"  [{marker}] {rel['parent_table_name']}->{rel['child_table_name']}: orphans={orphans} ({rate:.4f})"
        print(msg)
        if orphans > 0:
            issues.append((rel, int(orphans)))
    return issues


def main():
    update_progress('issue-65-data-prep', 'in_progress')
    try:
        download_olist()
        tables = load_tables(RAW_DIR)
        sampled = sample_with_fk_integrity(tables)
        cleaned = clean_for_synthesis(sampled)
        metadata = build_metadata()
        cleaned = keep_metadata_columns(cleaned, metadata)
        verify_fk_integrity(cleaned, metadata)

        # 保存
        for name, df in cleaned.items():
            out = os.path.join(PROC_DIR, f'{name}.csv')
            df.to_csv(out, index=False)
            save_profile(df, os.path.join(PROC_DIR, f'{name}_profile.json'))
            print(f"  saved {out}")

        with open(os.path.join(PROC_DIR, 'metadata.json'), 'w') as f:
            json.dump(metadata, f, indent=2)

        # サンプリング情報
        info = {
            'target_orders': TARGET_ORDERS,
            'random_seed': RANDOM_SEED,
            'tables': {name: len(df) for name, df in cleaned.items()},
            'timestamp': datetime.now().isoformat(),
        }
        with open(os.path.join(PROC_DIR, 'prep_info.json'), 'w') as f:
            json.dump(info, f, indent=2)

        update_progress('issue-65-data-prep', 'completed', tables=info['tables'])
        print("\nOlist データ準備完了。")
    except Exception as e:
        update_progress('issue-65-data-prep', 'error', error=str(e))
        print(f"ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
