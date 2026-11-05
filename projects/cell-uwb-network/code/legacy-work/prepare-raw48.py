from pathlib import Path
import shutil
root=Path.cwd();base=root/'work/toolnail-UWB/DW3_QM33_SDK_1.1.1/Drivers/API/Build_Platforms'
old=base/'nRF52832-BroadcastTree';dst=base/'nRF52832-Raw48';dst.mkdir(exist_ok=True)
full=(old/'main.c').read_text();prefix=full[:full.index('#include "dw3000_deca_regs.h"')]
init=full[full.index(' NRF_TIMER1->MODE='):full.index(' SEGGER_RTT_WriteString(0,"Four-board')]
body=(root/'work/raw48-body.c').read_text()
(dst/'main.c').write_text(prefix+body.replace('/* PLATFORM_INIT */',init))
(dst/'build.py').write_text((old/'build.py').read_text().replace('uwb-broadcast-tree','uwb-raw48'))
print(dst)
