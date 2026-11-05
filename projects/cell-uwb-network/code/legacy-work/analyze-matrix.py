from pathlib import Path
import sys,json,collections
sys.path.insert(0,str(Path('work/plot-libs').resolve()))
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
rows=[json.loads(x) for x in Path('outputs/broadcast-long-runs/results.jsonl').read_text().splitlines()]
g=collections.defaultdict(list)
for r in rows:g[(r['channel'],r['frame_bytes'],r['post_tx_gap_us'])].append(r)
summary=[]
for k,a in sorted(g.items()):
 tx=sum(r['tx']['tx'] for r in a);rx=sum(r['rx']['rx'] for r in a);t=sum(r['tx']['elapsed'] for r in a)/tx
 summary.append(dict(channel=k[0],frame=k[1],gap=k[2],runs=len(a),tx=tx,rx=rx,pdr=rx/tx,minimum=min(r['pdr'] for r in a),maximum=max(r['pdr'] for r in a),service_us=t,N100=int(100000/t),T200=t*.2,T300=t*.3,payload_kbps=(k[1]-17)*8*rx/(sum(r['tx']['elapsed'] for r in a)/1e6)/1000))
Path('outputs/broadcast-matrix-summary.json').write_text(json.dumps(summary,indent=2))
fig,ax=plt.subplots(figsize=(9,4.5))
keys=[(l,d) for l in (32,64) for d in (0,150,500)]
for ch,offset in ((5,-.12),(9,.12)):
 a=[next(x for x in summary if (x['channel'],x['frame'],x['gap'])==(ch,*k)) for k in keys]
 ys=[x['pdr']*100 for x in a]
 ax.errorbar([i+offset for i in range(6)],ys,yerr=[[100*(x['pdr']-x['minimum']) for x in a],[100*(x['maximum']-x['pdr']) for x in a]],fmt='o',capsize=4,label=f'Channel {ch}: aggregate and run range')
ax.set_xticks(range(6),[f'{l}B / {d}us' for l,d in keys]);ax.set_ylabel('Unique packet delivery (%)');ax.set_xlabel('Frame bytes excluding FCS / post-TX wait');ax.grid(axis='y',alpha=.3);ax.legend(fontsize=8);ax.set_title('1,970,000 packets across 197 completed runs; no retries');fig.tight_layout();fig.savefig('outputs/broadcast-matrix.png',dpi=180)
print('matrix prepared',sum(x['tx'] for x in summary))
