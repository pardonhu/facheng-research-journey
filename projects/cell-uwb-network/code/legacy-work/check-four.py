from four_io import *
for b in boards[2:]:
 print(b['label'],command(b,'h\nmem32 0x10000060 2\nmem32 0x10000100 5\nmem32 0x200072bc 12\nregs\ng'))
