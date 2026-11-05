from pathlib import Path
p=Path('work/four-body.c');s=p.read_text();s=s.replace(' NRF_SPI0->FREQUENCY=0x10000000;output(RESET,0);deca_sleep(2);GPIO->PIN_CNF[RESET]=0;deca_sleep(10);',' stats.state=201;deca_sleep(2000);\n NRF_SPI0->FREQUENCY=0x10000000;output(RESET,0);stats.state=202;deca_sleep(2000);GPIO->PIN_CNF[RESET]=0;stats.state=203;deca_sleep(2000);');p.write_text(s)
