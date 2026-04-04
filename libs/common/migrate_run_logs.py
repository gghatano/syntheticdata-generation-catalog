"""既存 run_log から .meta.json を生成するマイグレーションスクリプト。

実行: python libs/common/migrate_run_logs.py
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..', '..')
sys.path.insert(0, os.path.join(ROOT, 'libs'))
from common.experiment import file_sha256, update_manifest

META_DIR = os.path.join(ROOT, 'results/metadata')

# 既存 run_log とそのコンテキスト情報のマッピング
RUN_LOG_CONFIG = [
    {
        "path": "results/phase1/sdv_run_log.json",
        "phase": "phase1",
        "library": "sdv",
        "version_key": "sdv_version",
        "dataset": {"name": "d1_adult", "path": "data/processed/d1_adult.csv"},
        "entries": {
            "sdv_gaussiancopula": {"model": "gaussiancopula", "csv": "results/phase1/sdv_gaussiancopula.csv"},
            "sdv_ctgan": {"model": "ctgan", "csv": "results/phase1/sdv_ctgan.csv"},
        },
    },
    {
        "path": "results/phase1/synthcity_run_log.json",
        "phase": "phase1",
        "library": "synthcity",
        "version_key": "synthcity_version",
        "dataset": {"name": "d1_adult", "path": "data/processed/d1_adult.csv"},
        "entries": {
            "synthcity_bayesian_network": {"model": "bayesian_network", "csv": "results/phase1/synthcity_bayesian_network.csv"},
            "synthcity_ctgan": {"model": "ctgan", "csv": "results/phase1/synthcity_ctgan.csv"},
            "synthcity_tvae": {"model": "tvae", "csv": "results/phase1/synthcity_tvae.csv"},
            "synthcity_adsgan": {"model": "adsgan", "csv": "results/phase1/synthcity_adsgan.csv"},
            "synthcity_nflow": {"model": "nflow", "csv": "results/phase1/synthcity_nflow.csv"},
            "synthcity_marginal_distributions": {"model": "marginal_distributions", "csv": "results/phase1/synthcity_marginal_distributions.csv"},
        },
    },
    {
        "path": "results/phase1/ydata_run_log.json",
        "phase": "phase1",
        "library": "ydata",
        "version_key": "ydata_version",
        "dataset": {"name": "d1_adult", "path": "data/processed/d1_adult.csv"},
        "entries": {
            "ydata_ctgan": {"model": "ctgan", "csv": "results/phase1/ydata_ctgan.csv"},
        },
    },
    {
        "path": "results/phase1/additional_run_log.json",
        "phase": "phase1",
        "library": "sdv",
        "version_key": "sdv_version",
        "entries": {
            "insurance_gaussiancopula": {
                "model": "gaussiancopula",
                "experiment_id": "phase1_sdv_gaussiancopula_insurance",
                "csv": "results/phase1/sdv_gaussiancopula_insurance.csv",
                "dataset": {"name": "d_insurance", "path": "data/raw/d_insurance.csv"},
            },
            "insurance_ctgan_50ep": {
                "model": "ctgan",
                "experiment_id": "phase1_sdv_ctgan_50ep_insurance",
                "csv": "results/phase1/sdv_ctgan_50ep_insurance.csv",
                "dataset": {"name": "d_insurance", "path": "data/raw/d_insurance.csv"},
            },
            "imdb_hma": {
                "model": "hma",
                "experiment_id": "phase2_sdv_hma_imdb",
                "phase": "phase2",
                "dataset": {"name": "d_imdb_small", "path": "data/raw/d_imdb_*.csv"},
                "multi_table": True,
            },
            "fake_companies_gaussiancopula": {
                "model": "gaussiancopula",
                "experiment_id": "phase1_sdv_gaussiancopula_fake_companies",
                "csv": "results/phase1/sdv_gaussiancopula_fake_companies.csv",
                "dataset": {"name": "d_fake_companies", "path": "data/raw/d_fake_companies.csv"},
            },
        },
    },
    {
        "path": "results/phase2/sdv_run_log.json",
        "phase": "phase2",
        "library": "sdv",
        "version_key": "sdv_version",
        "dataset": {"name": "d2_hotel_reservations", "path": "data/processed/d2_*.csv"},
        "entries": {
            "sdv_hma": {"model": "hma", "multi_table": True},
        },
    },
    {
        "path": "results/phase3/sdv_run_log.json",
        "phase": "phase3",
        "library": "sdv",
        "version_key": "sdv_version",
        "dataset": {"name": "d3_nasdaq", "path": "data/processed/d3_nasdaq.csv"},
        "entries": {
            "sdv_par": {"model": "par", "csv": "results/phase3/sdv_par.csv"},
        },
    },
    {
        "path": "results/phase3/weather_run_log.json",
        "phase": "phase3",
        "library": "sdv",
        "version_key": "sdv_version",
        "dataset": {"name": "d_weather", "path": "data/processed/d_weather.csv"},
        "entries": {
            "weather_par": {
                "model": "par",
                "experiment_id": "phase3_sdv_par_weather",
                "csv": "results/phase3/weather_par.csv",
            },
        },
    },
]


def migrate_run_log(config):
    """1 つの run_log ファイルから .meta.json を生成する。"""
    run_log_path = os.path.join(ROOT, config["path"])
    if not os.path.exists(run_log_path):
        print(f"  SKIP: {config['path']} not found")
        return 0

    with open(run_log_path) as f:
        run_log = json.load(f)

    env_info = run_log.get("_env", {})
    count = 0

    for key, entry_config in config["entries"].items():
        if key not in run_log:
            print(f"  SKIP: key '{key}' not in {config['path']}")
            continue

        entry = run_log[key]
        phase = entry_config.get("phase", config["phase"])
        library = config["library"]
        model = entry_config["model"]
        experiment_id = entry_config.get("experiment_id", f"{phase}_{library}_{model}")
        dataset = entry_config.get("dataset", config.get("dataset", {}))

        # output 情報の構築
        output = {}
        if "csv" in entry_config:
            csv_abs = os.path.join(ROOT, entry_config["csv"])
            output["csv_path"] = entry_config["csv"]
            output["sha256"] = file_sha256(csv_abs)
        if "rows" in entry:
            output["rows"] = entry["rows"]
        if "tables" in entry:
            output["tables"] = {}
            for tname, row_count in entry["tables"].items():
                output["tables"][tname] = {"rows": row_count}
        if "sequences" in entry:
            output["sequences"] = entry["sequences"]

        # dataset sha256 計算
        ds = dict(dataset)
        if "path" in ds and not ds["path"].endswith("*.csv"):
            ds_abs = os.path.join(ROOT, ds["path"])
            ds["sha256"] = file_sha256(ds_abs)

        meta = {
            "$schema": "experiment-meta-v1",
            "experiment_id": experiment_id,
            "phase": phase,
            "library": library,
            "model": model,
            "dataset": ds,
            "params": {"random_seed": 42},
            "output": output,
            "env": {
                "python_version": env_info.get("python_version", "unknown"),
                "library_version": env_info.get(config.get("version_key", ""), "unknown"),
                "platform": "migrated",
                "machine": "migrated",
            },
            "timing": {
                "started_at": env_info.get("timestamp"),
                "finished_at": None,
                "elapsed_sec": entry.get("time_sec"),
            },
            "status": entry.get("status", "unknown"),
            "error": None,
            "tags": ["migrated"],
            "notes": f"Migrated from {config['path']}",
        }

        if entry.get("status") == "error":
            meta["error"] = {
                "type": "unknown",
                "message": entry.get("error", ""),
                "traceback": entry.get("traceback", ""),
            }

        # 保存
        phase_dir = os.path.join(META_DIR, phase)
        os.makedirs(phase_dir, exist_ok=True)
        meta_path = os.path.join(phase_dir, f"{experiment_id}.meta.json")
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
        print(f"  Created: {os.path.relpath(meta_path, ROOT)}")
        count += 1

    return count


def main():
    print("=== Migrating existing run_logs to .meta.json ===\n")
    total = 0
    for config in RUN_LOG_CONFIG:
        print(f"Processing: {config['path']}")
        total += migrate_run_log(config)

    print(f"\nMigrated {total} experiments.")

    print("\nGenerating manifest.json...")
    update_manifest(META_DIR)
    print("Done.")


if __name__ == "__main__":
    main()
