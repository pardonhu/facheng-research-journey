from pathlib import Path
import json,datetime
p=Path('outputs/p2p-runs'); rows=[json.loads(x) for x in (p/'results.jsonl').read_text().splitlines() if x.strip()]
a=['Completed runs: '+str(len(rows))]
for r in rows:
 tx=r['tx']['tx']; rx=r['rx']['rx']; rate=tx*1e6/r['tx']['elapsed'] if r['tx']['elapsed'] else 0
 a.append(f"Run {r['run']} {r['tx_serial']}->{r['rx_serial']} ch{r['channel']} frame={r['frame_bytes_without_fcs']}B interval={r['interval_us']}us TX={tx} RX_unique={rx} loss={tx-rx} PDR={r['pdr']:.6f} achieved_rate={rate:.2f}fps RX_errors={r['rx']['errors']}")
Path('outputs/p2p-summary.txt').write_text('\n'.join(a))
print('\n'.join(a))
print('LIVE', (p/'live.json').read_text())
