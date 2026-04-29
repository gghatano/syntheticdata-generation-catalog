"""Olist 合成データの評価。

評価項目（Issue #65 準拠）:
1. スキーマ整合性（FK 整合性、PK 重複）
2. 件数構造（顧客あたり注文数、注文あたり明細・支払・レビュー数）
3. 単変量分布（KS / TV）
4. 多変量分布（カテゴリ × 数値の集計差）
5. リレーション評価（親属性 × 子集計）
6. TSTR（レビュー評価予測 / 注文金額予測）
7. プライバシー（DCR）
8. 性能はrun_logから読み取り

実行: cd libs/evaluation && uv run python eval_olist.py
"""
import json
import os
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..', '..')
PROC_DIR = os.path.join(ROOT, 'data', 'processed', 'olist')
OUTPUT_DIR = os.path.join(ROOT, 'results', 'phase2_olist')

RANDOM_SEED = 42


def load_metadata():
    with open(os.path.join(PROC_DIR, 'metadata.json')) as f:
        return json.load(f)


def load_real_tables(metadata):
    tables = {}
    for tname, tdef in metadata['tables'].items():
        df = pd.read_csv(os.path.join(PROC_DIR, f'{tname}.csv'))
        for col, col_def in tdef['columns'].items():
            if col_def['sdtype'] == 'datetime' and col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        tables[tname] = df
    return tables


def load_synth_tables(prefix, expected_tables):
    """OUTPUT_DIR/<prefix>_<table>.csv を読み込む。なければスキップ。"""
    tables = {}
    for tname in expected_tables:
        path = os.path.join(OUTPUT_DIR, f'{prefix}_{tname}.csv')
        if os.path.exists(path):
            tables[tname] = pd.read_csv(path)
    return tables


def fk_integrity(tables, metadata):
    results = {}
    for rel in metadata['relationships']:
        p, c = rel['parent_table_name'], rel['child_table_name']
        pk, fk = rel['parent_primary_key'], rel['child_foreign_key']
        if p not in tables or c not in tables:
            continue
        if pk not in tables[p].columns or fk not in tables[c].columns:
            # RTF などは child に FK 列を持たない出力をする
            results[f'{p}->{c}'] = {'status': 'fk_column_missing'}
            continue
        parent_set = set(tables[p][pk].dropna())
        child_fks = tables[c][fk].dropna()
        orphans = (~child_fks.isin(parent_set)).sum()
        results[f'{p}->{c}'] = {
            'orphans': int(orphans),
            'orphan_rate': float(orphans) / max(len(child_fks), 1),
            'parent_unique': len(parent_set),
            'child_total': len(child_fks),
            'integrity': bool(orphans == 0),
        }
    return results


def pk_uniqueness(tables, metadata):
    results = {}
    for tname, tdef in metadata['tables'].items():
        pk = tdef.get('primary_key')
        if not pk or tname not in tables:
            continue
        df = tables[tname]
        if pk not in df.columns:
            continue
        dup = df[pk].duplicated().sum()
        results[tname] = {
            'pk': pk,
            'duplicates': int(dup),
            'unique_rate': 1.0 - dup / max(len(df), 1),
        }
    return results


def count_distribution(real_tables, synth_tables, parent, child, parent_key, child_fk):
    """親 1 件あたりの子件数分布を比較。"""
    if parent not in real_tables or child not in real_tables:
        return None
    if parent not in synth_tables or child not in synth_tables:
        return None

    def _counts(p_df, c_df):
        if parent_key not in p_df.columns or child_fk not in c_df.columns:
            return None
        counts = c_df.groupby(child_fk).size()
        # 親に存在するキーすべてに対して 0 を含める
        all_keys = p_df[parent_key]
        full = counts.reindex(all_keys, fill_value=0)
        return full

    real_c = _counts(real_tables[parent], real_tables[child])
    synth_c = _counts(synth_tables[parent], synth_tables[child])
    if real_c is None or synth_c is None:
        return None

    return {
        'real_mean': float(real_c.mean()),
        'real_std': float(real_c.std()),
        'real_max': int(real_c.max()),
        'synth_mean': float(synth_c.mean()),
        'synth_std': float(synth_c.std()),
        'synth_max': int(synth_c.max()),
        'mean_diff': float(abs(real_c.mean() - synth_c.mean())),
    }


def numeric_marginals(real_df, synth_df, cols):
    """数値列の分布差（KS）。"""
    from scipy.stats import ks_2samp
    res = {}
    for c in cols:
        if c not in real_df.columns or c not in synth_df.columns:
            continue
        r = real_df[c].dropna().astype(float)
        s = synth_df[c].dropna().astype(float)
        if len(r) < 2 or len(s) < 2:
            continue
        ks = ks_2samp(r, s)
        res[c] = {
            'ks_stat': float(ks.statistic),
            'real_mean': float(r.mean()),
            'synth_mean': float(s.mean()),
            'real_std': float(r.std()),
            'synth_std': float(s.std()),
        }
    return res


