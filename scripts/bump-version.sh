#!/usr/bin/env bash
set -euo pipefail
NEW="${1:?usage: bump-version.sh 2.0.1}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
python3 - "$NEW" "$ROOT" <<'PY'
import json, os, sys
new = sys.argv[1]
root = sys.argv[2]
cfg = json.load(open(os.path.join(root, '.version-bump.json')))
for m in cfg['manifests']:
    p = os.path.join(root, m['path'])
    try:
        d = json.load(open(p))
        d[m['field']] = new
        json.dump(d, open(p, 'w'), indent=2)
        open(p, 'a').write('\n')
        print(f"updated {m['path']}")
    except FileNotFoundError:
        print(f"skip missing {m['path']}")
PY
python3 "$ROOT/scripts/update-lock.py"
python3 "$ROOT/scripts/generate-host-wrappers.py"
