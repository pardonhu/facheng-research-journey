from pathlib import Path
import json,zipfile,hashlib
root=Path.cwd();out=root/'outputs';study=out/'broadcast-tree-study'
assert json.loads((study/'status.json').read_text())['state']=='complete'
assert (study/'verification.json').exists()
with zipfile.ZipFile(out/'广播定时回复实验代码与数据.zip','w',zipfile.ZIP_DEFLATED) as z:
 z.write(out/'广播定时回复与轮询全过程对照.md','广播定时回复与轮询全过程对照.md')
 for p in study.rglob('*'):
  if p.is_file():z.write(p,p.relative_to(out))
 for name in ('prepare-broadcast-tree.py','broadcast-tree-body.c','broadcast_tree_io.py','run-broadcast-tree.py','backup-broadcast-tree.py','verify-broadcast-tree.py','analyze-broadcast-tree.py','report-broadcast-tree.py'):
  z.write(root/'work'/name,'code/'+name)
 for chip in ('52832','52840'):
  p=root/f'work/toolnail-UWB/DW3_QM33_SDK_1.1.1/Drivers/API/Build_Platforms/nRF{chip}-BroadcastTree'
  for name in ('main.c','build.py','memory.ld','build/uwb-broadcast-tree.hex','build/uwb-broadcast-tree.elf'):
   z.write(p/name,f'code/nRF{chip}-BroadcastTree/{name}')
with zipfile.ZipFile(out/'广播定时回复实验代码与数据.zip') as z:assert z.testzip() is None
print('Created verified report, firmware, backup and data archive')
