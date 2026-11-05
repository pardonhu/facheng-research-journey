from four_io import *
b=boards[3];vals=[12345,3000,0,4,1,636,1000,5,7,0,0]
cmd=['h']+[f'w4 {b["symbols"]["control"]+4*(i+1):#x} {v:#x}' for i,v in enumerate(vals)]+[f'w4 {b["symbols"]["control"]:#x} 1','mem32 0x200072bc 12','g','sleep 20','h','regs','mem32 0x20007220 8','mem32 0x200072bc 12','mem32 0x40000400 1','g']
print(command(b,'\n'.join(cmd)))
