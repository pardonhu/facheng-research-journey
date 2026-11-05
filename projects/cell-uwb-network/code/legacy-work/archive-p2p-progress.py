from pathlib import Path
import time,json
p=Path('outputs/p2p-runs'); old=''
with (p/'progress.jsonl').open('a') as f:
 while not Path('work/STOP-P2P').exists():
  try:
   s=(p/'live.json').read_text()
   if s!=old:
    obj=json.loads(s); obj['host_unix_time']=time.time(); f.write(json.dumps(obj)+'\n'); f.flush(); old=s
  except (ValueError,OSError): pass
  time.sleep(5)
