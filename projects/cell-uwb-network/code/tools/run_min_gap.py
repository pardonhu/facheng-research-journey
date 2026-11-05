"""Run one explicit four-board MinGap test. --help never accesses hardware."""
from pathlib import Path
import argparse,subprocess,time,json,struct,hashlib,traceback
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--config',type=Path,required=True)
mode=parser.add_mutually_exclusive_group(required=True)
mode.add_argument('--flash',action='store_true',help='back up flash/UICR, then load archived test firmware')
mode.add_argument('--use-installed',action='store_true',help='use previously loaded matching MinGap firmware')
parser.add_argument('--gap-us',type=int,required=True)
parser.add_argument('--preamble',type=int,choices=[32,64,128],required=True)
parser.add_argument('--count',type=int,default=10000)
parser.add_argument('--batch',type=int,default=300)
args=parser.parse_args()
if not 1<=args.count<=10000 or not 1<=args.batch<=300 or not 0<=args.gap_us<=10000:parser.error('count 1..10000, batch 1..300, gap 0..10000 required')
root=Path(__file__).resolve().parents[2]
cfg=json.loads(args.config.read_text(encoding='utf-8'))
jlink=cfg['jlink_exe'];toolchain=Path(cfg['arm_gcc_bin'])
nm=next((p for p in [toolchain/'arm-none-eabi-nm.exe',toolchain/'arm-none-eabi-nm'] if p.is_file()),None)
if nm is None:raise FileNotFoundError('arm-none-eabi-nm')
if not Path(jlink).is_file():raise FileNotFoundError(jlink)
boards=cfg['boards'];center=cfg.get('center','C');boards=sorted(boards,key=lambda b:b['label']!=center)
if len(boards)!=4 or boards[0]['label']!=center:raise ValueError('one center and three leaf boards required')
for b in boards:
 if b['chip'] not in ('52832','52840') or not str(b['serial']).isdigit():raise ValueError('fill actual local board chip and serial')
 b['serial']=str(b['serial'])
base=root/'code/firmware/platforms'
out=root/'runs'/time.strftime('%Y%m%d-%H%M%S');out.mkdir(parents=True)
fields='state devid unique first_unique missing tx_frames rx_frames invalid phy_errors overruns late_tx retries elapsed_us first_pass_us batches duplicates dt_min_ns dt_max_ns dt_count node_0 node_1 node_2'.split()
for b in boards:
 b['build']=base/f"nRF{b['chip']}-MinGap/build"
 raw=subprocess.check_output([str(nm),str(b['build']/'uwb-min-gap.elf')],text=True)
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
 command(b,f'savebin "{f.as_posix()}" {b["symbols"][symbol]:#x} {n:#x}')
 data=f.read_bytes();assert len(data)==n
 return dict(zip(fields,struct.unpack('<'+'I'*len(fields),data))) if symbol=='stats' else data
def stop(b):command(b,f"h\nw4 {b['symbols']['control']:#x} 3\ng")
def start(b,role,run,n,gap,batch,leaves,pre=32):
 rank=boards.index(b)-1
 vals=[run,n,pre,1,gap,max(rank,0),leaves,batch,4,500]
 cmds=['r','g','sleep 100','h']+[f"w4 {b['symbols']['control']+4*(i+1):#x} {v:#x}" for i,v in enumerate(vals)]+[f"w4 {b['symbols']['control']:#x} {role}",'g']
 command(b,'\n'.join(cmds))
def case(name,gap,n=10000,batch=300,leaves=3,formal=True,pre=32):
 if (out/'STOP').exists():raise KeyboardInterrupt
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
 if args.flash:
  for b in boards:
   f=out/f"{b['label']}-before-flash.bin";u=out/f"{b['label']}-before-uicr.bin";size=0x80000 if b['chip']=='52832' else 0x100000
   command(b,f'h\nsavebin "{f.as_posix()}" 0 {size:#x}\nsavebin "{u.as_posix()}" 0x10001000 0x1000\ng')
   assert f.stat().st_size==size and u.stat().st_size==4096
  for b in boards:
   image=b['build']/'uwb-min-gap.hex'
   command(b,f'h\nloadfile "{image.as_posix()}"\nr\ng\nsleep 100')
 case(f"p{args.preamble}-gap{args.gap_us}",args.gap_us,n=args.count,batch=args.batch,pre=args.preamble,formal=args.count==10000)
 (out/'status.json').write_text(json.dumps(dict(state='complete')))
except BaseException:
 (out/'error.txt').write_text(traceback.format_exc());raise
finally:
 for b in boards:
  try:stop(b)
  except Exception:pass
