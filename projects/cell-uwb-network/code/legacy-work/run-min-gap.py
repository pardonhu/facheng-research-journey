from pathlib import Path
import subprocess,time,json,struct,hashlib,zipfile,traceback,sys
root=Path.cwd();out=Path((root/'work/min-gap-latest.txt').read_text()) if '--resume' in sys.argv else root/'outputs'/('min-gap-study-'+time.strftime('%Y%m%d-%H%M%S'));out.mkdir(exist_ok=True)
(root/'work/min-gap-latest.txt').write_text(str(out))
base=root/'work/toolnail-UWB/DW3_QM33_SDK_1.1.1/Drivers/API/Build_Platforms';jlink=r'D:\Program Files\SEGGER\JLink_V990\JLink.exe'
boards=[dict(label='A',serial='JLINK_A',chip='52832'),dict(label='B',serial='JLINK_B',chip='52832'),dict(label='C',serial='JLINK_C',chip='52840'),dict(label='D',serial='JLINK_D',chip='52840')]
boards=[boards[2],boards[0],boards[1],boards[3]]
fields='state devid unique first_unique missing tx_frames rx_frames invalid phy_errors overruns late_tx retries elapsed_us first_pass_us batches duplicates dt_min_ns dt_max_ns dt_count node_0 node_1 node_2'.split()
for b in boards:
 b['build']=base/f"nRF{b['chip']}-MinGap/build"
 raw=subprocess.check_output([str(root/'work/arm-gcc/bin/arm-none-eabi-nm.exe'),str(b['build']/'uwb-min-gap.elf')],text=True)
 b['symbols']={l.split()[2]:int(l.split()[0],16) for l in raw.splitlines() if len(l.split())==3}
def command(b,cmd):
 f=out/f"command-{b['label']}.jlink";f.write_text('connect\n'+cmd+'\nexit\n')
 for attempt in range(4):
  device=f"nRF{b['chip']}_xxAA" if 'loadfile' in cmd or b['chip']=='52832' else 'Cortex-M4'
  r=subprocess.run([jlink,'-SelectEmuBySN',b['serial'],'-Device',device,'-If','SWD','-Speed','1000','-AutoConnect','0','-ExitOnError','1','-CommandFile',str(f)],capture_output=True,text=True,timeout=50)
  (out/f"last-{b['label']}.log").write_text(r.stdout+r.stderr)
  if not r.returncode and 'Could not read memory' not in r.stdout and 'Cannot connect to the probe' not in r.stdout:return r.stdout
  time.sleep(1)
 raise RuntimeError(r.stdout+r.stderr)
def read(b,symbol='stats',n=None):
 n=n or 4*len(fields);f=out/f"read-{b['label']}-{symbol}.bin"
 command(b,f"savebin {f.as_posix()} {b['symbols'][symbol]:#x} {n:#x}")
 data=f.read_bytes();assert len(data)==n
 return dict(zip(fields,struct.unpack('<'+'I'*len(fields),data))) if symbol=='stats' else data
def stop(b):command(b,f"h\nw4 {b['symbols']['control']:#x} 3\ng")
def start(b,role,run,n,gap,batch,leaves,pre=32):
 rank=boards.index(b)-1
 vals=[run,n,pre,1,gap,max(rank,0),leaves,batch,4,500]
 cmds=['r','g','sleep 100','h']+[f"w4 {b['symbols']['control']+4*(i+1):#x} {v:#x}" for i,v in enumerate(vals)]+[f"w4 {b['symbols']['control']:#x} {role}",'g']
 command(b,'\n'.join(cmds))
