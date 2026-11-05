from pathlib import Path
import argparse,json,time,subprocess,sys,zipfile,hashlib,traceback
from preamble_io import *
def report():subprocess.run([sys.executable,'-X','utf8',str(root/'work/report-preamble.py')],check=True)
def package():
 project=p.parent
 with zipfile.ZipFile(root/'outputs/UWB前导码与4字节优化实验.zip','w',zipfile.ZIP_DEFLATED) as z:
  for f in out.glob('*'):
   if f.is_file():z.write(f,'results/'+f.name)
  for name in ['main.c','build.py','memory.ld']:z.write(project/name,'nRF52832-Preamble/'+name)
  z.write(p/'uwb-preamble.hex','uwb-preamble.hex')
  for name in ['run-preamble.py','report-preamble.py','preamble_io.py']:z.write(root/'work'/name,name)
  header=project.parents[1]/'Src/examples/ex_08_reliable_p2p/reliable_p2p_protocol.h'
  z.write(header,'original-colleague/reliable_p2p_protocol.h')
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--flash',action='store_true');parser.add_argument('--smoke',action='store_true');args=parser.parse_args()
 try:
  if args.flash:
   for sn in boards:(out/f'flash-{sn}.log').write_text(command(sn,f'h\nloadfile {(p/"uwb-preamble.hex").as_posix()}\nr\ng'))
   (out/'firmware.json').write_text(json.dumps(dict(sha256=hashlib.sha256((p/'uwb-preamble.hex').read_bytes()).hexdigest(),backup=json.loads((root/'outputs/latest-backup.json').read_text())),indent=2))
  done={r['name'] for r in existing()}
  for payload in (32,4):
   for preamble in (128,64,32):
    profile.update(payload=payload,preamble=preamble)
    if args.smoke:
     for mode in (0,1):
      name=f'smoke-p{preamble}-l{payload}-m{mode}'
      if name not in done:run_case(name,1003,0,mode,mode,300,0)
    else:
     for mode in (0,1):
      for direction in (0,1):
       name=f'p{preamble}-l{payload}-m{mode}-d{direction}'
       if name not in done:
        run_case(name,100000,0,direction,mode,300,1 if payload==32 else 2)
        report()
  report();package()
  (out/'status.json').write_text(json.dumps(dict(state='smoke_complete' if args.smoke else 'complete',completed=time.time(),runs=len(existing()))))
 except BaseException as e:
  (out/'error.txt').write_text(traceback.format_exc());raise
 finally:
  for sn in boards:
   try:stop(sn)
   except Exception:pass
