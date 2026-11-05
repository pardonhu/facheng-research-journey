from pathlib import Path
import json,math
def air(pre,n):return (pre+8)*1.01763+21*1.02564+(8*n+48*math.ceil(8*n/330))*.12821
rows=[]
for pre in (64,32):
 total=6*air(pre,30)+2*air(pre,34)+air(pre,38)
 rows.append(dict(preamble=pre,control_frames=6,leaf_frames=2,aggregate_frames=1,air_only_group_us=total,air_only_200_ms=100*total/1000,air_only_300_ms=150*total/1000))
result=dict(assumption='Current nine-frame, two-leaf, fully sequential protocol; zero loss, zero idle gaps, zero CPU time. This is a protocol-specific lower bound, not a general UWB network bound.',source='Qorvo DW3000 Datasheet v1.1 Table 18 and section 4.5',url='https://www.mouser.com/catalog/specsheets/Qorvo_DW3000.pdf',rows=rows)
Path('outputs/tree-end-to-end-study/air-budget.json').write_text(json.dumps(result,indent=2));print(json.dumps(rows))
