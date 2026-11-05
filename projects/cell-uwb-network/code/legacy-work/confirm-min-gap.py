from pathlib import Path
import sys
sys.argv=['run-min-gap.py','--resume']
source=Path('work/run-min-gap.py').read_text();exec(source[:source.index('\ntry:\n')])
try:
 for gap in (30,40):case(f'v3-screen-p64-gap{gap}',gap,n=600,formal=False,pre=64)
 case('v3-formal-p64-gap30',30,pre=64)
 case('v3-formal-p64-gap40',40,pre=64)
 case('v3-formal-p128-gap0',0,pre=128)
 (out/'status.json').write_text(json.dumps(dict(state='complete')))
finally:
 for b in boards:
  try:stop(b)
  except Exception:pass
