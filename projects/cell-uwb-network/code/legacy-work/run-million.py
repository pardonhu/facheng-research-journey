from pathlib import Path
import subprocess,time,struct,json,itertools
root=Path.cwd(); out=root/'outputs/million-packet-runs'; out.mkdir(exist_ok=True)
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
 for cycle in range(4):
  for channel in (5,):
   for length in (32,):
    for gap in (150,):
     for direction in (0,):
      if Path('work/STOP-MILLION').exists():raise KeyboardInterrupt
      run+=1;tx=boards[direction];rx=boards[1-direction];n=250000
      start(rx,1,run,n,gap,length,channel,65535,0x1234,2);time.sleep(.5)
      if read(rx)['state']!=1:raise RuntimeError('RX setup failed')
      start(tx,2,run,n,gap,length,channel,65535,0x1234,1)
      deadline=time.monotonic()+600
      while True:
       time.sleep(5)
       if Path('work/STOP-MILLION').exists():raise KeyboardInterrupt
       ts=read(tx);rs=read(rx)
       (out/'live.json').write_text(json.dumps(dict(run=run,cycle=cycle,tx=ts,rx=rs,channel=channel,length=length,gap=gap)))
       if ts['state']==3:break
       if ts['state']!=2 or time.monotonic()>deadline:raise RuntimeError(str(ts))
      time.sleep(.5);stop(rx);rs=read(rx)
      row=dict(run=run,cycle=cycle,tx_serial=tx,rx_serial=rx,channel=channel,frame_bytes=length,post_tx_gap_us=gap,destination=65535,pan=0x1234,tx=ts,rx=rs,pdr=rs['rx']/ts['tx'])
      with (out/'results.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
      print(json.dumps(row),flush=True)
except KeyboardInterrupt:print('STOP requested',flush=True)
except Exception as e:
 (out/'error.txt').write_text(str(e));print('ERROR',e,flush=True)
finally:
 for sn in boards:
  try:stop(sn)
  except Exception:pass
