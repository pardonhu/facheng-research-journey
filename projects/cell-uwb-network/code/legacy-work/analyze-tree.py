from pathlib import Path
import json,statistics,math
out=Path('outputs/tree-end-to-end-study');raw=[json.loads(x) for x in (out/'results.jsonl').read_text().splitlines()];rows=[]
def q(values,p):return sorted(values)[math.ceil(len(values)*p)-1]
for r in raw:
 if not r['formal']:continue
 assert r['target']==50000
 a=r['boards']['A'];b=r['phase']['B'];count=a['hist_rounds']
 v=dict(name=r['name'],mode=r['mode'],preamble=r['preamble'],reply_marker_delay_us=r['turn_us'],leaf_records=r['target'],groups=count,pdr=r['pdr'],first_pdr=r['first_pdr'],group_mean_ms=r['round_mean_us']/1000,group_p99_upper_ms=None if r['round_p99']['upper_us'] is None else r['round_p99']['upper_us']/1000,group_max_ms=a['round_max']/1000,all_groups_received=r['all_round_rate'],capacity_by_mean_even_groups=2*math.floor(100000/r['round_mean_us']),root_retries=a['retries'],relay_retries=r['boards']['B']['retries'],late_tx=sum(x['late_tx'] for x in r['boards'].values()))
 if r['mode']>=2:
  v['leaf_collection_ms_per_group']=b['collection_us']/count/1000;v['relay_uplink_work_ms_per_group']=b['uplink_us']/count/1000
  v['other_control_wait_processing_ms_per_group']=v['group_mean_ms']-v['leaf_collection_ms_per_group']-v['relay_uplink_work_ms_per_group']
 for size in (200,300):
  w=r['windows'][str(size)];times=[x['us']/1000 for x in w]
  v[f'window{size}']=dict(samples=len(w),mean_ms=statistics.mean(times),p95_ms=q(times,.95),p99_ms=q(times,.99),max_ms=max(times),all_received_rate=sum(x['missing']==0 for x in w)/len(w),all_received_in_100ms=sum(x['missing']==0 and x['us']<=100000 for x in w)/len(w))
 assert sum(x['us'] for x in r['windows']['200'])==a['elapsed']
 assert sum(x['missing'] for x in r['windows']['200'])==a['missing']
 rows.append(v)
(out/'summary.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows[-1] if rows else {'completed':0}))
