"""実験メタデータ管理ヘルパー: 再現性のためのトラッキングとメタデータ出力"""
import hashlib
import json
import os
import platform
import time
import traceback as tb_module
from datetime import datetime, timezone


def file_sha256(path):
    """ファイルの SHA-256 ハッシュを計算する。ファイルが存在しなければ None を返す。"""
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def update_progress(progress_file, task_id, status, **kwargs):
    """progress.json を更新する（全スクリプト共通）。"""
    progress = {}
    if os.path.exists(progress_file) and os.path.getsize(progress_file) > 0:
        with open(progress_file) as f:
            progress = json.load(f)
    if "tasks" not in progress:
        progress["tasks"] = {}
    entry = {"status": status, "updated_at": datetime.now().isoformat()}
    entry.update(kwargs)
    progress["tasks"][task_id] = entry
    with open(progress_file, "w") as f:
        json.dump(progress, f, indent=2)


class ExperimentRun:
    """1 実験（1 モデル実行）を追跡するコンテキストマネージャ。

    使い方:
        run = ExperimentRun(
            experiment_id="phase1_sdv_gaussiancopula",
            phase="phase1", library="sdv", model="gaussiancopula",
            dataset={"name": "d1_adult", "path": "data/processed/d1_adult.csv",
                     "rows": 32561, "columns": 15},
            params={"random_seed": 42, "num_rows": 32561},
        )
        with run:
            # ... 合成データ生成 ...
            run.set_output(csv_path=path, rows=len(df), columns=len(df.columns))
        run.save_meta(meta_dir, library_version="1.35.1")
    """

    def __init__(self, experiment_id, phase, library, model,
                 dataset, params=None, tags=None, notes=""):
        self.experiment_id = experiment_id
        self.phase = phase
        self.library = library
        self.model = model
        self.dataset = dict(dataset)
        self.params = params or {}
        self.tags = tags or []
        self.notes = notes
        self.status = "running"
        self.error = None
        self.output = {}
        self._start_time = None
        self._start_iso = None
        self._end_iso = None
        self.elapsed_sec = None

    def __enter__(self):
        self._start_time = time.time()
        self._start_iso = datetime.now(timezone.utc).isoformat()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed_sec = round(time.time() - self._start_time, 2)
        self._end_iso = datetime.now(timezone.utc).isoformat()
        if exc_type is not None:
            self.status = "error"
            self.error = {
                "type": exc_type.__name__,
                "message": str(exc_val),
                "traceback": tb_module.format_exc(),
            }
        else:
            self.status = "ok"
        return True  # 例外を抑制し、呼び出し元は self.status で判定

    def set_output(self, csv_path=None, rows=None, columns=None,
                   sequences=None):
        """単一表 / 時系列の出力メタデータを記録する。"""
        if csv_path:
            self.output["csv_path"] = csv_path
            self.output["sha256"] = file_sha256(csv_path)
        if rows is not None:
            self.output["rows"] = rows
        if columns is not None:
            self.output["columns"] = columns
        if sequences is not None:
            self.output["sequences"] = sequences

    def set_multi_table_output(self, table_csv_paths, table_dfs):
        """複数表の出力メタデータを記録する。

        Args:
            table_csv_paths: {table_name: csv_path}
            table_dfs: {table_name: DataFrame}
        """
        tables = {}
        for tname, csv_path in table_csv_paths.items():
            df = table_dfs[tname]
            tables[tname] = {
                "csv_path": csv_path,
                "sha256": file_sha256(csv_path),
                "rows": len(df),
                "columns": len(df.columns),
            }
        self.output["tables"] = tables

    def to_meta(self, library_version="unknown"):
        """`.meta.json` 用の辞書を生成する。"""
        ds = dict(self.dataset)
        if "sha256" not in ds and "path" in ds:
            ds["sha256"] = file_sha256(ds["path"])

        return {
            "$schema": "experiment-meta-v1",
            "experiment_id": self.experiment_id,
            "phase": self.phase,
            "library": self.library,
            "model": self.model,
            "dataset": ds,
            "params": self.params,
            "output": self.output,
            "env": {
                "python_version": platform.python_version(),
                "library_version": library_version,
                "platform": platform.platform(),
                "machine": platform.machine(),
            },
            "timing": {
                "started_at": self._start_iso,
                "finished_at": self._end_iso,
                "elapsed_sec": self.elapsed_sec,
            },
            "status": self.status,
            "error": self.error,
            "tags": self.tags,
            "notes": self.notes,
        }

    def save_meta(self, meta_dir, library_version="unknown"):
        """`.meta.json` をファイルに保存する。"""
        phase_dir = os.path.join(meta_dir, self.phase)
        os.makedirs(phase_dir, exist_ok=True)
        meta = self.to_meta(library_version)
        path = os.path.join(phase_dir, f"{self.experiment_id}.meta.json")
        with open(path, "w") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
        return path


def build_run_log(runs, env):
    """ExperimentRun のリストから既存 run_log 互換の辞書を生成する。"""
    results = {}
    for run in runs:
        entry = {"status": run.status, "time_sec": run.elapsed_sec}
        if run.status == "ok":
            if "rows" in run.output:
                entry["rows"] = run.output["rows"]
            if "tables" in run.output:
                entry["tables"] = {
                    t: info["rows"] for t, info in run.output["tables"].items()
                }
            if "sequences" in run.output:
                entry["sequences"] = run.output["sequences"]
        else:
            if run.error:
                entry["error"] = run.error["message"]
                entry["traceback"] = run.error["traceback"]
        # experiment_id からキーを生成（既存形式に合わせる）
        key = run.experiment_id
        # phase prefix を除去して既存キー名に合わせる
        # e.g. "phase1_sdv_gaussiancopula" -> "sdv_gaussiancopula"
        prefix = f"{run.phase}_"
        if key.startswith(prefix):
            key = key[len(prefix):]
        results[key] = entry
    results["_env"] = env
    return results


def update_manifest(meta_root):
    """results/metadata/ 配下の全 .meta.json を走査して manifest.json を再生成する。"""
    manifest = {}
    if not os.path.isdir(meta_root):
        return
    for phase_dir_name in sorted(os.listdir(meta_root)):
        phase_path = os.path.join(meta_root, phase_dir_name)
        if not os.path.isdir(phase_path):
            continue
        for fname in sorted(os.listdir(phase_path)):
            if not fname.endswith(".meta.json"):
                continue
            fpath = os.path.join(phase_path, fname)
            with open(fpath) as f:
                meta = json.load(f)
            exp_id = meta.get("experiment_id", fname.replace(".meta.json", ""))
            manifest[exp_id] = {
                "status": meta.get("status"),
                "phase": meta.get("phase"),
                "library": meta.get("library"),
                "model": meta.get("model"),
                "dataset": meta.get("dataset", {}).get("name"),
                "elapsed_sec": meta.get("timing", {}).get("elapsed_sec"),
                "output_rows": meta.get("output", {}).get("rows"),
                "timestamp": meta.get("timing", {}).get("started_at"),
            }
    manifest_path = os.path.join(meta_root, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
