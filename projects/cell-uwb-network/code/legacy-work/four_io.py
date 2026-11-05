from pathlib import Path
import subprocess,time,struct,json,math,hashlib
root=Path.cwd();out=root/'outputs/four-board-study';out.mkdir(exist_ok=True)
base=root/'work/toolnail-UWB/DW3_QM33_SDK_1.1.1/Drivers/API/Build_Platforms'
jlink=r'D:\Program Files\SEGGER\JLink_V990\JLink.exe'
boards=[dict(label='A',serial='JLINK_A',chip='52832',node=1),dict(label='B',serial='JLINK_B',chip='52832',node=2),dict(label='C',serial='JLINK_C',chip='52840',node=3),dict(label='D',serial='JLINK_D',chip='52840',node=4)]
fields='state run devid rounds unique first_unique missing tx_frames tx_data tx_poll tx_ack rx_frames duplicates invalid phy_errors filtered timeouts late_tx requests retries elapsed round_max round_sum_lo round_sum_hi hist_rounds rounds_all rounds_deadline quiet_skips relay_collections relay_forwards'.split()+[f'node_{kind}_{i}' for kind in ('unique','first','missing') for i in (2,3,4)]
for b in boards:
 b['build']=base/f"nRF{b['chip']}-Four/build"
 raw=subprocess.check_output([str(root/'work/arm-gcc/bin/arm-none-eabi-nm.exe'),str(b['build']/'uwb-four.elf')],text=True)
 b['symbols']={s.split()[2]:int(s.split()[0],16) for s in raw.splitlines() if len(s.split())==3}
def command(b,cmds):
 f=root/f"work/four-{b['label']}.jlink";f.write_text('connect\n'+cmds+'\nexit\n')
 for attempt in range(2):
  device=f"nRF{b['chip']}_xxAA" if 'loadfile' in cmds or b['chip']=='52832' else 'Cortex-M4'
  p=subprocess.run([jlink,'-SelectEmuBySN',b['serial'],'-Device',device,'-If','SWD','-Speed','1000','-AutoConnect','0','-ExitOnError','1','-CommandFile',str(f)],capture_output=True,text=True,timeout=50)
  (out/f"last-{b['label']}.log").write_text(p.stdout+p.stderr)
  if p.returncode==0 and 'O.K.' in p.stdout and 'Could not read memory' not in p.stdout:return p.stdout
  time.sleep(1)
 raise RuntimeError(p.stdout+p.stderr)
def rawread(b,symbol,n):
 f=root/f"work/four-{b['label']}-{symbol}.bin";command(b,f"savebin {f.as_posix()} {b['symbols'][symbol]:#x} {n:#x}");return f.read_bytes()
def read(b):return dict(zip(fields,struct.unpack('<'+'I'*len(fields),rawread(b,'stats',4*len(fields)))))
def stop(b):command(b,f"h\nw4 {b['symbols']['control']:#x} 3\ng")
def start(b,role,run,n,mode,mask,guard,turn,attempts,quiet=None):
 parent=2 if mode>=2 and b['node']>=3 else 1
 qfrom,qlen=(quiet[1],quiet[2]) if quiet and quiet[0]==b['node'] else (0,0)
 values=[run,n,mode,b['node'],parent,136+guard,turn,attempts,mask,qfrom,qlen]
 cmds=[f"w4 {b['symbols']['control']+4*(i+1):#x} {v:#x}" for i,v in enumerate(values)]
 command(b,'\n'.join(['r','g','sleep 100','h']+cmds+[f"w4 {b['symbols']['control']:#x} {role}",'g']))
def flash():
 for b in boards:
  log=command(b,f"h\nloadfile {(b['build']/'uwb-four.hex').as_posix()}\nr\ng\nsleep 200")
  (out/f"flash-{b['label']}.log").write_text(log)
def run_case(name,mode,n=100000,mask=7,guard=500,turn=1000,attempts=5,quiet=None,formal=True):
 if (root/'work/STOP-FOUR').exists():raise KeyboardInterrupt
 run=int(time.time()*1000)&0xffffffff
 for b in boards[1:]:
  for init_attempt in range(3):
   start(b,1,run,n,mode,mask,guard,turn,attempts,quiet)
   time.sleep(.3)
   s=read(b)
   if s['state']==1 and s['devid']==0xdeca0302:break
   with (out/'initialization-events.jsonl').open('a') as f:f.write(json.dumps(dict(board=b['label'],run=run,attempt=init_attempt,stats=s))+'\n')
  assert s['state']==1 and s['devid']==0xdeca0302,(b['label'],s)
 start(boards[0],2,run,n,mode,mask,guard,turn,attempts)
 status=dict(state='running',name=name,mode=mode,count=n,mask=mask,guard_us=guard,turn_us=turn,run=run,formal=formal,started=time.time())
 (out/'status.json').write_text(json.dumps(status));deadline=time.monotonic()+1800
 while True:
  time.sleep(2 if n<10000 else 15)
  if (root/'work/STOP-FOUR').exists():raise KeyboardInterrupt
  s=read(boards[0]);status['root']=s;(out/'status.json').write_text(json.dumps(status))
  if s['state']!=2:break
  if time.monotonic()>deadline:raise RuntimeError('test exceeded 30min')
 assert s['state']==3 and s['devid']==0xdeca0302,s
 # Freeze all responders before final snapshots.
 for b in boards[1:]:stop(b)
 snapshots={'A':s}
 for b in boards[1:]:snapshots[b['label']]=read(b)
 bitmap=rawread(boards[0],'received',(n+7)//8);(out/f'{name}-received.bin').write_bytes(bitmap)
 got=sum((bitmap[i//8]>>(i%8))&1 for i in range(n));assert got==s['unique'] and got+s['missing']==n,'delivery accounting mismatch'
 assert sum(s[f'node_unique_{i}'] for i in (2,3,4))==got
 hist=list(struct.unpack('<4096I',rawread(boards[0],'round_hist',4096*4)));assert sum(hist)==s['hist_rounds']
 def percentile(q):
  wanted=math.ceil(sum(hist)*q);acc=0
  for i,v in enumerate(hist):
   acc+=v
   if acc>=wanted:return dict(lower_us=i*25,upper_us=(i+1)*25 if i<4095 else None)
 row=dict(firmware_sha256={b['label']:hashlib.sha256((b['build']/'uwb-four.hex').read_bytes()).hexdigest() for b in boards},name=name,mode=mode,target=n,mask=mask,guard_us=guard,turn_us=turn,max_attempts=attempts,quiet=quiet,formal=formal,boards=snapshots,pdr=got/n,first_pdr=s['first_unique']/n,round_mean_us=(s['round_sum_lo']+(s['round_sum_hi']<<32))/s['hist_rounds'],round_p95=percentile(.95),round_p99=percentile(.99),round_hist_25us=hist,all_round_rate=s['rounds_all']/s['hist_rounds'],deadline_100ms=s['rounds_deadline']/s['hist_rounds'])
 with (out/'results.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
 print(json.dumps({k:row[k] for k in ('name','pdr','first_pdr','round_mean_us','round_p95','all_round_rate')}),flush=True)
 stop(boards[0]);return row
