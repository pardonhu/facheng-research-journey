from pathlib import Path
import subprocess,time,struct,json,itertools
root=Path.cwd(); out=root/'outputs/broadcast-runs'; out.mkdir(exist_ok=True)
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
def start(sn,role,run,n,interval,length,ch,dest=0xffff,pan=0x1234,node=1):
 vals=[run,n,interval,length,ch,dest,pan,node]; cmds=[]
 for i,v in enumerate(vals): cmds.append(f'w4 0x{0x20009344+4*i:X} {v:#x}')
 cmds.append(f'w4 0x20009340 {role}'); command(sn,'\n'.join(cmds))
def stop(sn): command(sn,'w4 0x20009340 3')

run=0
try:
 for rep in range(3):
  for name,dest,tpan,rpan,node,expected in [('broadcast',65535,0x1234,0x1234,2,True),('unicast_match',2,0x1234,0x1234,2,True),('unicast_other',3,0x1234,0x1234,2,False),('broadcast_wrong_pan',65535,0x4321,0x1234,2,False),('broadcast_B_new_address',65535,0x1234,0x1234,3,True)]:
   run+=1;tx,rx=boards;n=1000;gap=500
   start(rx,1,run,n,gap,32,5,dest,rpan,node);time.sleep(.5)
   if read(rx)['state']!=1:raise RuntimeError('RX setup failed')
   start(tx,2,run,n,gap,32,5,dest,tpan,1)
   deadline=time.monotonic()+20
   while True:
    time.sleep(.5);ts=read(tx)
    if ts['state']==3:break
    if ts['state']!=2 or time.monotonic()>deadline:raise RuntimeError(str(ts))
   time.sleep(.5);stop(rx);rs=read(rx)
   row=dict(run=run,repeat=rep,name=name,destination=dest,tx_pan=tpan,rx_pan=rpan,rx_address=node,expected_receive=expected,tx=ts,rx=rs,pdr=rs['rx']/ts['tx'])
   with (out/'results.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
   print(json.dumps(row),flush=True)
except Exception as e:
 (out/'error.txt').write_text(str(e));print('ERROR',e,flush=True)
finally:
 for sn in boards:
  try:stop(sn)
  except Exception:pass
