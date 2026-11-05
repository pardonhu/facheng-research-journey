from pathlib import Path
import subprocess,json,hashlib
root=Path.cwd();out=root/'outputs/four-board-study';out.mkdir(exist_ok=True)
j=r'D:\Program Files\SEGGER\JLink_V990\JLink.exe'
records=[]
for label,sn,size in [('A','JLINK_A',0x80000),('B','JLINK_B',0x80000),('C','JLINK_C',0x100000),('D','JLINK_D',0x100000)]:
 flash=out/f'{label}-before-fourboard-flash.bin';uicr=out/f'{label}-before-fourboard-uicr.bin'
 if flash.exists() or uicr.exists():raise RuntimeError('Backup already exists; refusing overwrite: '+label)
 script=root/f'work/backup-four-{label}.jlink'
 script.write_text(f'connect\nr\nh\nmem32 0x10000100 5\nsavebin {flash.as_posix()} 0 {size:#x}\nsavebin {uicr.as_posix()} 0x10001000 0x1000\ng\nexit\n')
 proc=subprocess.run([j,'-SelectEmuBySN',sn,'-Device','Cortex-M4','-If','SWD','-Speed','1000','-AutoConnect','0','-ExitOnError','1','-CommandFile',str(script)],capture_output=True,text=True,timeout=60)
 (out/f'{label}-backup.log').write_text(proc.stdout+proc.stderr)
 assert proc.returncode==0 and flash.stat().st_size==size and uicr.stat().st_size==4096,proc.stdout
 records.append(dict(board=label,serial=sn,flash_bytes=size,flash_sha256=hashlib.sha256(flash.read_bytes()).hexdigest(),uicr_sha256=hashlib.sha256(uicr.read_bytes()).hexdigest()))
 print('Backed up '+label+' '+sn,flush=True)
(out/'backup-manifest.json').write_text(json.dumps(records,indent=2))
