from pathlib import Path
import json,math,statistics
out=Path('outputs/broadcast-tree-study')
raw=[json.loads(x) for x in (out/'results.jsonl').read_text().splitlines()]
def quant(a,q):return sorted(a)[math.ceil(len(a)*q)-1]
rows=[]
for r in raw:
 if not r['formal']:continue
 a=r['boards']['A'];n=a['rounds'];ph=r['phase']['B'];gc=r['group_counts']['B'];pair=r['sync']['B'][0];ready=r['rearm_us']['B']
 v=dict(name=r['name'],mode=r['mode'],slot_us=136+r['guard_us'],target=r['target'],received=a['unique'],missing=a['missing'],mean_ms=r['round_mean_us']/1000,p99_upper_ms=r['round_p99']['upper_us']/1000,max_ms=a['round_max']/1000,collection_ms=ph['collection_us']/n/1000,uplink_ms=ph['uplink_us']/n/1000,relay_retries=r['boards']['B']['retries'],root_retries=a['retries'],late_tx=sum(s['late_tx'] for s in r['boards'].values()),first_leaf_received=gc[2],first_leaf_expected=gc[1],first_leaf_missing=gc[3],injected_D=r['group_counts']['D'][4],group_broadcasts=gc[0],pair_samples=pair['count'],pair_min_ns=pair['min_ns'],pair_max_ns=pair['max_ns'],pair_mean_ns=pair['mean_ns'],rearm_mean_us=ready[1]/ready[0] if ready[0] else None,rearm_min_us=ready[3],rearm_max_us=ready[2])
 v['other_ms']=v['mean_ms']-v['collection_ms']-v['uplink_ms']
 for size in ('200','300'):
  w=r['windows'][size];ts=[t['us']/1000 for t in w]
  v['window'+size]=dict(mean_ms=statistics.mean(ts),p99_ms=quant(ts,.99),samples=len(ts),all_received=sum(t['missing']==0 for t in w),within100ms=sum(t['missing']==0 and t['us']<=100000 for t in w))
 rows.append(v)
(out/'summary.json').write_text(json.dumps(rows,indent=2))
print(json.dumps(rows,ensure_ascii=False))
