from pathlib import Path
import subprocess,json,hashlib,time,zipfile
root=Path.cwd();out=root/'outputs/lean-rerun-study';j=r'D:\Program Files\SEGGER\JLink_V990\JLink.exe';records=[];out.mkdir(exist_ok=True)
for label,sn,size in [('A','JLINK_A',0x80000),('B','JLINK_B',0x80000),('C','JLINK_C',0x100000),('D','JLINK_D',0x100000)]:
 f=out/f'{label}-before-flash.bin';u=out/f'{label}-before-uicr.bin'
 if not f.exists():
  script=root/f'work/lean-backup-{label}.jlink';script.write_text(f'connect\nh\nsavebin {f.as_posix()} 0 {size:#x}\nsavebin {u.as_posix()} 0x10001000 0x1000\ng\nexit\n')
  for attempt in range(4):
   r=subprocess.run([j,'-SelectEmuBySN',sn,'-Device','Cortex-M4','-If','SWD','-Speed','1000','-AutoConnect','0','-ExitOnError','1','-CommandFile',str(script)],capture_output=True,text=True,timeout=50);(out/f'{label}-backup.log').write_text(r.stdout+r.stderr)
   if r.returncode==0:break
   time.sleep(2)
  assert r.returncode==0,r.stdout
 assert f.stat().st_size==size and u.stat().st_size==4096
 records.append(dict(board=label,serial=sn,flash_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),uicr_sha256=hashlib.sha256(u.read_bytes()).hexdigest()))
 print('Backed up',label,flush=True)
(out/'backup-manifest.json').write_text(json.dumps(records,indent=2))
with zipfile.ZipFile(out/'before-source.zip','w',zipfile.ZIP_DEFLATED) as z:
 for name in ('broadcast-tree-body.c','broadcast_tree_io.py','run-broadcast-tree.py','prepare-broadcast-tree.py','verify-broadcast-tree.py'):z.write(root/'work'/name,name)
