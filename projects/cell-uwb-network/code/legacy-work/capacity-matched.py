from pathlib import Path
import json, math
import numpy as np
out=Path('outputs/ble-matched-study')
model=json.loads((out/'model-results.json').read_text())
rows=[]
for r in model['profiles']:
    agg=r['aggregation'];case=r['case'];poll=case.startswith('poll')
    step=r['poll_air_us']+r['data_air_us']+300 if poll else (r['data_air_us']+150)*(5 if case=='repeat5' else 1)
    success=.81 if poll else 1
    mean_capacity=math.floor(100150*success/step)*agg
    q99capacity=None
    if poll:
        lo,hi=0,mean_capacity//agg+1
        while hi-lo>1:
            mid=(lo+hi)//2
            trials=np.random.default_rng(20261104).negative_binomial(mid,.81,50000)+mid
            if np.quantile(trials*step-150,.99,method='higher')<=100000:lo=mid
            else:hi=mid
        q99capacity=lo*agg
    rows.append(dict(profile=r['profile'],case=case,aggregation=agg,mean300_ms=(300/agg/success*step-150)/1000,p99_300_ms=r['p99_ms'],capacity_by_mean=mean_capacity,capacity_by_p99_simulation=q99capacity))
(out/'model-capacity.json').write_text(json.dumps(rows,indent=2))
print(json.dumps(rows))
