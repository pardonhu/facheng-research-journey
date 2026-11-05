import argparse,traceback
from four_io import *
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--flash',action='store_true');a.add_argument('--smoke',action='store_true');args=a.parse_args()
 try:
  if args.flash:flash()
  if args.smoke:
   run_case('smoke-individual',0,3000,formal=False)
   run_case('smoke-group',1,3000,formal=False)
   run_case('smoke-relay-forward',2,2000,mask=6,formal=False)
   run_case('smoke-relay-aggregate',3,2000,mask=6,formal=False)
   run_case('smoke-missing-D',0,3000,quiet=(4,100,20),formal=False)
  else:
   run_case('individual-3',0)
   for guard in (1000,500,250,100,50,0):run_case(f'group-3-guard{guard}',1,guard=guard)
   run_case('direct-2-leaves',0,mask=6)
   run_case('relay-forward-2',2,mask=6)
   run_case('relay-aggregate-2',3,mask=6)
  (out/'status.json').write_text(json.dumps(dict(state='smoke_complete' if args.smoke else 'complete',completed=time.time())))
 except BaseException:
  (out/'error.txt').write_text(traceback.format_exc());raise
 finally:
  for b in boards:
   try:stop(b)
   except Exception:pass
