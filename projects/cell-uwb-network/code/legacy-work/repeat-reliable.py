from pathlib import Path
import time,json
from test_reliable import run_case,stop,boards

# Run 100000-packet natural-link trials until the user requests stop.
try:
 cycle=0
 while not Path('work/STOP-RELIABLE').exists():
  for direction in (0,1):
   if Path('work/STOP-RELIABLE').exists():break
   row=run_case(f'continuous-{cycle}-'+('A-B' if direction==0 else 'B-A'),direction=direction)
   if row['tx']['remote_failed']:
    Path('outputs/reliable-runs/attention.json').write_text(json.dumps(row))
  cycle+=1
except KeyboardInterrupt:
 print('Stopped by request',flush=True)
except Exception as e:
 Path('outputs/reliable-runs/continuous-error.txt').write_text(str(e))
 raise
finally:
 for sn in boards:
  try:stop(sn)
  except Exception:pass
