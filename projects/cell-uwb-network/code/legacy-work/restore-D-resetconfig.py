from four_io import *
b=boards[3]
before=(out/'D-before-fourboard-uicr.bin').read_bytes();after=(out/'D-after-fourboard-uicr.bin').read_bytes();diff=[]
for i in range(0,4096,4):
 if before[i:i+4]!=after[i:i+4]:diff.append(dict(address=hex(0x10001000+i),original=hex(int.from_bytes(before[i:i+4],'little')),tested=hex(int.from_bytes(after[i:i+4],'little'))))
assert diff==[dict(address='0x10001200',original='0x12',tested='0xffffffff'),dict(address='0x10001204',original='0x12',tested='0xffffffff')]
(out/'D-tested-uicr.bin').write_bytes(after)
(out/'D-uicr-restoration.json').write_text(json.dumps(dict(changes=diff,reason='Restore original PSELRESET configuration after post-test comparison; no erase required.'),indent=2))
print(command(b,'h\nw4 0x4001E504 1\nsleep 10\nw4 0x10001200 0x12\nsleep 10\nw4 0x10001204 0x12\nsleep 10\nw4 0x4001E504 0\nmem32 0x10001200 2\nr\ng'))
