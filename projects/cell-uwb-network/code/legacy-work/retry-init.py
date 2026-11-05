from pathlib import Path
p=Path('work/four_io.py');s=p.read_text();a=s.index('  start(b,1,run,n,mode,mask,guard,turn,attempts,quiet)');z=s.index(' start(boards[0]',a)
s=s[:a]+'''  for init_attempt in range(3):
   start(b,1,run,n,mode,mask,guard,turn,attempts,quiet)
   time.sleep(.3)
   s=read(b)
   if s['state']==1 and s['devid']==0xdeca0302:break
   with (out/'initialization-events.jsonl').open('a') as f:f.write(json.dumps(dict(board=b['label'],run=run,attempt=init_attempt,stats=s))+'\\n')
  assert s['state']==1 and s['devid']==0xdeca0302,(b['label'],s)
'''+s[z:];p.write_text(s)
