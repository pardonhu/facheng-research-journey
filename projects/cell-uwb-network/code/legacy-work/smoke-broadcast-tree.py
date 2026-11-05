from broadcast_tree_io import *
try:
 flash()
 for name,mode,guard in [('smoke-poll',3,500),('smoke-broadcast636',4,500),('smoke-broadcast386',4,250)]:
  r=run_case(name,mode,n=600,mask=6,guard=guard,turn=750,formal=False,pre=64)
  print('sync',json.dumps({b:[{k:v for k,v in x.items() if k!='hist_100ns'} for x in r['sync'][b]] for b in ('B','C','D')}),flush=True)
finally:
 for b in boards:
  try:stop(b)
  except Exception:pass
