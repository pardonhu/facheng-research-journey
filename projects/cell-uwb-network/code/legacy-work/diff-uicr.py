from pathlib import Path
import struct
p=Path('outputs/four-board-study');a=(p/'D-before-fourboard-uicr.bin').read_bytes();b=(p/'D-after-fourboard-uicr.bin').read_bytes()
for i in range(0,len(a),4):
 if a[i:i+4]!=b[i:i+4]:print(hex(0x10001000+i),a[i:i+4].hex(),b[i:i+4].hex())
