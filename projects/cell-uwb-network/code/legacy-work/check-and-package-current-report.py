from pathlib import Path
import json,re,zipfile,shutil,hashlib
root=Path(__file__).resolve().parent.parent
out=root/'outputs'
names=['电芯UWB组网研究报告.md','电芯UWB组网两日实验总报告.md','广播定时回复与轮询全过程对照.md','四板电芯到中继再到中心全过程实验.md']
files=set(out/n for n in names)
checked=[]
for name in names:
 p=out/name;s=p.read_text(encoding='utf-8')
 for banned in ('附录B','早期程序','参数和计时范围保持明确','最小可用值','电芯值','Ultra-Wideband','millisecond'):
  assert banned not in s,(name,banned)
 images=re.findall(r'!\[[^\]]*\]\(([^)]+)\)',s)
 captions=re.findall(r'^图(\d+)\.',s,re.M)
 assert len(images)==len(captions),(name,len(images),captions)
 assert list(map(int,captions))==list(range(1,len(captions)+1)),(name,captions)
 for target in re.findall(r'\]\(([^)]+)\)',s):
  if target.startswith(('https://','http://','#')):continue
  q=p.parent/target.split('#')[0]
  assert q.is_file(),(name,target)
  files.add(q)
 checked.append({'name':name,'images':len(images),'local_links_valid':True})

main=(out/names[0]).read_text(encoding='utf-8')
assert (out/names[0]).read_bytes()==(out/names[1]).read_bytes()
for part in re.split(r'^### A\.\d+ ',main,flags=re.M)[1:]:
 for label in ('**目的：','**设置：','**指标：','**结果与结论：'):
  assert label in part,label
for i,r in enumerate(json.loads((out/'broadcast-tree-study/summary.json').read_text())):
 assert f"{r['mean_ms']:.3f}" in main
 assert abs(r['mean_ms']-r['collection_ms']-r['uplink_ms']-r['other_ms'])<1e-8
 assert r['received']==r['target']==50000
assert '电芯数据量与前导码长度优化实验' not in main
assert '152 bit实验管理字段由本实验程序自行添加' in main
assert '100 ms容量 = k' in main
assert '帧间隔500.165、350.165 μs' in main
assert '附录A' not in main
assert '星型拓扑广播' in main and '树型拓扑两跳中继' in main
assert (root/'AGENTS.md').read_bytes()==(out/'报告写作要求-AGENTS.md').read_bytes()
files.add(out/'报告写作要求-AGENTS.md')
files.update((out/'当前组网报告配图').glob('*'))
for sub in ['broadcast-tree-study','tree-end-to-end-study','four-board-study','ble-matched-study','preamble-study','reliable-runs']:
 for n in ['results.jsonl','summary.json','verification.json','formal-summary.json','hardware-summary.json','experiment-manifest.json']:
  p=out/sub/n
  if p.is_file():files.add(p)

bundle=out/'电芯UWB组网研究报告与配图.zip'
with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(files):
  if p.is_file():z.write(p,p.relative_to(out).as_posix())
with zipfile.ZipFile(bundle) as z:
 assert z.testzip() is None
 assert z.read(names[0])==(out/names[0]).read_bytes()
shutil.copy2(bundle,out/'电芯UWB组网两日实验总报告与配图.zip')

# Refresh report entries in existing experiment packages while preserving evidence.
for archive,report in [('广播定时回复实验代码与数据.zip',names[2]),('四板全过程实验数据与代码.zip',names[3])]:
 src=out/archive;temp=root/'work'/('refreshed-'+archive)
 replacements={report:out/report}
 for target in re.findall(r'\]\(([^)]+)\)',(out/report).read_text(encoding='utf-8')):
  if not target.startswith(('http://','https://','#')) and (out/target).is_file():replacements[target]=out/target
 with zipfile.ZipFile(src) as old,zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED) as new:
  preserved={}
  for info in old.infolist():
   if info.filename in replacements:continue
   content=old.read(info.filename);new.writestr(info,content)
   preserved[info.filename]=hashlib.sha256(content).hexdigest()
  for entry,p in replacements.items():new.write(p,entry)
 with zipfile.ZipFile(temp) as z:
  assert z.testzip() is None
  for entry,digest in preserved.items():assert hashlib.sha256(z.read(entry)).hexdigest()==digest
 shutil.copy2(temp,src)
(root/'work/report-revision-validation.json').write_text(json.dumps({'reports':checked,'archive_valid':True,'evidence_preserved':True},ensure_ascii=False,indent=2),encoding='utf-8')
print('Validated 4 reports, captions, local links, current metrics and archives; original evidence preserved.')
print('Bundle size:',bundle.stat().st_size)
