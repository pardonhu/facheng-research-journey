from pathlib import Path
import subprocess,time,struct,json,hashlib,math,traceback,argparse
root=Path.cwd();out=root/'outputs/ble-matched-study';p=root/'work/toolnail-UWB/DW3_QM33_SDK_1.1.1/Drivers/API/Build_Platforms/nRF52832-Matched/build';jlink=r'D:\Program Files\SEGGER\JLink_V990\JLink.exe';boards={'A':'JLINK_A','B':'JLINK_B'}
raw=subprocess.check_output([str(root/'work/arm-gcc/bin/arm-none-eabi-nm.exe'),str(p/'uwb-matched.elf')],text=True);symbols={s.split()[2]:int(s.split()[0],16) for s in raw.splitlines() if len(s.split())==3}
fields='state run devid tx_data tx_poll rx_data rx_poll unique first_unique duplicates invalid phy_errors poll_dropped data_dropped late_tx tx_errors timeouts completed failed elapsed batches period_n period_min period_max period_lo period_hi'.split()
def command(label,cmds):
 f=root/f'work/matched-{label}.jlink';f.write_text('connect\n'+cmds+'\nexit\n')
 for attempt in range(4):
  r=subprocess.run([jlink,'-SelectEmuBySN',boards[label],'-Device','nRF52832_xxAA','-If','SWD','-Speed','1000','-AutoConnect','0','-ExitOnError','1','-CommandFile',str(f)],capture_output=True,text=True,timeout=45);(out/f'last-{label}.log').write_text(r.stdout+r.stderr)
  if r.returncode==0:return r.stdout
  if 'FAILED: Cannot connect to the probe/programmer' not in r.stdout:break
  time.sleep(2)
 assert r.returncode==0,r.stdout[-2000:]
def readbytes(label,symbol,n):
 f=root/f'work/matched-{label}-{symbol}.bin';command(label,f'savebin {f.as_posix()} {symbols[symbol]:#x} {n:#x}');return f.read_bytes()
def read(label):return dict(zip(fields,struct.unpack('<26I',readbytes(label,'stats',104))))
def stop(label):command(label,f'h\nw4 {symbols["control"]:#x} 3\ng')
def flash():
 for b in boards:command(b,f'h\nloadfile {(p/"uwb-matched.hex").as_posix()}\nr\ng\nsleep 100')
def start(label,role,run,n,mode,pre,agg):
 values=[run,n,mode,1 if label=='A' else 2,pre,agg,150,100 if mode else 0,20261104,32,1000]
 cmds=['r','g','sleep 100','h']+[f'w4 {symbols["control"]+4*(i+1):#x} {v:#x}' for i,v in enumerate(values)]+[f'w4 {symbols["control"]:#x} {role}','g'];command(label,'\n'.join(cmds))
def case(pre,mode,agg,n=50000,formal=True):
 name=f'p{pre}-m{mode}-a{agg}'+('' if formal else '-smoke');run=int(time.time()*1000)&0xffffffff;controller='A' if mode==2 else 'B';receiver='B' if mode==2 else 'A';collector='A'
 start(receiver,1,run,n,mode,pre,agg);time.sleep(.2);assert read(receiver)['state']==1,read(receiver)
 start(controller,2,run,n,mode,pre,agg);status=dict(state='running',name=name,preamble=pre,mode=mode,aggregation=agg,count=n,formal=formal);(out/'status.json').write_text(json.dumps(status));deadline=time.monotonic()+1200
 while True:
  time.sleep(10 if formal else 1)
  if (root/'work/STOP-MATCHED').exists():raise KeyboardInterrupt
  s=read(controller);status['progress']=s;(out/'status.json').write_text(json.dumps(status))
  if s['state']!=2:break
  assert time.monotonic()<deadline,'case timeout'
 assert s['state']==3,s
 return collect(pre,mode,agg,n,formal,s)

def collect(pre,mode,agg,n,formal,s):
 name=f'p{pre}-m{mode}-a{agg}'+('' if formal else '-smoke');controller='A' if mode==2 else 'B';collector='A'
 time.sleep(.1)
 for b in boards:stop(b)
 snaps={b:read(b) for b in boards};rx=snaps[collector];bitmap=readbytes(collector,'received',(n+7)//8);assert sum(x.bit_count() for x in bitmap)==rx['unique'];assert s['completed']==n
 if mode==2:assert rx['unique']+s['failed']==n
 else:assert s['tx_data']==n*(5 if mode==1 else 1)
 (out/f'{name}-received.bin').write_bytes(bitmap);batch=300//agg;dur=list(struct.unpack('<'+'I'*s['batches'],readbytes(controller,'batch_us',s['batches']*4)));hist=list(struct.unpack('<2048I',readbytes(controller,'period_hist',8192)));assert sum(hist)==s['period_n']
 cycles=[]
 for k,us in enumerate(dur):
  first=k*batch;end=min(first+batch,n);lost=sum(not(bitmap[i//8]&(1<<(i%8))) for i in range(first,end));cycles.append(dict(packets=end-first,records=(end-first)*agg,us=us,missing_packets=lost))
 row=dict(name=name,formal=formal,preamble=pre,mode=mode,aggregation=agg,count=n,ifs_requested_us=150,loss_permille=100 if mode else 0,seed=20261104,poll_timeout_us=1000,frame_bytes=30+(30*agg+7)//8,poll_bytes=30,controller=controller,boards=snaps,pdr=rx['unique']/n,elapsed_us=s['elapsed'],period_mean_us=(s['period_lo']+(s['period_hi']<<32))/s['period_n']/63897.6 if s['period_n'] else None,cycles=cycles,period_hist=hist,firmware_sha256=hashlib.sha256((p/'uwb-matched.hex').read_bytes()).hexdigest())
 with (out/'results.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
 print(json.dumps({k:row[k] for k in ('name','pdr','elapsed_us','period_mean_us')}),flush=True)
 return row
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--flash',action='store_true');a.add_argument('--smoke',action='store_true');a.add_argument('--resume',action='store_true');a.add_argument('--preambles',default='128,64,32');args=a.parse_args()
 try:
  if args.flash:flash()
  for pre in map(int,args.preambles.split(',')):
   for mode,agg in ((0,1),(0,10),(1,1),(2,1),(2,10)):
    if args.resume and any(r['name']==f'p{pre}-m{mode}-a{agg}' and r['formal'] for r in map(json.loads,(out/'results.jsonl').read_text().splitlines())):continue
    case(pre,mode,agg,n=600 if args.smoke else 50000,formal=not args.smoke)
  (out/'status.json').write_text(json.dumps(dict(state='smoke_complete' if args.smoke else 'complete',completed=time.time())))
 except BaseException:
  (out/'error.txt').write_text(traceback.format_exc());raise
 finally:
  for b in boards:
   try:stop(b)
   except Exception:pass
