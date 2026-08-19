<!--
CARDO REI methodology applied to this document.
Reference: [CARDO REI Methodology](PROMPTHOUND-DOCS/CARDO-REI.md)
-->

# V3 Quickstart

## Pull the V3 branch

```bash
cd ~/repos/uap-footage-analyzer
git fetch origin
git checkout v3-residual-analyzer
```

If the repo is not cloned yet:

```bash
cd ~/repos
git clone https://github.com/aaronmarchant96-max/uap-footage-analyzer.git
cd uap-footage-analyzer
git checkout v3-residual-analyzer
```

## Set up Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Expected input folder

Put local videos here:

```text
uap_footage/
```

This folder is ignored by Git so raw footage does not get uploaded.

## Run V3

```bash
python3 src/sky_residual_v3.py \
  --input uap_footage \
  --out uap_results_v3 \
  --motion-threshold 300000 \
  --frame-skip 10 \
  --cooldown-sec 5
```

## Review outputs

```bash
ls -R uap_results_v3 | head -80
cat uap_results_v3/v3_summary.md
```

Inspect the full event log:

```bash
head -5 uap_results_v3/v3_events.jsonl | jq .
```

Inspect the residual review queue:

```bash
head -5 uap_results_v3/v3_residual_review_queue.jsonl | jq .
```

Count labels:

```bash
python3 - <<'PY'
import json
from collections import Counter
from pathlib import Path

path = Path('uap_results_v3/v3_events.jsonl')
rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
counts = Counter(row['label'] for row in rows)

print('total_events:', len(rows))
print('manual_review:', sum(1 for row in rows if row.get('needs_manual_review') is True))
print('\nlabels:')
for label, count in counts.most_common():
    print(label, count)
PY
```

## What success looks like

The first useful result is not a UAP claim.

The first useful result is a reduction report:

```text
V2 raw motion events: 286
V3 known false positives filtered: X
V3 residual review candidates: Y
High priority residuals: Z
```

## Nano option

To inspect or edit the script:

```bash
nano src/sky_residual_v3.py
```