def categorical_marginals(real_df, synth_df, cols):
    """カテゴリ列の TV（total variation）。"""
    res = {}
    for c in cols:
        if c not in real_df.columns or c not in synth_df.columns:
            continue
        r = real_df[c].fillna('__NA__').astype(str).value_counts(normalize=True)
        s = synth_df[c].fillna('__NA__').astype(str).value_counts(normalize=True)
        cats = sorted(set(r.index) | set(s.index))
        r_aligned = np.array([r.get(x, 0.0) for x in cats])
        s_aligned = np.array([s.get(x, 0.0) for x in cats])
        tv = 0.5 * float(np.abs(r_aligned - s_aligned).sum())
        res[c] = {'tv_distance': tv, 'real_n_categories': int(len(r)), 'synth_n_categories': int(len(s))}
    return res


def tstr_review_score_classification(real_tables, synth_tables):
    """レビュー評価（1-5）の予測。"""
    if 'order_reviews' not in real_tables or 'order_payments' not in real_tables:
        return None
    if 'order_reviews' not in synth_tables or 'order_payments' not in synth_tables:
        return None

    def _build(tables):
        rv = tables['order_reviews'][['order_id', 'review_score']].dropna()
        pm = tables['order_payments'].groupby('order_id').agg(
            payment_value_sum=('payment_value', 'sum'),
            payment_installments_max=('payment_installments', 'max'),
        ).reset_index()
        oi = tables['order_items'].groupby('order_id').agg(
            n_items=('order_item_id', 'count'),
            price_sum=('price', 'sum'),
            freight_sum=('freight_value', 'sum'),
        ).reset_index() if 'order_items' in tables else None
        df = rv.merge(pm, on='order_id', how='left')
        if oi is not None:
            df = df.merge(oi, on='order_id', how='left')
        df = df.dropna()
        if len(df) < 50:
            return None
        df['review_score'] = df['review_score'].astype(int)
        return df

    real = _build(real_tables)
    synth = _build(synth_tables)
    if real is None or synth is None:
        return None

    feat = [c for c in ['payment_value_sum', 'payment_installments_max', 'n_items', 'price_sum', 'freight_sum'] if c in real.columns]
    if not feat:
        return None
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score, f1_score

    clf = RandomForestClassifier(n_estimators=80, random_state=RANDOM_SEED, n_jobs=1)
    clf.fit(synth[feat], synth['review_score'])
    pred = clf.predict(real[feat])
    return {
        'task': 'review_score_classification',
        'tstr_accuracy': float(accuracy_score(real['review_score'], pred)),
        'tstr_f1_macro': float(f1_score(real['review_score'], pred, average='macro')),
        'features': feat,
        'real_test_n': len(real),
        'synth_train_n': len(synth),
    }


def dcr_summary(real_df, synth_df, cols, sample=2000):
    """数値列のみで簡易 DCR（最近傍距離）を計算。"""
    use = [c for c in cols if c in real_df.columns and c in synth_df.columns]
    if not use:
        return None
    real_x = real_df[use].dropna().astype(float).values
    synth_x = synth_df[use].dropna().astype(float).values
    if len(real_x) == 0 or len(synth_x) == 0:
        return None

    rng = np.random.RandomState(RANDOM_SEED)
    if len(real_x) > sample:
        real_x = real_x[rng.choice(len(real_x), sample, replace=False)]
    if len(synth_x) > sample:
        synth_x = synth_x[rng.choice(len(synth_x), sample, replace=False)]
    # 標準化
    mu = real_x.mean(axis=0)
    sd = real_x.std(axis=0) + 1e-6
    real_n = (real_x - mu) / sd
    synth_n = (synth_x - mu) / sd
    from sklearn.neighbors import NearestNeighbors
    nn = NearestNeighbors(n_neighbors=1).fit(real_n)
    dist, _ = nn.kneighbors(synth_n)
    return {
        'dcr_mean': float(dist.mean()),
        'dcr_min': float(dist.min()),
        'dcr_p5': float(np.percentile(dist, 5)),
        'features': use,
        'n_real_used': len(real_x),
        'n_synth_used': len(synth_x),
    }


def quality_score_multitable(real_tables, synth_tables, metadata):
    """SDMetrics MultiTableQualityReport を計算（共通テーブルのみ）。"""
    common = [t for t in metadata['tables'].keys() if t in real_tables and t in synth_tables]
    if len(common) < 2:
        return None
    # metadata から共通テーブル分のみ抽出
    sub_meta = {
        'METADATA_SPEC_VERSION': metadata.get('METADATA_SPEC_VERSION', 'V1'),
        'tables': {t: metadata['tables'][t] for t in common},
        'relationships': [
            r for r in metadata['relationships']
            if r['parent_table_name'] in common and r['child_table_name'] in common
        ],
    }
    real_sub = {t: real_tables[t].copy() for t in common}
    synth_sub = {t: synth_tables[t].copy() for t in common}

    try:
        from sdmetrics.reports.multi_table import QualityReport
        report = QualityReport()
        report.generate(real_sub, synth_sub, sub_meta, verbose=False)
        return {
            'quality_score': float(report.get_score()),
            'tables_evaluated': common,
        }
    except Exception as e:
        return {'error': str(e), 'tables_evaluated': common}


