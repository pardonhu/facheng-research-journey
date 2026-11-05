import argparse,traceback
from tree_io import *
cases=[('direct64',0,64,1000),('forward64',2,64,1000),('aggregate64',3,64,1000),('aggregate32',3,32,1000),('aggregate64-fast',3,64,750),('aggregate32-fast',3,32,750)]
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--flash',action='store_true');p.add_argument('--smoke',action='store_true');args=p.parse_args()
 try:
  if args.flash:flash()
  for name,mode,pre,turn in cases:
   run_case(('smoke-' if args.smoke else '')+name,mode,n=600 if args.smoke else 50000,mask=6,turn=turn,formal=not args.smoke,pre=pre)
  if args.smoke:
   r=run_case('smoke-missing-leaf',3,n=600,mask=6,quiet=(4,50,10),formal=False,pre=64)
   assert r['boards']['A']['node_missing_4']==10 and r['boards']['A']['node_missing_3']==0,r
  (out/'status.json').write_text(json.dumps(dict(state='smoke_complete' if args.smoke else 'complete',completed=time.time())))
 except BaseException:
  (out/'error.txt').write_text(traceback.format_exc());raise
 finally:
  for b in boards:
   try:stop(b)
   except Exception:pass
