from four_io import *
import zipfile,hashlib
folder=root/'outputs/ble-matched-study';folder.mkdir(exist_ok=True)
for b in boards[:2]:
 f=folder/f"{b['label']}-before-flash.bin";u=folder/f"{b['label']}-before-uicr.bin"
 assert not f.exists()
 command(b,f"savebin {f.as_posix()} 0 0x80000\nsavebin {u.as_posix()} 0x10001000 0x1000")
with zipfile.ZipFile(folder/'before-source.zip','w',zipfile.ZIP_DEFLATED) as z:
 for n in ('four-body.c','four_io.py','prepare-four.py','run-four.py'):z.write(root/'work'/n,n)
print('A/B backups complete; C/D unchanged')
