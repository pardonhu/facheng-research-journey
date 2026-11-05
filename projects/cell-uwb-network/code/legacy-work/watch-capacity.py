from pathlib import Path
import json,time,subprocess,zipfile,hashlib,sys
root=Path.cwd();out=root/'outputs/capacity-study';last=-1
while True:
 rows=(out/'results.jsonl').read_text().splitlines() if (out/'results.jsonl').exists() else []
 state=json.loads((out/'status.json').read_text()) if (out/'status.json').exists() else {}
 if len(rows)!=last or state.get('state')=='complete':
  subprocess.run([sys.executable,'-X','utf8',str(root/'work/report-capacity.py')],check=True)
  last=len(rows)
  print(json.dumps(dict(saved_runs=last,state=state.get('state','running'))),flush=True)
 if (out/'error.txt').exists():
  print('RUNNER ERROR: '+(out/'error.txt').read_text(),flush=True);break
 if state.get('state')=='complete':
  p=root/'work/toolnail-UWB/DW3_QM33_SDK_1.1.1/Drivers/API/Build_Platforms/nRF52832-Capacity'
  files=list(out.glob('*.json'))+list(out.glob('*.jsonl'))+list(out.glob('*.txt'))+list(out.glob('*.png'))+list(out.glob('*received.bin'))
  with zipfile.ZipFile(root/'outputs/UWB帧间隔与重传实验.zip','w',zipfile.ZIP_DEFLATED) as z:
   for f in files:z.write(f,'results/'+f.name)
   for name in ['main.c','build.py','memory.ld']:z.write(p/name,'nRF52832-Capacity/'+name)
   z.write(p/'build/uwb-capacity.hex','uwb-capacity.hex')
   for name in ['run-capacity.py','report-capacity.py']:z.write(root/'work'/name,name)
  print('COMPLETE: outputs/UWB帧间隔与重传实验.zip',flush=True);break
 time.sleep(15)
