from pathlib import Path
import subprocess,time,struct,json,argparse,random,math
root=Path.cwd(); out=root/'outputs/preamble-study';out.mkdir(exist_ok=True)
p=root/'work/toolnail-UWB/DW3_QM33_SDK_1.1.1/Drivers/API/Build_Platforms/nRF52832-Preamble/build'
jlink=r'D:\Program Files\SEGGER\JLink_V990\JLink.exe';boards=['JLINK_A','JLINK_B']
profile={'preamble':128,'payload':4}
fields='state run attempts retransmissions unique duplicates invalid phy_errors ack_requests ack_timeouts ack_missing remote_unique remote_failed summary_received completed elapsed first_unique recovered injected ack_dropped windows window_max_us tx_errors control_retries'.split()
symbols=subprocess.check_output([str(root/'work/arm-gcc/bin/arm-none-eabi-nm.exe'),str(p/'uwb-preamble.elf')],text=True)
addresses={s.split()[2]:int(s.split()[0],16) for s in symbols.splitlines() if len(s.split())==3}
def command(sn,cmds):
 f=root/f'work/preamble-{sn}.jlink';f.write_text('connect\n'+cmds+'\nexit\n')
 for attempt in range(2):
  r=subprocess.run([jlink,'-SelectEmuBySN',sn,'-Device','nRF52832_xxAA','-If','SWD','-Speed','1000','-AutoConnect','0','-ExitOnError','1','-CommandFile',str(f)],capture_output=True,text=True,timeout=40)
  (out/f'last-{sn}.log').write_text(r.stdout+r.stderr)
  if not r.returncode and 'O.K.' in r.stdout:return r.stdout
  if 'Connecting to J-Link ...FAILED' not in r.stdout:break
  time.sleep(1)
 raise RuntimeError(r.stdout+r.stderr)
def read_bytes(sn,symbol,n):
 f=root/f'work/preamble-{sn}-{symbol}.bin';command(sn,f'savebin {f.as_posix()} {addresses[symbol]:#x} {n:#x}');return f.read_bytes()
def words(sn,symbol,n):return list(struct.unpack('<'+'I'*n,read_bytes(sn,symbol,n*4)))
def read(sn):return dict(zip(fields,words(sn,'stats',len(fields))))
def stop(sn):command(sn,f'w4 {addresses["control"]:#x} 3')
def start(sn,role,run,n,gap,mode,batch,rounds=5):
 vals=[run,n,gap,5,0,0,rounds,role,mode,batch,profile['preamble'],profile['payload']]
 cmds=[f'w4 {addresses["control"]+4*(i+1):#x} {v:#x}' for i,v in enumerate(vals)]
 command(sn,'\n'.join(cmds+[f'w4 {addresses["control"]:#x} {role}']))
def stopped():return (root/'work/STOP-PREAMBLE').exists()
def quantile(a,q):
 a=sorted(a);return a[min(len(a)-1,max(0,math.ceil(q*len(a))-1))] if a else None
def run_case(name,n,gap,direction,mode,batch,stage,repeat=0):
 if stopped():raise KeyboardInterrupt
 tx,rx=boards[direction],boards[1-direction];run=int(time.time()*1000)&0xffffffff
 start(rx,1,run,n,gap,mode,batch);time.sleep(.1)
 assert read(rx)['state']==1,'RX initialization'
 started=time.time();start(tx,2,run,n,gap,mode,batch)
 status=dict(preamble=profile['preamble'],payload=profile['payload'],name=name,stage=stage,started=started,count=n,gap=gap,mode=mode,direction=direction,batch=batch)
 (out/'status.json').write_text(json.dumps(status))
 deadline=time.monotonic()+300
 # No debugger reads during the first estimated portion of transmission.
 remaining=min(120,n*(gap+500)/1e6)
 while remaining>0:
  dt=min(2,remaining);time.sleep(dt);remaining-=dt
  if stopped():raise KeyboardInterrupt
 while True:
  ts=read(tx)
  if ts['state']!=2:break
  status['tx']=ts;(out/'status.json').write_text(json.dumps(status))
  if time.monotonic()>deadline:raise RuntimeError('timeout')
  time.sleep(5)
  if stopped():raise KeyboardInterrupt
 rs=read(rx);stop(rx);stop(tx)
 assert ts['state']==3 and rs['state']==4 and ts['summary_received']==1,'session completion'
 assert ts['remote_unique']==rs['unique'] and ts['remote_failed']==n-rs['unique'],'delivery accounting'
 assert ts['attempts']==n if mode==0 else n<=ts['attempts']<=5*n,'attempt accounting'
 tm=words(tx,'timing',6);hist=words(tx,'interval_hist',2048)
 durations=words(tx,'batch_us',tm[5]);missing=words(tx,'batch_missing',tm[5])
 bitmap=read_bytes(rx,'received',(n+7)//8)
 (out/f'{name}-received.bin').write_bytes(bitmap)
 got=[bool(bitmap[i//8]&(1<<(i%8))) for i in range(n)]
 assert sum(got)==rs['unique'],'bitmap mismatch'
 longest=streak=0;loss_runs={}
 for v in got+[True]:
  if not v:streak+=1;longest=max(longest,streak)
  elif streak:loss_runs[streak]=loss_runs.get(streak,0)+1;streak=0
 batches=[]
 for k,us in enumerate(durations):
  begin=k*batch;end=min(n,begin+batch);lost=(end-begin)-sum(got[begin:end])
  batches.append(dict(size=end-begin,us=us,receiver_missing=lost,unconfirmed=missing[k],all_delivered=lost==0,deadline_confirmed=us<=100000 and lost==0 and (mode==0 or missing[k]==0)))
 assert sum(hist)==tm[0],'timestamp histogram mismatch'
 if mode==0:assert tm[0]==n-1,'timestamp sample count mismatch'
 total_ticks=tm[3]+(tm[4]<<32);mean=total_ticks/tm[0]/63897.6 if tm[0] else None
 row=dict(preamble=profile['preamble'],payload=profile['payload'],data_frame_bytes=27+profile['payload'],name=name,stage=stage,repeat=repeat,count=n,gap_us=gap,direction=direction,mode=mode,batch_size=batch,tx=ts,rx=rs,pdr=rs['unique']/n,mean_period_us=mean,min_period_us=tm[1]/63897.6,max_period_us=tm[2]/63897.6,interval_samples=tm[0],interval_hist_us=hist,longest_loss_run=longest,loss_run_counts=loss_runs,batches=batches)
 with (out/'results.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
 brief={k:row[k] for k in ('name','pdr','mean_period_us','longest_loss_run')};brief['elapsed_s']=ts['elapsed']/1e6
 print(json.dumps(brief),flush=True)
 (out/'last-complete.json').write_text(json.dumps(brief));return row
def existing():return [json.loads(x) for x in (out/'results.jsonl').read_text().splitlines()] if (out/'results.jsonl').exists() else []
