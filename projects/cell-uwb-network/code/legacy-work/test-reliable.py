from pathlib import Path
import subprocess,time,struct,json,argparse
root=Path.cwd(); out=root/'outputs/reliable-runs'; out.mkdir(exist_ok=True)
p=root/'work/toolnail-UWB/DW3_QM33_SDK_1.1.1/Drivers/API/Build_Platforms/nRF52832-Reliable/build'
jlink=r'D:\Program Files\SEGGER\JLink_V990\JLink.exe'
boards=['JLINK_A','JLINK_B']
fields='state run attempts retransmissions unique duplicates invalid phy_errors ack_requests ack_timeouts ack_missing remote_unique remote_failed summary_received completed elapsed first_unique recovered injected ack_dropped windows window_max_us tx_errors control_retries'.split()
symbols=subprocess.check_output([str(root/'work/arm-gcc/bin/arm-none-eabi-nm.exe'),str(p/'uwb-reliable.elf')],text=True)
addresses={line.split()[2]:int(line.split()[0],16) for line in symbols.splitlines() if len(line.split())==3}
def command(sn,cmds):
 f=root/f'work/reliable-{sn}.jlink'; f.write_text('connect\n'+cmds+'\nexit\n')
 r=subprocess.run([jlink,'-SelectEmuBySN',sn,'-Device','nRF52832_xxAA','-If','SWD','-Speed','1000','-AutoConnect','0','-ExitOnError','1','-CommandFile',str(f)],capture_output=True,text=True,timeout=40)
 (out/f'last-{sn}.log').write_text(r.stdout+r.stderr)
 if r.returncode or 'O.K.' not in r.stdout: raise RuntimeError(r.stdout+r.stderr)
 return r.stdout
def read(sn):
 f=root/f'work/reliable-stat-{sn}.bin';command(sn,f'savebin {f.as_posix()} {addresses["stats"]:#x} {len(fields)*4:#x}')
 return dict(zip(fields,struct.unpack('<'+'I'*len(fields),f.read_bytes())))
def start(sn,role,run,n,gap,inj,ack,rounds):
 vals=[run,n,gap,5,inj,ack,rounds];cmds=[f'w4 {addresses["control"]+4*(i+1):#x} {v:#x}' for i,v in enumerate(vals)]
 command(sn,'\n'.join(cmds+[f'w4 {addresses["control"]:#x} {role}']))
def stop(sn):command(sn,f'w4 {addresses["control"]:#x} 3')
def run_case(name,n=100000,inj=0,ack=0,rounds=5,direction=0,gap=150):
 tx,rx=boards[direction],boards[1-direction]; run=int(time.time())&0xffffffff
 start(rx,1,run,n,gap,inj,ack,rounds);time.sleep(.2)
 assert read(rx)['state']==1,'receiver setup failed'
 start(tx,2,run,n,gap,0,0,rounds);deadline=time.monotonic()+300
 while True:
  time.sleep(2)
  if (root/'work/STOP-RELIABLE').exists(): raise KeyboardInterrupt
  ts=read(tx)
  if ts['state']!=2: break
  if time.monotonic()>deadline: raise RuntimeError('test deadline exceeded')
  (out/'live.json').write_text(json.dumps(dict(name=name,tx=ts)))
 rs=read(rx)
 row=dict(name=name,count=n,injection=inj,ack_drop=ack,rounds=rounds,gap_us=gap,tx_serial=tx,rx_serial=rx,tx=ts,rx=rs)
 with (out/'results.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
 print(json.dumps(row),flush=True)
 stop(tx); stop(rx)
 assert ts['state']==3 and ts['summary_received']==1 and rs['state']==4,'protocol did not complete'
 assert ts['remote_unique']==rs['unique'] and rs['unique']+ts['remote_failed']==n,'summary mismatch'
 assert rs['first_unique']+rs['recovered']==rs['unique'],'recovery accounting mismatch'
 assert ts['attempts']<=n*rounds and ts['completed']==n,'attempt bound failed'
 if inj==2: assert rs['unique']<=n-(n+9)//10 and ts['remote_failed']>0,'permanent loss unreported'
 elif inj==1 and rounds>1: assert rs['recovered']>0 and ts['retransmissions']>0,'recovery not exercised'
 if ack: assert rs['ack_dropped']>0 and ts['ack_timeouts']>0,'ACK loss not exercised'
 return row
if __name__=='__main__':
 a=argparse.ArgumentParser(); a.add_argument('--flash',action='store_true');a.add_argument('--suite',choices=['smoke','full'],default='smoke');args=a.parse_args()
 if args.flash:
  for sn in boards:
   log=command(sn,f'h\nloadfile {(p/"uwb-reliable.hex").as_posix()}\nr\ng')
   (out/f'flash-{sn}.log').write_text(log)
   assert 'O.K.' in log
 try:
  if args.suite=='smoke':
   run_case('smoke',1000)
   run_case('first-loss',1003,inj=1)
   run_case('ack-loss',1003,ack=1)
   run_case('permanent-loss',1003,inj=2)
  else:
   run_case('natural-A-B')
   run_case('natural-B-A',direction=1)
   run_case('first-loss-10pct',inj=1)
   run_case('ack-loss-every10windows',ack=10)
   run_case('first-loss-no-retry',inj=1,rounds=1)
 finally:
  for sn in boards:
   try:stop(sn)
   except Exception:pass
