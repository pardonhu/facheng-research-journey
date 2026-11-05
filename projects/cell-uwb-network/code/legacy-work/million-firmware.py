from pathlib import Path
p=Path('work/toolnail-UWB/DW3_QM33_SDK_1.1.1/Drivers/API/Build_Platforms/nRF52832-Broadcast/main.c')
s=p.read_text().replace('static uint8_t seen[37500];','static uint8_t seen[8192];\nstatic uint32_t high_seq; static int have_seq;')
s=s.replace('memset(seen,0,sizeof(seen));','memset(seen,0,sizeof(seen)); high_seq=0; have_seq=0;').replace('target>300000','target>1000000')
a='if(good) { if(seen[seq/8]&(1u<<(seq%8))) stats.duplicate++; else { seen[seq/8]|=1u<<(seq%8); stats.rx++; } stats.last=seq; } else stats.bad++;'
b='''if(good) {
 if(!have_seq) { high_seq=seq; have_seq=1; }
 else if(seq>high_seq) { uint32_t jump=seq-high_seq; if(jump>=65536) memset(seen,0,sizeof(seen)); else for(uint32_t v=high_seq+1;v<=seq;v++) seen[(v%65536)/8]&=(uint8_t)~(1u<<(v%8)); high_seq=seq; }
 if(high_seq-seq>=65536) { stats.bad++; } else { uint32_t ix=seq%65536; if(seen[ix/8]&(1u<<(ix%8))) stats.duplicate++; else { seen[ix/8]|=1u<<(ix%8); stats.rx++; } }
 stats.last=seq;
 } else stats.bad++;'''
assert a in s;s=s.replace(a,b);p.write_text(s)
