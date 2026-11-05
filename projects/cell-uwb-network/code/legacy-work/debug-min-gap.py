from pathlib import Path
import sys
sys.argv=['run-min-gap.py','--resume']
source=Path('work/run-min-gap.py').read_text();exec(source[:source.index('\ntry:\n')])
try:
 for b in boards:command(b,f'h\nloadfile {(b["build"]/"uwb-min-gap.hex").as_posix()}\nr\ng\nsleep 100')
 r=case('v2-debug-gap500',500,n=300,formal=False)
 print(json.dumps(r),flush=True)
finally:
 for b in boards:
  try:stop(b)
  except Exception:pass
