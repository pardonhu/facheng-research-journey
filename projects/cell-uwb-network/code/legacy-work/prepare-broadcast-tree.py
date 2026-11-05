from pathlib import Path
s=Path('work/tree-body.c').read_text()
def sub(a,b):
 global s
 assert a in s,a[:80]
 s=s.replace(a,b)
sub('quiet_rounds,preamble;', 'quiet_rounds,preamble,drop_every;')
sub('static uint32_t relay_values[3];', '''static uint32_t relay_values[3];
/* ns histograms: 100ns bins centered at -20000..20000; tails counted separately.
 * On relay: row 0 inter-arrival spacing error, row 1 C, row 2 D relative to GROUP TX.
 * On leaf: row 0 actual hardware TX marker minus requested marker.
 */
typedef struct {int32_t min_ns,max_ns;int64_t sum_ns;uint32_t count,under,over,hist[401];} sync_stat;
volatile sync_stat timing[3];
volatile uint32_t rearm_us[4],antenna_delay[2]; /* count,sum,max,min; raw register values */
volatile uint32_t group_counts[6]; /* grants, expected, first received, first missing, injected drops, pairs */
static uint64_t grant_stamp;
static int64_t diff40(uint64_t a,uint64_t b){uint64_t d=(a-b)&0xffffffffffULL;return (d&(1ULL<<39))?(int64_t)d-(1LL<<40):(int64_t)d;}
static uint64_t tx_stamp(void){uint8_t t[5];uint64_t v=0;dwt_readtxtimestamp(t);for(unsigned i=0;i<5;i++)v|=(uint64_t)t[i]<<(8*i);return v;}
static void timing_add(unsigned k,int64_t dtu){
 int32_t ns=(int32_t)(dtu*10000/638976);volatile sync_stat *p=&timing[k];
 if(!p->count||ns<p->min_ns)p->min_ns=ns;
 if(!p->count||ns>p->max_ns)p->max_ns=ns;
 p->count++;p->sum_ns+=ns;
 int32_t bin=(ns+20050)/100;
 if(ns< -20050)p->under++;else if(bin>400)p->over++;else p->hist[bin]++;
}
''')
sub(' return 1;\n}\n/* Receiver', ''' if(txbuf[11]==GROUP)grant_stamp=tx_stamp();
 if(delayed && txbuf[11]==DATA)timing_add(0,diff40(tx_stamp(),delayed));
 return 1;
}
/* Receiver''')
sub('static void relay_collect(uint32_t round,uint32_t wanted) {', '''static void relay_group(uint32_t round,uint32_t wanted) {
 uint32_t begin=ticks();prepare(GROUP,0xffff,round,wanted,control.slot_us);stats.requests++;
 group_counts[0]++;group_counts[1]+=pop(wanted);
 for(unsigned b=1;b<3;b++)if(wanted&(1u<<b))relay_attempts[b]=1;
 uint32_t seen=0;uint64_t stamps[3]={0};
 if(transmit(0)) {
  listen();uint32_t start=ticks(),limit=control.turn_us+(pop(wanted)-1)*control.slot_us+1500;
  while(ticks()-start<limit&&control.command!=3){
   uint32_t proc_start=ticks();int r=receive();if(r==1){
    unsigned src=source();uint32_t m=get(rxbuf,20);
    if(rxbuf[11]==DATA&&src>=3&&src<=4&&get(rxbuf,16)==round&&m==(1u<<(src-2))&&(m&wanted)&&valid_payload(round,m)){
     unsigned b=src-2;
     if(!(seen&m)){
      seen|=m;relay_values[b]=get(rxbuf,28);stamps[b]=rxstamp;
      unsigned rank=pop(wanted&(m-1));uint64_t expected=grant_stamp+(uint64_t)(control.turn_us+rank*control.slot_us)*638976/10;
      timing_add(b,diff40(rxstamp,expected));
     }
    }else stats.invalid++;
    if(seen==wanted)break;
    listen();uint32_t cost=ticks()-proc_start;
    if(!rearm_us[0]||cost<rearm_us[3])rearm_us[3]=cost;
    rearm_us[0]++;rearm_us[1]+=cost;if(cost>rearm_us[2])rearm_us[2]=cost;
   }else if(r<0)listen();
  }
 }
 off();relay_mask|=seen;group_counts[2]+=pop(seen);group_counts[3]+=pop(wanted&~seen);
 if((seen&6)==6){timing_add(0,diff40(stamps[2],stamps[1])-(int64_t)control.slot_us*638976/10);group_counts[5]++;}
 phase.collection_us+=ticks()-begin;
}
static void relay_collect(uint32_t round,uint32_t wanted) {''')
sub('if(relay_round!=round){relay_round=round;relay_mask=0;memset(relay_attempts,0,sizeof(relay_attempts));}', 'int fresh=relay_round!=round;\n if(fresh){relay_round=round;relay_mask=0;memset(relay_attempts,0,sizeof(relay_attempts));}\n if(control.mode==4&&fresh)relay_group(round,wanted);')
sub('if(control.mode==3&&(relay_mask&wanted))','if(control.mode>=3&&(relay_mask&wanted))')
sub('  unsigned rank=pop(mask&(own-1));', '''  if(type==GROUP&&control.drop_every&&round%control.drop_every==0){group_counts[4]++;listen();return;}
  unsigned rank=pop(mask&(own-1));''')
sub('memset((void*)&phase,0,sizeof(phase));','memset((void*)timing,0,sizeof(timing));memset((void*)group_counts,0,sizeof(group_counts));\n   memset((void*)&phase,0,sizeof(phase));')
sub('control.mode>3','control.mode>4')
sub('NRF_SPI0->FREQUENCY=0x80000000;return 0;', 'NRF_SPI0->FREQUENCY=0x80000000;antenna_delay[0]=dwt_gettxantennadelay();antenna_delay[1]=dwt_getrxantennadelay();return 0;')
sub('memset((void*)timing,0,sizeof(timing));','memset((void*)rearm_us,0,sizeof(rearm_us));memset((void*)timing,0,sizeof(timing));')
Path('work/broadcast-tree-body.c').write_text(s)
base=Path('work/toolnail-UWB/DW3_QM33_SDK_1.1.1/Drivers/API/Build_Platforms')
for chip in ('52832','52840'):
 old=base/f'nRF{chip}-Tree';dst=base/f'nRF{chip}-BroadcastTree';dst.mkdir(exist_ok=True)
 full=(old/'main.c').read_text();prefix=full[:full.index('#include "dw3000_deca_regs.h"')]
 init=full[full.index(' NRF_TIMER1->MODE='):full.index(' SEGGER_RTT_WriteString(0,"Four-board')]
 (dst/'main.c').write_text(prefix+s.replace('/* PLATFORM_INIT */',init))
 (dst/'build.py').write_text((old/'build.py').read_text().replace('uwb-tree','uwb-broadcast-tree'))
print('Prepared independent instrumented baseline and broadcast tree firmware')
