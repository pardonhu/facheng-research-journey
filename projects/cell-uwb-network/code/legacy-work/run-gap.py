from pathlib import Path
import subprocess,time,struct,json,itertools
root=Path.cwd(); out=root/'outputs/gap-runs'; out.mkdir(exist_ok=True)
jlink=r'D:\Program Files\SEGGER\JLink_V990\JLink.exe'
boards=['JLINK_A','JLINK_B']; fields='state run tx rx duplicate bad errors timeouts last elapsed'.split()
def command(sn,cmds):
 f=root/f'work/cmd-{sn}.jlink'; f.write_text('connect\n'+cmds+'\nexit\n')
 p=subprocess.run([jlink,'-SelectEmuBySN',sn,'-Device','nRF52832_xxAA','-If','SWD','-Speed','1000','-AutoConnect','0','-ExitOnError','1','-CommandFile',str(f)],capture_output=True,text=True,timeout=30)
 if p.returncode or 'O.K.' not in p.stdout:
  if 'Cannot connect to the probe/programmer' in p.stdout:
   time.sleep(2)
   p=subprocess.run([jlink,'-SelectEmuBySN',sn,'-Device','nRF52832_xxAA','-If','SWD','-Speed','1000','-AutoConnect','0','-ExitOnError','1','-CommandFile',str(f)],capture_output=True,text=True,timeout=30)
  if p.returncode or 'O.K.' not in p.stdout: raise RuntimeError(p.stdout+p.stderr)
 return p.stdout
def read(sn):
 f=root/f'work/stat-{sn}.bin'; command(sn,f'savebin {f.as_posix()} 0x20009318 0x28')
 return dict(zip(fields,struct.unpack('<10I',f.read_bytes())))
def start(sn,role,run,n,interval,length,ch):
 vals=[run,n,interval,length,ch]; cmds=[]
 for i,v in enumerate(vals): cmds.append(f'w4 0x{0x20009344+4*i:X} {v:#x}')
 cmds.append(f'w4 0x20009340 {role}'); command(sn,'\n'.join(cmds))
def stop(sn): command(sn,'w4 0x20009340 3')
run=100
try:
 for cycle in range(1):
  cases=[(5,l,iv,1000,d) for l in (32,16,64) for iv in (1000,500,300,200,150,100,50,0) for d in (0,1)]
  for ch,length,iv,n,d in cases:
   if (root/'work/STOP-GAP').exists(): raise KeyboardInterrupt
   run+=1; tx=boards[d]; rx=boards[1-d]
   start(rx,1,run,n,iv,length,ch); time.sleep(1); rs=read(rx)
   if rs['state']!=1: raise RuntimeError(f'RX init {rs}')
   start(tx,2,run,n,iv,length,ch); print(f'START {run} {tx}->{rx} ch={ch} len={length} interval_us={iv} n={n}',flush=True)
   deadline=time.monotonic()+n*iv/1e6*2+30
   while True:
    time.sleep(0.5)
    if (root/'work/STOP-GAP').exists(): raise KeyboardInterrupt
    ts=read(tx); rs=read(rx)
    (out/'live.json').write_text(json.dumps({'run':run,'tx':ts,'rx':rs},indent=2))
    if ts['state']==3: break
    if ts['state']!=2 or time.monotonic()>deadline: raise RuntimeError(f'TX failed or stalled {ts}')
   time.sleep(1); stop(rx); rs=read(rx)
   result={'run':run,'tx_serial':tx,'rx_serial':rx,'channel':ch,'frame_bytes_without_fcs':length,'post_tx_gap_us':iv,'requested':n,'tx':ts,'rx':rs,'pdr':rs['rx']/ts['tx'] if ts['tx'] else None}
   with (out/'results.jsonl').open('a') as f:f.write(json.dumps(result)+'\n')
   print('RESULT '+json.dumps(result),flush=True)
except KeyboardInterrupt: print('STOP requested',flush=True)
except Exception as e:
 (out/'error.txt').write_text(str(e)); print('ERROR '+str(e),flush=True)
finally:
 for sn in boards:
  try:stop(sn)
  except Exception:pass

