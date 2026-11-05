from pathlib import Path
import zipfile,hashlib,json,datetime,subprocess
root=Path.cwd();repo=root/'work/toolnail-UWB';base=repo/'DW3_QM33_SDK_1.1.1/Drivers/API'
tag=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y%m%d-%H%M%S')
target=root/'outputs'/f'UWB优化前备份-{tag}.zip'
files=[]
for name in ['nRF52832-Capacity','nRF52832-Reliable','nRF52832-Broadcast','nRF52832-P2P','nRF52832-ID']:
 p=base/'Build_Platforms'/name
 if p.exists():files.extend(x for x in p.rglob('*') if x.is_file())
files+=list((base/'Src/examples/ex_08_reliable_p2p').glob('*.[ch]'))
files+=list((root/'work').glob('*.py'))+list((root/'work').glob('*.c'))
for folder in ['capacity-study','reliable-runs']:
 files.extend(x for x in (root/'outputs'/folder).rglob('*') if x.is_file())
manifest={'created_Asia_Shanghai':tag,'git_commit':subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip(),'files':{}}
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(set(files)):
  data=f.read_bytes();name=f.relative_to(root).as_posix();z.writestr(name,data)
  manifest['files'][name]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
 z.writestr('manifest.json',json.dumps(manifest,indent=2))
 z.writestr('RESTORE.txt','Restore the saved Build_Platforms directory and scripts to the original repository paths. The nRF52832-Capacity/build/uwb-capacity.hex image is the last capacity-study firmware loaded on both boards. No UICR changes are needed. Completed results are included; interrupted runs are not complete observations.\n')
with zipfile.ZipFile(target) as z:
 assert z.testzip() is None
 for name,entry in manifest['files'].items():assert hashlib.sha256(z.read(name)).hexdigest()==entry['sha256']
(root/'outputs/latest-backup.json').write_text(json.dumps(dict(path=str(target),file_count=len(manifest['files']),sha256=hashlib.sha256(target.read_bytes()).hexdigest()),indent=2))
print(json.dumps(dict(path=str(target),file_count=len(manifest['files']),verified=True),ensure_ascii=False))
