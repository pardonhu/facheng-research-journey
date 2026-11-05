import json
from pathlib import Path
rows=[json.loads(x) for x in Path('outputs/four-board-study/results.jsonl').read_text().splitlines()]
r=[r for r in rows if r['name']=='smoke-missing-D'][-1]
a=r['boards']['A'];d=r['boards']['D'];assert [a[f'node_unique_{n}'] for n in (2,3,4)]==[1000,1000,980];assert a['missing']==20 and d['quiet_skips']==100
print('Fault injection verified: B=1000 C=1000 D=980; 100 ignored polls across 20 missing rounds.')
