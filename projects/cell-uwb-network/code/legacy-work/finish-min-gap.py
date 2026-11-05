from pathlib import Path
import sys
sys.argv=['run-min-gap.py','--resume']
source=Path('work/run-min-gap.py').read_text();exec(source[:source.index('\ntry:\n')])
try:
 for b in boards:command(b,f'h\nloadfile {(b["build"]/"uwb-min-gap.hex").as_posix()}\nr\ng\nsleep 100')
 scanned=[]
 for gap in (200,100,50,20,10,5,2,1,0):scanned.append(case(f'v3-screen-gap{gap}',gap,n=600,formal=False))
 good=[r for r in scanned if r['pdr']==1]
 best=min(good,key=lambda r:r['mean_record_us'])['gap_us'] if good else 50
 picks={0,best,next((x for x in (1,2,5,10,20,50,100,200) if x>best),500)}
 for gap in sorted(picks):case(f'v3-formal-gap{gap}',gap)
 (out/'status.json').write_text(json.dumps(dict(state='complete',fastest_screen_gap_us=best)))
except BaseException:
 (out/'v3-error.txt').write_text(traceback.format_exc());raise
finally:
 for b in boards:
  try:stop(b)
  except Exception:pass
