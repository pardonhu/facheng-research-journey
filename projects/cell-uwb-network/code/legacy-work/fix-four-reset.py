from pathlib import Path
p=Path('work/four-body.c');s=p.read_text();a=s.index(' stats.state=201;');b=s.index(' if(dwt_probe',a);s=s[:a]+' NRF_SPI0->FREQUENCY=0x10000000;\n if(control.node!=4){output(RESET,0);deca_sleep(2);GPIO->PIN_CNF[RESET]=0;}deca_sleep(10);\n'+s[b:];p.write_text(s)
