#!/usr/bin/env bash
set -euo pipefail
NEW="${1:?usage: bump-version.sh 2.0.1}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
python3 - "$NEW" <<'PY'
import json, sys
new = sys.argv[1]
cfg = json.load(open('docs/../.version-bump.json'.replace('docs/../','')))
for m in cfg['manifests']:
    p = m['path']
    try:
        d = json.load(open(p))
        d[m['field']] = new
        json.dump(d, open(p, 'w'), indent=2)
        open(p, 'a').write('\n')
        print(f"updated {p}")
    except FileNotFoundError:
        print(f"skip missing {p}")
PY
python3 scripts/update-lock.py
python3 scripts/generate-host-wrappers.py
