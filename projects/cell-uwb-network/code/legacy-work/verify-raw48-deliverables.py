from pathlib import Path
import json,re,zipfile
root=Path.cwd();out=Path((root/'work/raw48-latest.txt').read_text())
md=(out/'48bit精简帧测试报告.md').read_text(encoding='utf-8')
for target in re.findall(r'\]\(([^)]+)\)',md):
 if not target.startswith('https://'):assert (out/target).is_file(),target
rows=[json.loads(l) for l in (out/'results.jsonl').read_text().splitlines()]
formal=[r for r in rows if r['formal']]
assert len(formal)==7 and all(r['count']==r['root']['unique']==10000 for r in formal)
assert next(r for r in formal if r['name'].endswith('drop10pct'))['responder']['injected_drops']==1000
with zipfile.ZipFile(out/'before-source.zip','w',zipfile.ZIP_DEFLATED) as z:
 for name in ['broadcast-tree-body.c','broadcast_tree_io.py','run-broadcast-tree.py']:
  z.write(root/'work'/name,name)
 old=root/'work/toolnail-UWB/DW3_QM33_SDK_1.1.1/Drivers/API/Build_Platforms/nRF52832-BroadcastTree'
 for name in ['main.c','build.py','build/uwb-broadcast-tree.hex']:
  z.write(old/name,'platform/'+name)
with zipfile.ZipFile(root/'outputs/48bit精简帧实验结果.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in out.iterdir():
  if p.is_file():z.write(p,p.name)
with zipfile.ZipFile(root/'outputs/48bit精简帧实验结果.zip') as z:assert z.testzip() is None
print('Verified 7 formal groups, 70000 records, report links, source backups and archive.')
print(out)
