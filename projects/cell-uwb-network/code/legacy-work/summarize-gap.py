from pathlib import Path
import json,collections,math
rows=[json.loads(x) for x in Path('outputs/gap-runs/results.jsonl').read_text().splitlines() if json.loads(x)['run']>=100]
g=collections.defaultdict(list)
for r in rows:g[(r['frame_bytes_without_fcs'],r['post_tx_gap_us'])].append(r)
lines=['Single-channel measured baseline; preamble128; SPI8MHz; no ACK/retry.','Frame bytes exclude FCS and include 9-byte test header. Capacity is an ideal serial service-time estimate, NOT a physical multinode result.','frame_B gap_us mean_service_us conservative_N100ms estimate_T200ms estimate_T300ms aggregate_PDR min_run_PDR max_run_PDR']
summary=[]
for (l,gap),rs in sorted(g.items()):
 ts=[r['tx']['elapsed']/r['tx']['tx'] for r in rs]; t=sum(ts)/len(ts); worst=max(ts); pdr=sum(r['rx']['rx'] for r in rs)/sum(r['tx']['tx'] for r in rs)
 lines.append(f'{l:3} {gap:4} {t:9.3f} {math.floor(100000/worst):4} {t*.2:9.3f} {t*.3:9.3f} {pdr:.6f} {min(r["pdr"] for r in rs):.6f} {max(r["pdr"] for r in rs):.6f}')
 summary.append(dict(frame_bytes=l,gap_us=gap,service_us=t,N100ms=math.floor(100000/worst),T200ms=t*.2,T300ms=t*.3,pdr=pdr,runs=len(rs)))
Path('outputs/advisor-gap-results.txt').write_text('\n'.join(lines));Path('outputs/advisor-gap-results.json').write_text(json.dumps(summary,indent=2));print('\n'.join(lines))
try:
 import sys;sys.path.insert(0,str(Path('work/plot-libs').resolve()))
 import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
 fig,ax=plt.subplots(1,2,figsize=(11,4.5))
 for l in (16,32,64):
  a=[x for x in summary if x['frame_bytes']==l]; ax[0].plot([x['gap_us'] for x in a],[x['service_us'] for x in a],'o-',label=f'{l} B frame'); ax[1].plot([x['gap_us'] for x in a],[x['T300ms'] for x in a],'o-',label=f'{l} B frame')
 ax[0].axhline(333.333,color='red',ls='--',label='300 reports / 100 ms budget');ax[1].axhline(100,color='red',ls='--',label='100 ms target')
 ax[0].set_ylabel('Measured average service time (us)'); ax[1].set_ylabel('Estimated time for 300 reports (ms)')
 for a in ax:a.set_xlabel('Configured wait after TX completes (us)');a.grid(alpha=.3);a.legend(fontsize=8)
 fig.suptitle('Two-node single-channel baseline; no ACK/retry; not a 300-node validation');fig.tight_layout();fig.savefig('outputs/advisor-gap-results.png',dpi=180)
except ImportError:pass
