from pathlib import Path
p=Path('work/toolnail-UWB/DW3_QM33_SDK_1.1.1/Drivers/API/Build_Platforms/nRF52832-P2P/main.c')
s=p.read_text().replace('0x10000000; }','0x80000000; }').replace('interval<2000','interval>1000000').replace('next+=interval; if((int32_t)(ticks()-next)>0) next=ticks()+interval;','next=ticks()+interval;')
s=s.replace('if(ticks()-report>1000000)','if(stats.state!=1 && stats.state!=2 && ticks()-report>1000000)')
p.write_text(s)
