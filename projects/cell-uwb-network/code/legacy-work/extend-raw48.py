from pathlib import Path
import sys
sys.argv=['run-raw48.py','--resume']
source=Path('work/run-raw48.py').read_text()
exec(source[:source.index('\ntry:\n')])
try:
 good=[]
 for wait in (350,400,450):
  r=case(f'screen-p32-fast-gap{wait}',32,1,wait,n=300,formal=False)
  if r['pdr']==1 and r['responder']['late_tx']==0:good.append(r)
 selected=min(good,key=lambda r:r['mean_round_us'])['reply_gap_us'] if good else 500
 case(f'p32-fast-gap{selected}-formal',32,1,selected)
 case(f'p32-fast-gap{selected}-reverse',32,1,selected,reverse=True)
 case(f'p32-fast-gap{selected}-drop10pct',32,1,selected,drop=10)
 (out/'status.json').write_text(json.dumps(dict(state='complete',selected_gap_us=selected)))
except BaseException:
 (out/'extension-error.txt').write_text(traceback.format_exc());raise
finally:
 for b in boards:
  try:stop(b)
  except Exception:pass
