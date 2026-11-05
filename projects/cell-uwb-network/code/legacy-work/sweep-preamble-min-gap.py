from pathlib import Path
import sys
sys.argv=['run-min-gap.py','--resume']
source=Path('work/run-min-gap.py').read_text();exec(source[:source.index('\ntry:\n')])
try:
 scanned=[]
 for pre,gap in [(64,50),(64,20),(64,10),(64,5),(64,2),(64,1),(64,0),(128,0)]:
  scanned.append(case(f'v3-screen-p{pre}-gap{gap}',gap,n=600,formal=False,pre=pre))
 good=[r for r in scanned if r['pdr']==1]
 best=min(good,key=lambda r:r['mean_record_us']) if good else dict(preamble=64,gap_us=20)
 picks={(64,0),(64,5),(best['preamble'],best['gap_us'])}
 for pre,gap in sorted(picks):case(f'v3-formal-p{pre}-gap{gap}',gap,pre=pre)
 (out/'status.json').write_text(json.dumps(dict(state='complete',fastest_screen_pre=best['preamble'],fastest_screen_gap=best['gap_us'])))
finally:
 for b in boards:
  try:stop(b)
  except Exception:pass
