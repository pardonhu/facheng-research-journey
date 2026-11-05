from pathlib import Path
import subprocess,time,json,hashlib,ctypes,traceback,zipfile,sys
root=Path.cwd();out=Path((root/'work/raw48-latest.txt').read_text()) if '--resume' in sys.argv else root/'outputs'/('raw48-study-'+time.strftime('%Y%m%d-%H%M%S'));out.mkdir(exist_ok=True)
(root/'work/raw48-latest.txt').write_text(str(out))
jlink=r'D:\Program Files\SEGGER\JLink_V990\JLink.exe'
build=root/'work/toolnail-UWB/DW3_QM33_SDK_1.1.1/Drivers/API/Build_Platforms/nRF52832-Raw48/build'
raw=subprocess.check_output([str(root/'work/arm-gcc/bin/arm-none-eabi-nm.exe'),str(build/'uwb-raw48.elf')],text=True)
symbols={s.split()[2]:int(s.split()[0],16) for s in raw.splitlines() if len(s.split())==3}
boards=[dict(label='A',serial='JLINK_A'),dict(label='B',serial='JLINK_B')]
class Stats(ctypes.Structure):
 _fields_=[(n,ctypes.c_uint32) for n in 'state devid unique first_unique missing tx_frames rx_frames retries invalid phy_errors timeouts late_tx elapsed_us round_max_us first_missing injected_drops'.split()]+[(n,ctypes.c_uint64) for n in ['round_sum_us','spacing_sum_dtu']]+[(n,ctypes.c_uint32) for n in ['spacing_count','spacing_min_us','spacing_max_us']]+[(n,ctypes.c_int32) for n in ['gap_min_ns','gap_max_ns']]+[('gap_sum_ns',ctypes.c_int64),('gap_count',ctypes.c_uint32)]
def command(b,cmd):
 f=out/f"command-{b['label']}.jlink";f.write_text('connect\n'+cmd+'\nexit\n')
 for attempt in range(4):
  r=subprocess.run([jlink,'-SelectEmuBySN',b['serial'],'-Device','nRF52832_xxAA','-If','SWD','-Speed','1000','-AutoConnect','0','-ExitOnError','1','-CommandFile',str(f)],capture_output=True,text=True,timeout=50)
  (out/f"last-{b['label']}.log").write_text(r.stdout+r.stderr)
  if not r.returncode and 'Could not read memory' not in r.stdout and 'Cannot connect to the probe' not in r.stdout:return r.stdout
  with (out/'connection-retries.jsonl').open('a') as log:log.write(json.dumps(dict(board=b['label'],attempt=attempt,output=r.stdout+r.stderr))+'\n')
  time.sleep(1)
 raise RuntimeError(r.stdout+r.stderr)
def read(b,symbol='stats',n=None):
 n=n or ctypes.sizeof(Stats);f=out/f"read-{b['label']}-{symbol}.bin"
 command(b,f'savebin {f.as_posix()} {symbols[symbol]:#x} {n:#x}')
 data=f.read_bytes();assert len(data)==n
 if symbol!='stats':return data
 s=Stats.from_buffer_copy(data);return {n:getattr(s,n) for n,t in Stats._fields_}
def stop(b):command(b,f"h\nw4 {symbols['control']:#x} 3\ng")
def start(b,role,run,n,pre,fast,wait,drop):
 vals=[run,n,pre,fast,wait,5,drop]
 cmds=['r','g','sleep 100','h']+[f"w4 {symbols['control']+4*(i+1):#x} {v:#x}" for i,v in enumerate(vals)]+[f"w4 {symbols['control']:#x} {role}",'g']
 command(b,'\n'.join(cmds))
