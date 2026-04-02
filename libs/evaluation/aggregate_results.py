"""全 Phase の実験結果を統合 JSON に集約する。"""
import json
import os
import glob
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..', '..')
EVAL_DIR = os.path.join(ROOT, 'results/evaluation')
PROGRESS_FILE = os.path.join(ROOT, 'docs/tasks/progress.json')
os.makedirs(EVAL_DIR, exist_ok=True)

LIB_MAP = {
    'sdv': ('L-01', 'SDV'),
    'synthcity': ('L-02', 'SynthCity'),
    'mostlyai': ('L-03', 'MOSTLY AI'),
    'ydata': ('L-04', 'ydata-synthetic'),
}

def load_json_safe(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        print(f"WARNING: Failed to load {path}: {e}")
        return {}

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

all_results = []

def extract_lib_info(model_key):
    for prefix, (lib_id, lib_name) in LIB_MAP.items():
        if model_key.startswith(prefix):
            model_name = model_key[len(prefix)+1:] if len(model_key) > len(prefix) else model_key
            return lib_id, lib_name, model_name
    return 'unknown', model_key.split('_')[0], model_key

def collect_phase(phase_name, data_type, dataset_id):
    phase_dir = os.path.join(ROOT, 'results', phase_name)
    if not os.path.isdir(phase_dir):
        print(f"SKIP: {phase_dir} not found")
        return None

    for log_file in sorted(glob.glob(os.path.join(phase_dir, '*_run_log.json'))):
        run_log = load_json_safe(log_file)
        env_info = run_log.pop('_env', {})

        for model_key, info in run_log.items():
            if model_key.startswith('_'):
                continue
            lib_id, lib_name, model_name = extract_lib_info(model_key)

            entry = {
                'experiment_id': f'{phase_name}_{model_key}',
                'library_id': lib_id,
                'library_name': lib_name,
                'model_name': model_name,
                'phase': phase_name,
                'data_type': data_type,
                'dataset_id': dataset_id,
                'run_info': {
                    'status': info.get('status', 'unknown'),
                    'time_sec': info.get('time_sec'),
                    'rows_generated': info.get('rows') or info.get('tables'),
                    'library_version': env_info.get(f'{model_key.split("_")[0]}_version',
                                                    env_info.get('sdv_version', 'unknown')),
                    'python_version': env_info.get('python_version', 'unknown'),
                    'timestamp': env_info.get('timestamp', ''),
                    'error': info.get('error'),
                },
                'metrics': {'utility': {}, 'privacy': {}, 'constraints': {}},
                'raw_output_path': f'results/{phase_name}/{model_key}.csv',
            }
            all_results.append(entry)

    return phase_dir

# Phase 1
phase1_dir = collect_phase('phase1', 'single_table', 'D1')
if phase1_dir:
    sdmetrics = load_json_safe(os.path.join(phase1_dir, 'sdmetrics_eval.json'))
    for entry in all_results:
        if entry['phase'] != 'phase1':
            continue
        key = entry['experiment_id'].replace('phase1_', '')
        if key in sdmetrics and 'status' not in sdmetrics[key]:
            entry['metrics']['utility']['sdmetrics_quality_score'] = sdmetrics[key].get('quality_score')
            entry['metrics']['utility']['sdmetrics_diagnostic_score'] = sdmetrics[key].get('diagnostic_score')

    tstr = load_json_safe(os.path.join(phase1_dir, 'tstr_results.json'))
    for entry in all_results:
        if entry['phase'] != 'phase1':
            continue
        key = entry['experiment_id'].replace('phase1_', '')
        if key in tstr.get('models', {}):
            m = tstr['models'][key]
            if 'status' not in m:
                entry['metrics']['utility']['tstr_accuracy'] = m.get('accuracy')
                entry['metrics']['utility']['tstr_f1'] = m.get('f1')

    privacy = load_json_safe(os.path.join(phase1_dir, 'privacy_eval.json'))
    for entry in all_results:
        if entry['phase'] != 'phase1':
            continue
        key = entry['experiment_id'].replace('phase1_', '')
        if key in privacy and 'status' not in privacy[key]:
            entry['metrics']['privacy'] = privacy[key]

# Phase 2
collect_phase('phase2', 'multi_table', 'D2')

# Phase 3
collect_phase('phase3', 'timeseries', 'D3')

# 保存
with open(os.path.join(EVAL_DIR, 'all_results.json'), 'w') as f:
    json.dump(all_results, f, indent=2, default=str)

status_counts = {}
for r in all_results:
    s = r['run_info']['status']
    status_counts[s] = status_counts.get(s, 0) + 1

phase_counts = {}
for r in all_results:
    p = r['phase']
    if p not in phase_counts:
        phase_counts[p] = {}
    s = r['run_info']['status']
    phase_counts[p][s] = phase_counts[p].get(s, 0) + 1

summary = {
    'total_experiments': len(all_results),
    'status_counts': status_counts,
    'by_phase': phase_counts,
    'generated_at': datetime.now().isoformat(),
}

with open(os.path.join(EVAL_DIR, 'summary.json'), 'w') as f:
    json.dump(summary, f, indent=2)

update_progress('05-evaluation', 'completed')
print(json.dumps(summary, indent=2))
print(f"\nSaved: {EVAL_DIR}/all_results.json ({len(all_results)} entries)")
