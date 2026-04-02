# 00: 環境構築

## 目的

検証に必要な Python 環境を、合成データ生成ライブラリごとに分離して構築する。
uv を使用し、依存競合を回避する。

## 前提条件

- Python 3.9 以上がインストール済み
- uv がインストール済み（未導入なら `curl -LsSf https://astral.sh/uv/install.sh | sh`）
- インターネット接続あり（初回 `uv sync` 時のみ）

## 手順

### Step 0-1: uv の確認

```bash
uv --version
# 未導入の場合: curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Step 0-2: .gitignore の作成

```bash
cat > /home/hatano/works/syntheticdata-catalog/.gitignore << 'GITIGNORE'
# Python
__pycache__/
*.pyc
.venv/

# uv
uv.lock

# データ（大きいため git 管理しない）
data/raw/
data/processed/
data/synthetic/

# 実験結果（大きいため git 管理しない。必要に応じて個別に add）
results/phase1/*.csv
results/phase2/*.csv
results/phase3/*.csv

# IDE
.idea/
.vscode/
*.swp

# OS
.DS_Store
Thumbs.db
GITIGNORE
```

### Step 0-3: ディレクトリ構造の作成

```bash
cd /home/hatano/works/syntheticdata-catalog
mkdir -p libs/sdv libs/synthcity libs/mostlyai libs/ydata libs/evaluation
mkdir -p data/raw data/processed
mkdir -p results/phase1 results/phase2 results/phase3 results/evaluation
```

### Step 0-4: 各ライブラリ環境の pyproject.toml 作成

#### libs/sdv/pyproject.toml

```toml
[project]
name = "synth-sdv"
version = "0.1.0"
requires-python = ">=3.9,<3.12"
dependencies = [
    "sdv>=1.0",
    "pandas",
    "numpy",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

#### libs/synthcity/pyproject.toml

```toml
[project]
name = "synth-synthcity"
version = "0.1.0"
requires-python = ">=3.9,<3.11"
dependencies = [
    "synthcity",
    "pandas",
    "numpy",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

#### libs/mostlyai/pyproject.toml

```toml
[project]
name = "synth-mostlyai"
version = "0.1.0"
requires-python = ">=3.9"
dependencies = [
    "mostlyai",
    "pandas",
    "numpy",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

#### libs/ydata/pyproject.toml

```toml
[project]
name = "synth-ydata"
version = "0.1.0"
requires-python = ">=3.9,<3.12"
dependencies = [
    "ydata-synthetic",
    "pandas",
    "numpy",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

#### libs/evaluation/pyproject.toml

```toml
[project]
name = "synth-evaluation"
version = "0.1.0"
requires-python = ">=3.9"
dependencies = [
    "sdmetrics",
    "pandas",
    "numpy",
    "scikit-learn",
    "matplotlib",
    "seaborn",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### Step 0-5: 各環境のセットアップ

各環境を個別にセットアップする。1つが失敗しても他に影響しない。

```bash
cd /home/hatano/works/syntheticdata-catalog

for lib in sdv synthcity mostlyai ydata evaluation; do
    echo "=== Setting up libs/$lib ==="
    (cd libs/$lib && uv sync 2>&1 | tail -5)
    echo "--- exit code: $? ---"
done
```

特定環境だけ再セットアップする場合:
```bash
cd /home/hatano/works/syntheticdata-catalog/libs/synthcity && uv sync
```

Python バージョン問題の場合（例: synthcity が 3.10 を要求）:
```bash
cd /home/hatano/works/syntheticdata-catalog/libs/synthcity
uv python install 3.10
uv sync
```

### Step 0-6: インストール確認・バージョン記録

```bash
cd /home/hatano/works/syntheticdata-catalog

python3 -c "
import json, subprocess, os

results = {}
checks = {
    'sdv': ('libs/sdv', 'import sdv; print(sdv.__version__)'),
    'synthcity': ('libs/synthcity', 'import synthcity; print(getattr(synthcity, \"__version__\", \"unknown\"))'),
    'mostlyai': ('libs/mostlyai', 'import mostlyai; print(getattr(mostlyai, \"__version__\", \"unknown\"))'),
    'ydata': ('libs/ydata', 'import ydata_synthetic; print(getattr(ydata_synthetic, \"__version__\", \"unknown\"))'),
    'evaluation': ('libs/evaluation', 'import sdmetrics; print(sdmetrics.__version__)'),
}

for name, (cwd, cmd) in checks.items():
    try:
        r = subprocess.run(['uv', 'run', 'python', '-c', cmd], capture_output=True, text=True, cwd=cwd, timeout=120)
        results[name] = {
            'status': 'ok' if r.returncode == 0 else 'error',
            'version': r.stdout.strip(),
            'stderr': r.stderr.strip()[:300] if r.returncode != 0 else ''
        }
    except Exception as e:
        results[name] = {'status': 'error', 'error': str(e)}

with open('docs/tasks/install_check.json', 'w') as f:
    json.dump(results, f, indent=2)

ok = sum(1 for v in results.values() if v['status'] == 'ok')
print(f'{ok}/{len(results)} environments ready')
for name, info in results.items():
    status = 'OK' if info['status'] == 'ok' else 'FAIL'
    ver = info.get('version', info.get('error', ''))
    print(f'  {name}: {status} {ver}')
"
```

## 各環境でのスクリプト実行パターン

```bash
# 例: SDV の Phase 1 実行
cd /home/hatano/works/syntheticdata-catalog/libs/sdv
uv run python run_phase1.py

# 例: 評価スクリプトの実行
cd /home/hatano/works/syntheticdata-catalog/libs/evaluation
uv run python tstr_phase1.py
```

## 完了条件

- [ ] uv が利用可能
- [ ] `.gitignore` が配置済み
- [ ] `libs/` 配下に5つのサブディレクトリが存在し、各 `pyproject.toml` が配置済み
- [ ] `uv sync` が各環境で成功（sdv, evaluation は必須。他はベストエフォート）
- [ ] `docs/tasks/install_check.json` が生成済み

## 権限・エラー対策

| 問題 | 対応 |
|------|------|
| sudo 不要 | uv はユーザー権限で動作。`.venv` は各 `libs/<name>/` 直下に作成 |
| Python バージョン制約 | SynthCity は 3.11 以上で動かない場合あり。`uv python install 3.10` で対応 |
| C拡張ビルドエラー | `uv sync --no-build-isolation` を試す。それでもダメなら該当ライブラリをスキップ |
| ネットワーク | 初回 `uv sync` 時のみ PyPI へアクセス。以降はキャッシュ利用 |
| MOSTLY AI | SDK のインストールは可能。実行には `MOSTLY_AI_API_KEY` 環境変数が必要 |
| ディスク容量 | 各 .venv は 500MB〜1GB。合計 3〜5GB の空きが必要 |
