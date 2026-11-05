/* Host writes command last. role: 1 receiver, 2 sender, 3 stop.
 * injection: 0 natural, 1 discard first attempt of every tenth DATA,
 * 2 discard every attempt of every tenth DATA. ack_drop: first ACK per N windows.
 * Uses colleague's RP v1 frame format and selective-repeat algorithm.
 */
volatile struct { uint32_t command,run,count,interval,channel,injection,ack_drop,rounds,command_role; } control;
volatile struct { uint32_t state,run,attempts,retransmissions,unique,duplicates,invalid,phy_errors,
 ack_requests,ack_timeouts,ack_missing,remote_unique,remote_failed,summary_received,
 completed,elapsed,first_unique,recovered,injected,ack_dropped,windows,window_max_us,tx_errors,control_retries; } stats;
#include "reliable_p2p_protocol.h"
static uint8_t received[12500], ack_seen[391], txbuf[59], rxbuf[59], mac_seq;
static uint32_t start_time;
static int active, finished;
/* PLATFORM_SETUP */
static uint32_t get(unsigned i) { return reliable_p2p_get_u32(rxbuf,i); }
static uint32_t mask_for(uint32_t base) { uint32_t n=control.count-base; return n>=32?0xffffffffu:((1u<<n)-1u); }
static unsigned pc(uint32_t v) { return reliable_p2p_popcount(v); }
static void clear_radio(void) { dwt_forcetrxoff(); dwt_writesysstatuslo(DWT_INT_TXFRS_BIT_MASK|DWT_INT_RXFCG_BIT_MASK|SYS_STATUS_ALL_RX_ERR|SYS_STATUS_ALL_RX_TO); }
static void prepare(uint8_t type,uint32_t field,uint32_t a0,uint32_t a1,uint32_t a2,uint32_t a3,uint32_t a4) {
 int receiver=control.command_role==1;
 reliable_p2p_prepare_frame(txbuf,mac_seq++,'X',receiver?'T':'R','X',receiver?'R':'T',type,control.run,field,a0,a1,a2,a3,a4);
}
static int transmit(void) {
 clear_radio(); dwt_writetxdata(57,txbuf,0); dwt_writetxfctrl(59,0,0);
 if(dwt_starttx(DWT_START_TX_IMMEDIATE)) { stats.tx_errors++; return 0; }
 uint32_t t=ticks();
 while(!(dwt_readsysstatuslo()&DWT_INT_TXFRS_BIT_MASK)) {
  if(ticks()-t>10000) { stats.tx_errors++; clear_radio(); return 0; }
 }
 dwt_writesysstatuslo(DWT_INT_TXFRS_BIT_MASK); return 1;
}
static void listen(void) { clear_radio(); dwt_setrxtimeout(0); dwt_rxenable(DWT_START_RX_IMMEDIATE); }
/* 0 pending, 1 validated frame, -1 bad frame/error; validates peer address too. */
static int receive(void) {
 uint32_t s=dwt_readsysstatuslo();
 if(s&DWT_INT_RXFCG_BIT_MASK) {
  unsigned n=dwt_getframelength(0); if(n==59) dwt_readrxdata(rxbuf,59,0);
  dwt_writesysstatuslo(DWT_INT_RXFCG_BIT_MASK);
  uint8_t source=control.command_role==1?'T':'R';
  if(n!=59 || !reliable_p2p_frame_is_valid(rxbuf,n) || rxbuf[0]!=0x41 || rxbuf[1]!=0x88 || rxbuf[7]!='X' || rxbuf[8]!=source || get(13)!=control.run) { stats.invalid++; return -1; }
  return 1;
 }
 if(s&(SYS_STATUS_ALL_RX_ERR|SYS_STATUS_ALL_RX_TO)) { stats.phy_errors++; return -1; }
 return 0;
}
static int request(uint8_t type,uint32_t field,uint32_t arg,uint8_t expected) {
 prepare(type,field,arg,0,0,0,0);
 if(!transmit()) return 0;
 listen(); uint32_t t=ticks();
 while(ticks()-t<10000 && control.command!=3) {
  int r=receive();
  if(r==1) {
   if(rxbuf[12]==expected && get(17)==field) { clear_radio(); return 1; }
   stats.invalid++; listen();
  } else if(r<0) listen();
 }
 stats.ack_timeouts++; clear_radio(); return 0;
}
static void reply(uint8_t type,uint32_t field,uint32_t a0,uint32_t a1,uint32_t a2,uint32_t a3,uint32_t a4) {
 prepare(type,field,a0,a1,a2,a3,a4); deca_usleep(300); transmit();
}
static void receiver_step(void) {
 int r=receive(); if(!r) return;
 if(r<0) { listen(); return; }
 uint32_t type=rxbuf[12], field=get(17), a0=get(21);
 if(type==RELIABLE_P2P_MSG_SESSION_START && field==control.count && a0==32) {
  if(!active) { active=1; start_time=ticks(); }
  reply(RELIABLE_P2P_MSG_SESSION_ACK,field,32,0,0,0,0);
 } else if(!active) stats.invalid++;
 else if(type==RELIABLE_P2P_MSG_DATA && !finished) {
  if(field>=control.count || !reliable_p2p_payload_is_valid(rxbuf,field)) stats.invalid++;
  else if(control.injection && field%10==0 && (control.injection==2 || a0==0)) stats.injected++;
  else {
   unsigned i=field/8, bit=1u<<(field%8);
   if(received[i]&bit) stats.duplicates++;
   else { received[i]|=bit; stats.unique++; if(a0==0) stats.first_unique++; else stats.recovered++; }
  }
 } else if(type==RELIABLE_P2P_MSG_BLOCK_ACK_REQ && field<control.count && field%32==0) {
  uint32_t bitmap=0, window=field/32;
  for(unsigned i=0;i<32 && field+i<control.count;i++) if(received[(field+i)/8]&(1u<<((field+i)%8))) bitmap|=1u<<i;
  stats.ack_requests++;
  if(control.ack_drop && window%control.ack_drop==0 && !(ack_seen[window/8]&(1u<<(window%8)))) {
   ack_seen[window/8]|=1u<<(window%8); stats.ack_dropped++;
  } else reply(RELIABLE_P2P_MSG_BLOCK_ACK,field,bitmap&a0,0,0,0,0);
 } else if(type==RELIABLE_P2P_MSG_SESSION_END && field==control.count) {
  if(!finished) { stats.elapsed=ticks()-start_time; finished=1; stats.completed=control.count; stats.state=4; }
  reply(RELIABLE_P2P_MSG_SUMMARY,field,stats.unique,control.count-stats.unique,stats.duplicates,stats.invalid,stats.phy_errors);
 } else stats.invalid++;
 listen();
}
static void sender_run(void) {
 start_time=ticks(); int ok=0;
 for(unsigned k=0;k<10 && control.command!=3;k++) {
  if(request(RELIABLE_P2P_MSG_SESSION_START,control.count,32,RELIABLE_P2P_MSG_SESSION_ACK) && get(21)==32) {ok=1;break;}
  stats.control_retries++; deca_usleep(1000);
 }
 if(!ok) { stats.state=91; return; }
 deca_usleep(300);
 for(uint32_t base=0;base<control.count && control.command!=3;base+=32) {
  uint32_t valid=mask_for(base), ack=0, wt=ticks();
  for(unsigned round=0;round<control.rounds && ack!=valid && control.command!=3;round++) {
   for(unsigned bit=0;bit<32 && control.command!=3;bit++) {
    if(!(valid&(1u<<bit)) || (ack&(1u<<bit))) continue;
    prepare(RELIABLE_P2P_MSG_DATA,base+bit,round,0,0,0,0); reliable_p2p_fill_payload(txbuf,base+bit);
    if(transmit()) { stats.attempts++; if(round) stats.retransmissions++; }
    deca_usleep(control.interval);
   }
   stats.ack_requests++;
   if(request(RELIABLE_P2P_MSG_BLOCK_ACK_REQ,base,valid,RELIABLE_P2P_MSG_BLOCK_ACK)) ack|=get(21)&valid;
   deca_usleep(300);
  }
  stats.ack_missing+=pc(valid&~ack); stats.completed+=pc(valid); stats.windows++;
  uint32_t elapsed=ticks()-wt; if(elapsed>stats.window_max_us) stats.window_max_us=elapsed;
  stats.elapsed=ticks()-start_time;
 }
 if(control.command==3) {stats.state=5;return;}
 for(unsigned k=0;k<10 && control.command!=3;k++) {
  if(request(RELIABLE_P2P_MSG_SESSION_END,control.count,stats.ack_missing,RELIABLE_P2P_MSG_SUMMARY)) {
   stats.remote_unique=get(21); stats.remote_failed=get(25);
   if(stats.remote_unique<=control.count && stats.remote_failed==control.count-stats.remote_unique) stats.summary_received=1;
   break;
  }
  stats.control_retries++; deca_usleep(1000);
 }
 stats.elapsed=ticks()-start_time; stats.state=stats.summary_received?3:92;
}
int main(void) {
/* PLATFORM_INIT */
 SEGGER_RTT_WriteString(0,"Reliable RP v1 ready\n");
 while(1) {
  if(control.command) {
   uint32_t cmd=control.command; control.command=0;
   if(cmd==3) {clear_radio(); stats.state=5;continue;}
   memset((void*)&stats,0,sizeof(stats)); memset(received,0,sizeof(received)); memset(ack_seen,0,sizeof(ack_seen));
   active=finished=0; stats.run=control.run; control.command_role=cmd;
   if((cmd!=1 && cmd!=2)||control.count==0||control.count>100000||control.interval>1000000||control.rounds<1||control.rounds>5||control.injection>2) {stats.state=90;continue;}
   int e=setup(); if(e) {stats.state=100-e;continue;}
   stats.state=cmd; if(cmd==1) listen(); else sender_run();
  }
  if(control.command_role==1 && (stats.state==1||stats.state==4)) receiver_step();
 }
}