def evaluate_method(prefix, real_tables, metadata):
    expected = list(metadata['tables'].keys())
    synth = load_synth_tables(prefix, expected)
    if not synth:
        return {'status': 'no_synth_data'}

    out = {
        'tables_present': sorted(synth.keys()),
        'tables_missing': sorted(set(expected) - set(synth.keys())),
    }

    # 0. quality_score (SDMetrics)
    qs = quality_score_multitable(real_tables, synth, metadata)
    if qs:
        out['quality_score'] = qs

    # 1. スキーマ整合性
    out['fk_integrity'] = fk_integrity(synth, metadata)
    out['pk_uniqueness'] = pk_uniqueness(synth, metadata)

    # 2. 件数構造
    out['count_distribution'] = {}
    for rel in metadata['relationships']:
        p, c = rel['parent_table_name'], rel['child_table_name']
        if p not in synth or c not in synth:
            continue
        cd = count_distribution(real_tables, synth, p, c, rel['parent_primary_key'], rel['child_foreign_key'])
        if cd:
            out['count_distribution'][f'{p}->{c}'] = cd

    # 3. 単変量分布（主要数値列）
    if 'order_items' in synth:
        out['marginal_order_items_numeric'] = numeric_marginals(
            real_tables['order_items'], synth['order_items'], ['price', 'freight_value', 'order_item_id']
        )
    if 'order_payments' in synth:
        out['marginal_payments_numeric'] = numeric_marginals(
            real_tables['order_payments'], synth['order_payments'],
            ['payment_value', 'payment_installments', 'payment_sequential']
        )
        out['marginal_payments_categorical'] = categorical_marginals(
            real_tables['order_payments'], synth['order_payments'], ['payment_type']
        )
    if 'orders' in synth:
        out['marginal_orders_categorical'] = categorical_marginals(
            real_tables['orders'], synth['orders'], ['order_status']
        )
    if 'order_reviews' in synth:
        out['marginal_reviews_numeric'] = numeric_marginals(
            real_tables['order_reviews'], synth['order_reviews'], ['review_score']
        )

    # 6. TSTR
    tstr = tstr_review_score_classification(real_tables, synth)
    if tstr:
        out['tstr'] = tstr

    # 7. DCR（order_items 数値列で簡易）
    if 'order_items' in synth:
        out['dcr_order_items'] = dcr_summary(
            real_tables['order_items'], synth['order_items'], ['price', 'freight_value']
        )

    # サマリ集計（カタログUI 表示向け）
    summary = {}
    if 'quality_score' in out and 'quality_score' in out['quality_score']:
        summary['quality_score'] = out['quality_score']['quality_score']
    fk_eval = [v for v in out['fk_integrity'].values() if 'integrity' in v]
    fk_ok = all(v['integrity'] for v in fk_eval) if fk_eval else None
    summary['fk_all_integrity'] = fk_ok
    summary['fk_orphan_total'] = sum(v['orphans'] for v in fk_eval)
    summary['fk_relations_evaluated'] = len(fk_eval)
    if out.get('count_distribution'):
        diffs = [v['mean_diff'] for v in out['count_distribution'].values()]
        summary['count_mean_diff_avg'] = float(np.mean(diffs)) if diffs else None
    if 'marginal_order_items_numeric' in out:
        ks_vals = [v['ks_stat'] for v in out['marginal_order_items_numeric'].values()]
        summary['ks_order_items_avg'] = float(np.mean(ks_vals)) if ks_vals else None
    if tstr:
        summary['tstr_accuracy'] = tstr['tstr_accuracy']
        summary['tstr_f1_macro'] = tstr['tstr_f1_macro']
    if 'dcr_order_items' in out and out['dcr_order_items']:
        summary['dcr_mean'] = out['dcr_order_items']['dcr_mean']

    out['summary'] = summary
    return out


def main():
    metadata = load_metadata()
    real_tables = load_real_tables(metadata)
    print(f"Real tables: {[(n, len(d)) for n, d in real_tables.items()]}")

    methods = ['sdv_hma', 'realtabformer']
    all_eval = {'_metadata': {
        'evaluated_at': datetime.now().isoformat(),
        'real_tables': {n: len(d) for n, d in real_tables.items()},
    }}

    for prefix in methods:
        print(f"\n=== Evaluating {prefix} ===")
        all_eval[prefix] = evaluate_method(prefix, real_tables, metadata)
        if 'summary' in all_eval[prefix]:
            print(f"  summary: {all_eval[prefix]['summary']}")
        else:
            print(f"  status: {all_eval[prefix].get('status')}")

    out_path = os.path.join(OUTPUT_DIR, 'olist_eval.json')
    with open(out_path, 'w') as f:
        json.dump(all_eval, f, indent=2, default=str)
    print(f"\nSaved {out_path}")


if __name__ == '__main__':
    main()
