from pathlib import Path
p=Path('work/four-body.c');s=p.read_text().replace('if(control.node!=4){','if(NRF_FICR->DEVICEID[0]!=0x06E5F278u){').replace('if(control.node==4){dwt_softreset','if(NRF_FICR->DEVICEID[0]==0x06E5F278u){dwt_softreset');s=s.replace('deca_usleep(200);transmit(0);}','deca_usleep(200);transmit(0);deca_usleep(500);}')
s=s.replace('prepare(DONE,1,round,relay_mask,0);deca_usleep(500);','prepare(DONE,1,round,relay_mask,0);deca_usleep(1000);')
p.write_text(s)
