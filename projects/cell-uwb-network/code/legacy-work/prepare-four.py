from pathlib import Path
import re
p=Path('work/toolnail-UWB/DW3_QM33_SDK_1.1.1/Drivers/API/Build_Platforms')
s=(p/'nRF52832-Preamble/main.c').read_text();prefix=s[:s.index('#include "dw3000_deca_regs.h"')]
prefix=prefix.replace('#define CS 22','#define GPIO NRF_P0\n#define PINBASE 0\n#define SCK 25\n#define MOSI 23\n#define MISO 24\n#define CS 22').replace('NRF_P0->','GPIO->')
init=s[s.index(' NRF_TIMER1->MODE='):s.index(' SEGGER_RTT_WriteString(0,"Reliable')]
init=init.replace('NRF_P0->','GPIO->').replace('output(25,0); output(23,0); GPIO->PIN_CNF[24]=0;','output(SCK,0); output(MOSI,0); GPIO->PIN_CNF[MISO]=0;').replace('PSELSCK=25','PSELSCK=PINBASE+SCK').replace('PSELMOSI=23','PSELMOSI=PINBASE+MOSI').replace('PSELMISO=24','PSELMISO=PINBASE+MISO')
body=Path('work/four-body.c').read_text().replace('/* PLATFORM_INIT */',init)
for chip in ('52832','52840'):
 dst=p/f'nRF{chip}-Four';dst.mkdir(exist_ok=True)
 pre=prefix
 if chip=='52840':
  pre=pre.replace('GPIO NRF_P0','GPIO NRF_P1').replace('PINBASE 0','PINBASE 32').replace('SCK 25','SCK 15').replace('MOSI 23','MOSI 13').replace('MISO 24','MISO 14').replace('CS 22','CS 12').replace('RESET 18','RESET 8').replace('WAKE 20','WAKE 11').replace('IRQ 19','IRQ 10')
 code=pre+body
 for pin in ('SCK','MOSI','MISO'):code=re.sub(r'\b'+pin+r'\b','PIN_'+pin,code)
 (dst/'main.c').write_text(code)
 build=(p/'nRF52832-Preamble/build.py').read_text().replace('uwb-preamble','uwb-four')
 if chip=='52840':build=build.replace('NRF52832_XXAA','NRF52840_XXAA').replace("'-DBOARD_PCA10040'","'-DBOARD_PCA10056','-DCONFIG_NRF_APPROTECT_DISABLE'").replace('gcc_startup_nrf52.S','gcc_startup_nrf52840.S').replace('system_nrf52.c','system_nrf52840.c').replace('LENGTH = 512K','LENGTH = 1024K').replace('LENGTH = 64K','LENGTH = 256K')
 (dst/'build.py').write_text(build)
