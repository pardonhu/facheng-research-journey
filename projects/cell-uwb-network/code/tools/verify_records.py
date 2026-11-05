"""Verify published MinGap records and received bitmaps, without hardware."""
from pathlib import Path
import json,statistics,hashlib
def main():
 root=Path(__file__).resolve().parents[2]
 data=root/'records/outputs/min-gap-study-20261104-190134'
 rows=[json.loads(l) for l in (data/'正式测试记录.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
 for r in rows:
  n=r['target'];bits=(data/(r['name']+'-received.bin')).read_bytes();s=r['stats']['C']
  assert n==10000 and sum((bits[i//8]>>(i%8))&1 for i in range(n))==s['unique']==n
  assert sum(s[f'node_{i}'] for i in range(3))==n
  assert len(r['batch_time_us'])==34 and abs(sum(r['batch_time_us'])-r['elapsed_us'])<1000
  times=r['batch_time_us'][:33]
  print(r['name'],f"first={r['first_pdr']:.4%}",f"300_mean_ms={statistics.mean(times)/1000:.3f}",f"300_max_ms={max(times)/1000:.3f}",f"within100ms={sum(t<=100000 for t in times)}/33")
  for label,chip in [('A','52832'),('B','52832'),('C','52840'),('D','52840')]:
   p=root/f'code/firmware/platforms/nRF{chip}-MinGap/build/uwb-min-gap.hex'
   assert hashlib.sha256(p.read_bytes()).hexdigest()==r['firmware_sha256'][label],(r['name'],label)
 print(f'PASS: {len(rows)} formal groups, {len(rows)*10000} records; bitmap, batch times and firmware hashes match.')
if __name__=='__main__':main()
