from pathlib import Path
p=Path('work/four-body.c');s=p.read_text().replace('stats.devid=dwt_readdevid();if(stats.devid!=0xDECA0302)return -2;','stats.devid=dwt_readdevid();if(stats.devid!=0xDECA0302)return -2;\n if(control.node==4){dwt_softreset(0);deca_sleep(10);}') ;p.write_text(s)