def case(name,pre,fast,wait,n=10000,drop=0,reverse=False,formal=True):
 if (root/'work/STOP-RAW48').exists():raise KeyboardInterrupt
 tx,rx=boards[::-1] if reverse else boards
 run=time.time_ns()&0xffffffff
 start(rx,1,run,n,pre,fast,wait,drop);time.sleep(.2)
 s=read(rx);assert s['state']==1 and s['devid']==0xdeca0302,(rx,s)
 start(tx,2,run,n,pre,fast,wait,drop)
 (out/'status.json').write_text(json.dumps(dict(state='running',case=name)))
 deadline=time.monotonic()+240
 while True:
  time.sleep(1 if n<1000 else 3)
  s=read(tx)
  if s['state']!=2:break
  if time.monotonic()>deadline:raise RuntimeError(('timeout',name,s))
 assert s['state']==3 and s['unique']+s['missing']==n,s
 stop(rx);r=read(rx);bitmap=read(tx,'received',(n+7)//8)
 assert sum((bitmap[i//8]>>(i%8))&1 for i in range(n))==s['unique']
 (out/(name+'-received.bin')).write_bytes(bitmap)
 row=dict(name=name,formal=formal,count=n,preamble=pre,fast_phr=fast,reply_gap_us=wait,drop_every=drop,direction=tx['label']+' requests '+rx['label'],root=s,responder=r,pdr=s['unique']/n,first_pdr=s['first_unique']/n,mean_round_us=s['round_sum_us']/n,elapsed_s=s['elapsed_us']/1e6,mean_rx_spacing_us=s['spacing_sum_dtu']*10/638976/s['spacing_count'] if s['spacing_count'] else None,frame_bits=48,firmware_sha256=hashlib.sha256((build/'uwb-raw48.hex').read_bytes()).hexdigest())
 with (out/'results.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
 stop(tx)
 print(json.dumps({k:row[k] for k in ['name','count','first_pdr','pdr','mean_round_us','elapsed_s']}),flush=True)
 return row
try:
 # Read and preserve current flash and UICR before changing either board.
 for b in boards:
  f=out/f"{b['label']}-before-flash.bin";u=out/f"{b['label']}-before-uicr.bin"
  if not f.exists():command(b,f'h\nsavebin {f.as_posix()} 0 0x80000\nsavebin {u.as_posix()} 0x10001000 0x1000\ng')
  assert f.stat().st_size==0x80000 and u.stat().st_size==4096
  print('Backed up '+b['label'],flush=True)
 with zipfile.ZipFile(out/'source-and-firmware.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in [root/'work/raw48-body.c',root/'work/prepare-raw48.py',root/'work/run-raw48.py',build.parent/'main.c',build.parent/'build.py',build/'uwb-raw48.elf',build/'uwb-raw48.hex']:
   z.write(p,p.name if p.parent!=build.parent else 'platform/'+p.name)
 for b in boards:
  command(b,f'h\nloadfile {(build/"uwb-raw48.hex").as_posix()}\nr\ng\nsleep 100')
  print('Flashed '+b['label'],flush=True)
 screen=case('screen-p64-standard-gap500',64,0,500,n=100,formal=False)
 if screen['pdr']<.9:raise RuntimeError(('screen failed',screen))
 for pre,fast in [(64,0),(32,0),(64,1),(32,1)]:case(f'p{pre}-phr{fast}-gap500',pre,fast,500)
 usable=[]
 for wait in (50,100,150,200,300):
  r=case(f'screen-p32-fast-gap{wait}',32,1,wait,n=300,formal=False)
  if r['pdr']>=.99 and r['responder']['late_tx']==0:usable.append(wait)
 if usable:
  selected=min(usable)
  case(f'p32-fast-gap{selected}-formal',32,1,selected)
  case(f'p32-fast-gap{selected}-reverse',32,1,selected,reverse=True)
  case(f'p32-fast-gap{selected}-drop10pct',32,1,selected,drop=10)
 (out/'status.json').write_text(json.dumps(dict(state='complete',selected_gap_us=min(usable) if usable else None)))
except BaseException:
 (out/'error.txt').write_text(traceback.format_exc());print(traceback.format_exc(),flush=True);raise
finally:
 for b in boards:
  try:stop(b)
  except Exception:pass
