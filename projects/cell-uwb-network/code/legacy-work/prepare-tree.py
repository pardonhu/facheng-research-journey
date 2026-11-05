from pathlib import Path
base=Path('work/toolnail-UWB/DW3_QM33_SDK_1.1.1/Drivers/API/Build_Platforms')
s=Path('work/four-body.c').read_text()
def sub(a,b):
 global s
 assert a in s,a[:100]
 s=s.replace(a,b)
sub('quiet_from,quiet_rounds;','quiet_from,quiet_rounds,preamble;')
sub('static uint32_t relay_round=', '''uint32_t window200_us[250],window300_us[167],window200_missing[250],window300_missing[167];
volatile struct {uint32_t collection_us,uplink_us,leaf_poll_calls,uplink_calls,windows200,windows300;} phase;
static uint32_t relay_values[3];
static uint32_t relay_round=''')
sub('if(dwt_initialise(DWT_READ_OTP_ALL)||dwt_configure(&config))return -4;', 'config.txPreambLength=control.preamble;config.sfdTO=control.preamble+1;\n if(dwt_initialise(DWT_READ_OTP_ALL)||dwt_configure(&config))return -4;')
sub('put(txbuf,28+4*k++,value(b+2,round));','put(txbuf,28+4*k++,(type==FORWARD||type==AGGREGATE)?relay_values[b]:value(b+2,round));')
sub('valid_payload(round,bit)) {off();return bit;}', 'valid_payload(round,bit)) {if(control.node==2)relay_values[node-2]=get(rxbuf,28);off();return bit;}')
sub('static void relay_collect(uint32_t round,uint32_t wanted) {', '''static void relay_send(unsigned type,uint32_t round,uint32_t mask) {
 uint32_t start=ticks();prepare(type,1,round,mask,0);deca_usleep(200);
 if(transmit(0))stats.relay_forwards++;
 phase.uplink_us+=ticks()-start;phase.uplink_calls++;
}
static void relay_collect(uint32_t round,uint32_t wanted) {''')
sub('  while(!(relay_mask&(1u<<b))', '  uint32_t collect_start=ticks();unsigned previous_attempts=relay_attempts[b];\n  while(!(relay_mask&(1u<<b))')
sub('  if(control.mode==2&&(relay_mask&(1u<<b))) {prepare(FORWARD,1,round,1u<<b,0);deca_usleep(200);if(transmit(0))stats.relay_forwards++;}', '  phase.collection_us+=ticks()-collect_start;phase.leaf_poll_calls+=relay_attempts[b]-previous_attempts;\n  if(control.mode==2&&(relay_mask&(1u<<b)))relay_send(FORWARD,round,1u<<b);')
sub('if(control.mode==3&&(relay_mask&wanted)) {prepare(AGGREGATE,1,round,relay_mask&wanted,0);deca_usleep(200);if(transmit(0))stats.relay_forwards++;}', 'if(control.mode==3&&(relay_mask&wanted))relay_send(AGGREGATE,round,relay_mask&wanted);')
sub(' for(uint32_t round=0;round<nrounds', ' uint32_t w200_start=start,w300_start=start,w200_lost=0,w300_lost=0;\n for(uint32_t round=0;round<nrounds')
sub('  stats.elapsed=ticks()-start;', '''  uint32_t end=ticks();w200_lost+=pop(expected&~seen);w300_lost+=pop(expected&~seen);
  if((round+1)%100==0&&phase.windows200<250){unsigned k=phase.windows200++;window200_us[k]=end-w200_start;window200_missing[k]=w200_lost;w200_start=end;w200_lost=0;}
  if((round+1)%150==0&&phase.windows300<167){unsigned k=phase.windows300++;window300_us[k]=end-w300_start;window300_missing[k]=w300_lost;w300_start=end;w300_lost=0;}
  stats.elapsed=end-start;''')
sub('   stats.run=control.run;', '''   memset((void*)&phase,0,sizeof(phase));memset(relay_values,0,sizeof(relay_values));
   memset(window200_us,0,sizeof(window200_us));memset(window300_us,0,sizeof(window300_us));memset(window200_missing,0,sizeof(window200_missing));memset(window300_missing,0,sizeof(window300_missing));
   stats.run=control.run;''')
sub('control.slot_us>5000)', 'control.slot_us>5000||(control.preamble!=64&&control.preamble!=32))')
Path('work/tree-body.c').write_text(s)
for chip in ('52832','52840'):
 old=base/f'nRF{chip}-Four';dst=base/f'nRF{chip}-Tree';dst.mkdir(exist_ok=True)
 full=(old/'main.c').read_text();prefix=full[:full.index('#include "dw3000_deca_regs.h"')]
 init=full[full.index(' NRF_TIMER1->MODE='):full.index(' SEGGER_RTT_WriteString(0,"Four-board')]
 (dst/'main.c').write_text(prefix+s.replace('/* PLATFORM_INIT */',init))
 (dst/'build.py').write_text((old/'build.py').read_text().replace('uwb-four','uwb-tree'))
print('Created independent Tree projects with received-payload forwarding and 200/300-record windows')
