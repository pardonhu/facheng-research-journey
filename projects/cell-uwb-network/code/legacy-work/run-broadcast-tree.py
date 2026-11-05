from broadcast_tree_io import *
import traceback
try:
 flash()
 selected=636
 for slot in (386,486,536,636):
  r=run_case('check-slot'+str(slot),4,n=600,mask=6,guard=slot-136,turn=750,formal=False)
  print('TIMING',slot,'first',r['group_counts']['B'],'rearm',r['rearm_us']['B'],'pair',r['sync']['B'][0]['min_ns'],r['sync']['B'][0]['max_ns'],flush=True)
  if r['pdr']==1 and r['group_counts']['B'][3]==0 and not sum(x['late_tx'] for x in r['boards'].values()):
   selected=min(selected,slot)
 r=run_case('check-injected-missing',4,n=600,mask=6,guard=selected-136,turn=750,formal=False,drop=10)
 assert r['pdr']==1 and r['group_counts']['D'][4]==30 and r['boards']['B']['retries']>=30
 r=run_case('check-permanent-missing',4,n=600,mask=6,guard=selected-136,turn=750,formal=False,quiet=(4,50,10))
 assert r['boards']['A']['node_missing_4']==10 and r['boards']['A']['node_missing_3']==0
 (out/'selection.json').write_text(json.dumps(dict(selected_slot_us=selected,rule='smallest scanned slot with all first replies received in 300-round screening; formal test follows')))
 cases=[('poll-reference',3,636,0),('broadcast-slot636',4,636,0)]
 if selected!=636:cases.append(('broadcast-slot'+str(selected),4,selected,0))
 cases += [('broadcast-missing10pct-D',4,selected,10)]
 for name,mode,slot,drop in cases:
  run_case(name,mode,n=50000,mask=6,guard=slot-136,turn=750,formal=True,drop=drop)
 (out/'status.json').write_text(json.dumps(dict(state='complete',cases=len(cases),selected_slot_us=selected,completed=time.time())))
except BaseException:
 (out/'error.txt').write_text(traceback.format_exc());raise
finally:
 for b in boards:
  try:stop(b)
  except Exception:pass
