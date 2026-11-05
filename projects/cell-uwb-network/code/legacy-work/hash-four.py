from pathlib import Path
p=Path('work/four_io.py');s=p.read_text().replace('import subprocess,time,struct,json,math','import subprocess,time,struct,json,math,hashlib');s=s.replace("row=dict(name=name,mode=mode", "row=dict(firmware_sha256={b['label']:hashlib.sha256((b['build']/'uwb-four.hex').read_bytes()).hexdigest() for b in boards},name=name,mode=mode");p.write_text(s)