def case(name,gap,n=10000,batch=300,leaves=3,formal=True,pre=32):
 if (root/'work/STOP-MIN-GAP').exists():raise KeyboardInterrupt
 run=time.time_ns()&0xffffffff
 for b in boards[1:1+leaves]:
  start(b,1,run,n,gap,batch,leaves,pre=pre);time.sleep(.1);s=read(b);assert s['state']==1 and s['devid']==0xdeca0302,(b,s)
 start(boards[0],2,run,n,gap,batch,leaves,pre=pre);deadline=time.monotonic()+100
 (out/'status.json').write_text(json.dumps(dict(state='running',case=name)))
 while True:
  time.sleep(.6 if n<1000 else 1);s=read(boards[0])
  if s['state']!=2:break
  if time.monotonic()>deadline:raise RuntimeError((name,s))
 assert s['state']==3 and s['unique']+s['missing']==n,s
 snaps={boards[0]['label']:s}
 for b in boards[1:1+leaves]:stop(b);snaps[b['label']]=read(b)
 bits=read(boards[0],'received',(n+7)//8);assert sum((bits[i//8]>>(i%8))&1 for i in range(n))==s['unique']
 assert sum(s[f'node_{i}'] for i in range(leaves))==s['unique']
 (out/(name+'-received.bin')).write_bytes(bits)
 row=dict(name=name,formal=formal,target=n,preamble=pre,gap_us=gap,slot_us=(pre+8)*1.01763+117*.12821+gap,batch=batch,leaves=leaves,pdr=s['unique']/n,first_pdr=s['first_unique']/n,mean_record_us=s['elapsed_us']/n,first_pass_us=s['first_pass_us'],elapsed_us=s['elapsed_us'],stats=snaps,firmware_sha256={b['label']:hashlib.sha256((b['build']/'uwb-min-gap.hex').read_bytes()).hexdigest() for b in boards})
 row['profile']={b['label']:list(struct.unpack('<16I',read(b,'profile',64))) for b in boards[:1+leaves]}
 row['batch_time_us']=list(struct.unpack('<'+'I'*s['batches'],read(boards[0],'batch_time_us',4*s['batches'])))
 row['batch_first_missing']=list(struct.unpack('<'+'I'*s['batches'],read(boards[0],'batch_missing',4*s['batches'])))
 with (out/'results.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
 print(json.dumps({k:row[k] for k in ['name','first_pdr','pdr','mean_record_us','elapsed_us']}),flush=True);stop(boards[0]);return row
try:
 for b in boards:
  f=out/f"{b['label']}-before-flash.bin";u=out/f"{b['label']}-before-uicr.bin";size=0x80000 if b['chip']=='52832' else 0x100000
  if not f.exists():command(b,f'h\nsavebin {f.as_posix()} 0 {size:#x}\nsavebin {u.as_posix()} 0x10001000 0x1000\ng')
  assert f.stat().st_size==size and u.stat().st_size==4096;print('Backed up '+b['label'],flush=True)
 for b in boards:
  command(b,f'h\nloadfile {(b["build"]/"uwb-min-gap.hex").as_posix()}\nr\ng\nsleep 100');print('Flashed '+b['label'],flush=True)
 screen=case('screen-gap500',500,n=300,formal=False)
 if screen['pdr']<.9:raise RuntimeError(('initial screen failed',screen))
 scanned=[]
 for gap in (200,100,50,20,10,5,2,1,0):scanned.append(case(f'screen-gap{gap}',gap,n=600,formal=False))
 # Confirm the shortest setting, the fastest screened setting including retries,
 # and an adjacent setting using 10000 data records each.
 good=[r for r in scanned if r['pdr']==1]
 picks={0, min(good,key=lambda r:r['mean_record_us'])['gap_us']} if good else {0,50}
 best=min(picks)
 picks.add(next((x for x in (1,2,5,10,20,50,100,200) if x>best),500))
 for gap in sorted(picks):case(f'formal-gap{gap}',gap)
 (out/'status.json').write_text(json.dumps(dict(state='complete')))
except BaseException:
 (out/'error.txt').write_text(traceback.format_exc());print(traceback.format_exc(),flush=True);raise
finally:
 for b in boards:
  try:stop(b)
  except Exception:pass
