from pathlib import Path
import json,re,zipfile,hashlib
root=Path('outputs').resolve()
# Refresh reports and their figure dependencies inside the two experimental archives.
for archive_name,report_name,figure_dirs in [
 ('四板全过程实验数据与代码.zip','四板电芯到中继再到中心全过程实验.md',['报告配图']),
 ('广播定时回复实验代码与数据.zip','广播定时回复与轮询全过程对照.md',['broadcast-tree-study'])]:
 archive=root/archive_name;updates={report_name:root/report_name}
 for directory in figure_dirs:
  for p in (root/directory).iterdir():
   if p.suffix.lower() in ('.png','.svg','.py'):updates[p.relative_to(root).as_posix()]=p
 temp=archive.with_suffix('.updated.zip')
 with zipfile.ZipFile(archive) as src,zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED) as dst:
  for info in src.infolist():
   if info.filename not in updates:dst.writestr(info,src.read(info.filename))
  for name,p in updates.items():dst.write(p,name)
 with zipfile.ZipFile(temp) as z:assert z.testzip() is None
 temp.replace(archive)
files=set();pending=[root/'电芯UWB组网两日实验总报告.md']
while pending:
 p=pending.pop()
 if p in files:continue
 assert p.is_file(),p;files.add(p)
 if p.suffix=='.md':
  s=p.read_text(encoding='utf-8')
  assert not any(x in s for x in ('电芯值','点名','实验日期：','64符号配置')),(p,'terminology')
  for link in re.findall(r'\]\(([^)]+)\)',s):
   if link.startswith(('https://','http://','#')):continue
   q=(p.parent/link.split('#')[0]).resolve();assert q.is_relative_to(root);pending.append(q)
files.update(p for p in (root/'报告配图').iterdir() if p.is_file())
files.update(p for p in (root/'broadcast-tree-study').iterdir() if p.suffix in ('.png','.svg','.py'))
files.update([root/'ble-matched-study/hardware-summary.json',root/'tree-end-to-end-study/summary.json'])
archive=root/'电芯UWB组网两日实验总报告与配图.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(files):z.write(p,p.relative_to(root))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
# Check central reported measurements against stored formal summaries.
s=(root/'电芯UWB组网两日实验总报告.md').read_text(encoding='utf-8')
for r in json.loads((root/'broadcast-tree-study/summary.json').read_text()):assert f"{r['mean_ms']:.3f}" in s
assert '前导码长度64个符号' in s and 'Ultra-Wideband' in s
manifest={'main_report':str(root/'电芯UWB组网两日实验总报告.md'),'figures':len(re.findall(r'!\[',s)),'packed_files':len(files),'links_valid':True,'archives_valid':True,'core_measurements_checked':True,'main_sha256':hashlib.sha256(s.encode()).hexdigest()}
Path('work/报告重写核对.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(manifest,ensure_ascii=False))
