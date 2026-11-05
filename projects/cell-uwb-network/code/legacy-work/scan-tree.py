from tree_io import *
import traceback
try:
 for pre in (64,32):
  r=run_case(f'smoke-aggregate{pre}-750',3,n=600,mask=6,turn=750,formal=False,pre=pre)
  assert r['pdr']==1.0 and sum(b['late_tx'] for b in r['boards'].values())==0,r['name']
 (out/'scan-status.json').write_text(json.dumps(dict(state='complete',selected_reply_delay_us=750)))
finally:
 for b in boards:
  try:stop(b)
  except Exception:pass
