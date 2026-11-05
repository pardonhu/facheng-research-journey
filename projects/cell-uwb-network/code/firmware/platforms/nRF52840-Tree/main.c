#include "nrf.h"
#include "deca_device_api.h"
#include "deca_interface.h"
#include "SEGGER_RTT.h"
#include <stdio.h>
#include <stdint.h>
#define GPIO NRF_P1
#define PINBASE 32
#define PIN_SCK 15
#define PIN_MOSI 13
#define PIN_MISO 14
#define CS 12
#define RESET 8
#define WAKE 11
#define IRQ 10
volatile uint32_t spi_timeouts;
static uint32_t ticks(void) { NRF_TIMER1->TASKS_CAPTURE[0]=1; return NRF_TIMER1->CC[0]; }
void deca_usleep(unsigned long us) { uint32_t s=ticks(); while((uint32_t)(ticks()-s)<us) {} }
void deca_sleep(unsigned int ms) { while(ms--) deca_usleep(1000); }
decaIrqStatus_t decamutexon(void) { uint32_t s=__get_PRIMASK(); __disable_irq(); return s; }
void decamutexoff(decaIrqStatus_t s) { __set_PRIMASK(s); }
static void output(unsigned p,unsigned v) { if(v) GPIO->OUTSET=1u<<p; else GPIO->OUTCLR=1u<<p; GPIO->PIN_CNF[p]=1; }
static void rate(void) { NRF_SPI0->FREQUENCY=0x80000000; }
static int byte(uint8_t tx,uint8_t *rx) { NRF_SPI0->EVENTS_READY=0; NRF_SPI0->TXD=tx; uint32_t s=ticks(); while(!NRF_SPI0->EVENTS_READY) { if((uint32_t)(ticks()-s)>10000) { spi_timeouts++; return -1; } } *rx=NRF_SPI0->RXD; return 0; }
static int32_t rd(uint16_t hn,uint8_t *h,uint16_t n,uint8_t *b) { uint8_t t; int e=0; GPIO->OUTCLR=1u<<CS; for(unsigned i=0;i<hn&&!e;i++) e=byte(h[i],&t); for(unsigned i=0;i<n&&!e;i++) e=byte(0,&b[i]); GPIO->OUTSET=1u<<CS; return e; }
static int32_t wr(uint16_t hn,const uint8_t *h,uint16_t n,const uint8_t *b) { uint8_t t; int e=0; GPIO->OUTCLR=1u<<CS; for(unsigned i=0;i<hn&&!e;i++) e=byte(h[i],&t); for(unsigned i=0;i<n&&!e;i++) e=byte(b[i],&t); GPIO->OUTSET=1u<<CS; return e; }
static int32_t wrcrc(uint16_t hn,const uint8_t *h,uint16_t n,const uint8_t *b,uint8_t crc) { (void)hn;(void)h;(void)n;(void)b;(void)crc; return -1; }
static void wake(void) { GPIO->OUTSET=1u<<WAKE; deca_sleep(1); GPIO->OUTCLR=1u<<WAKE; deca_sleep(5); }
extern const struct dwt_driver_s dw3000_driver;
static const struct dwt_driver_s *drivers[]={&dw3000_driver};
static const struct dwt_spi_s spi={.readfromspi=rd,.writetospi=wr,.writetospiwithcrc=wrcrc,.setslowrate=rate,.setfastrate=rate};
static const struct dwt_probe_s probe={.dw=0,.spi=(void*)&spi,.wakeup_device_with_io=wake,.driver_list=(struct dwt_driver_s**)drivers,.dw_driver_num=1};

#include "dw3000_deca_regs.h"
#include <string.h>
/* Host command: 1 responder, 2 root, 3 stop. All parameters precede command.
 * mode 0 individual poll, 1 group grant, 2 immediate relay, 3 aggregate relay.
 * mask bit 0/1/2 represents source 2/3/4. Every measurement is 4 bytes.
 */
volatile struct { uint32_t command,run,target,mode,node,parent,slot_us,turn_us,max_attempts,mask,quiet_from,quiet_rounds,preamble; } control;
volatile struct { uint32_t state,run,devid,rounds,unique,first_unique,missing,tx_frames,tx_data,tx_poll,tx_ack,
 rx_frames,duplicates,invalid,phy_errors,filtered,timeouts,late_tx,requests,retries,elapsed,round_max,
 round_sum_lo,round_sum_hi,hist_rounds,rounds_all,rounds_deadline,quiet_skips,relay_collections,relay_forwards;
 uint32_t node_unique[3],node_first[3],node_missing[3]; } stats;
uint8_t received[12500];
uint32_t round_hist[4096]; /* 25us bins, last bin >=102375us. */
static uint8_t txbuf[64],rxbuf[64],macseq;
static unsigned txlen,rxlen;
static uint64_t rxstamp,round_sum;
uint32_t window200_us[250],window300_us[167],window200_missing[250],window300_missing[167];
volatile struct {uint32_t collection_us,uplink_us,leaf_poll_calls,uplink_calls,windows200,windows300;} phase;
static uint32_t relay_values[3];
static uint32_t relay_round=0xffffffffu,relay_mask,relay_attempts[3];
enum { POLL=1,DATA=2,GROUP=3,ACK=4,COLLECT=5,FORWARD=6,AGGREGATE=7,DONE=8 };
static unsigned pop(uint32_t v) { unsigned n=0;while(v){v&=v-1;n++;}return n; }
static uint32_t get(const uint8_t *b,unsigned i) { return (uint32_t)b[i]|((uint32_t)b[i+1]<<8)|((uint32_t)b[i+2]<<16)|((uint32_t)b[i+3]<<24); }
static void put(uint8_t *b,unsigned i,uint32_t v) { for(unsigned j=0;j<4;j++)b[i+j]=v>>(8*j); }
static uint32_t value(unsigned node,uint32_t round) {return control.run^(round*2654435761u)^(node*0x45d9f3bu);}
static uint32_t source(void) {return rxbuf[7]|((uint32_t)rxbuf[8]<<8);}
static dwt_config_t config={5,DWT_PLEN_64,DWT_PAC8,9,9,1,DWT_BR_6M8,DWT_PHRMODE_STD,DWT_PHRRATE_STD,65,DWT_STS_MODE_OFF,DWT_STS_LEN_64,DWT_PDOA_M0};
static void off(void) {dwt_forcetrxoff();dwt_writesysstatuslo(DWT_INT_TXFRS_BIT_MASK|DWT_INT_RXFCG_BIT_MASK|SYS_STATUS_ALL_RX_ERR|SYS_STATUS_ALL_RX_TO);}
static void listen(void) {off();dwt_setrxtimeout(0);dwt_rxenable(DWT_START_RX_IMMEDIATE);}
static int setup(void) {
 NRF_SPI0->FREQUENCY=0x10000000;
 if(NRF_FICR->DEVICEID[0]!=0x06E5F278u){output(RESET,0);deca_sleep(2);GPIO->PIN_CNF[RESET]=0;}deca_sleep(10);
 if(dwt_probe((struct dwt_probe_s*)&probe))return -1;
 stats.devid=dwt_readdevid();if(stats.devid!=0xDECA0302)return -2;
 if(NRF_FICR->DEVICEID[0]==0x06E5F278u){dwt_softreset(0);deca_sleep(10);}
 uint32_t t=ticks();while(!dwt_checkidlerc())if(ticks()-t>100000)return -3;
 config.txPreambLength=control.preamble;config.sfdTO=control.preamble+1;
 if(dwt_initialise(DWT_READ_OTP_ALL)||dwt_configure(&config))return -4;
 dwt_txconfig_t power={0x34,0xfdfdfdfd,0};dwt_configuretxrf(&power);
 dwt_setpanid(0xDECA);dwt_setaddress16(control.node);dwt_configureframefilter(DWT_FF_ENABLE_802_15_4,DWT_FF_DATA_EN);
 NRF_SPI0->FREQUENCY=0x80000000;return 0;
}
static void prepare(unsigned type,unsigned destination,uint32_t round,uint32_t mask,uint32_t arg) {
 memset(txbuf,0,sizeof(txbuf));txbuf[0]=0x41;txbuf[1]=0x88;txbuf[2]=macseq++;
 txbuf[3]=0xca;txbuf[4]=0xde;txbuf[5]=destination;txbuf[6]=destination>>8;txbuf[7]=control.node;txbuf[8]=control.node>>8;
 txbuf[9]='F';txbuf[10]=1;txbuf[11]=type;put(txbuf,12,control.run);put(txbuf,16,round);put(txbuf,20,mask);put(txbuf,24,arg);
 txlen=30;
 if(type==DATA||type==FORWARD||type==AGGREGATE) {
  unsigned k=0;for(unsigned b=0;b<3;b++)if(mask&(1u<<b))put(txbuf,28+4*k++,(type==FORWARD||type==AGGREGATE)?relay_values[b]:value(b+2,round));
  txlen=30+4*pop(mask);
 }
}
static int transmit(uint64_t delayed) {
 off();dwt_writetxdata(txlen-2,txbuf,0);dwt_writetxfctrl(txlen,0,0);
 if(delayed)dwt_setdelayedtrxtime((uint32_t)(delayed>>8));
 if(dwt_starttx(delayed?DWT_START_TX_DELAYED:DWT_START_TX_IMMEDIATE)) {stats.late_tx++;off();return 0;}
 uint32_t t=ticks();while(!(dwt_readsysstatuslo()&DWT_INT_TXFRS_BIT_MASK)) {
  if(ticks()-t>30000||control.command==3){stats.timeouts++;off();return 0;}
 }
 dwt_writesysstatuslo(DWT_INT_TXFRS_BIT_MASK);stats.tx_frames++;
 if(txbuf[11]==DATA||txbuf[11]==FORWARD||txbuf[11]==AGGREGATE)stats.tx_data++;
 if(txbuf[11]==POLL||txbuf[11]==GROUP||txbuf[11]==COLLECT)stats.tx_poll++;
 if(txbuf[11]==ACK)stats.tx_ack++;
 return 1;
}
/* Receiver remains off after an event; caller rearms after consuming rxbuf. */
static int receive(void) {
 uint32_t s=dwt_readsysstatuslo();
 if(s&DWT_INT_RXFCG_BIT_MASK) {
  rxlen=dwt_getframelength(0);
  if(rxlen>=30&&rxlen<=42)dwt_readrxdata(rxbuf,rxlen,0);
  uint8_t ts[5];dwt_readrxtimestamp(ts,DWT_IP_M);rxstamp=0;for(unsigned i=0;i<5;i++)rxstamp|=(uint64_t)ts[i]<<(8*i);
  dwt_writesysstatuslo(DWT_INT_RXFCG_BIT_MASK);
  if(rxlen<30||rxlen>42||rxbuf[0]!=0x41||rxbuf[1]!=0x88||rxbuf[9]!='F'||rxbuf[10]!=1||get(rxbuf,12)!=control.run||source()<1||source()>4) {stats.invalid++;return -1;}
  unsigned type=rxbuf[11];uint32_t mask=get(rxbuf,20);
  unsigned expected=(type==DATA||type==FORWARD||type==AGGREGATE)?30+4*pop(mask):30;
  if((mask&~7u)||rxlen!=expected){stats.invalid++;return -1;}
  stats.rx_frames++;return 1;
 }
 if(s&(SYS_STATUS_ALL_RX_ERR|SYS_STATUS_ALL_RX_TO)) {
  if(s&DWT_INT_ARFE_BIT_MASK)stats.filtered++;else stats.phy_errors++;
  return -1;
 }
 return 0;
}
static int valid_payload(uint32_t round,uint32_t mask) {
 unsigned k=0;for(unsigned b=0;b<3;b++)if(mask&(1u<<b))if(get(rxbuf,28+4*k++)!=value(b+2,round))return 0;
 return 1;
}
static uint32_t poll_one(unsigned node,uint32_t round) {
 unsigned bit=1u<<(node-2);prepare(POLL,node,round,bit,control.turn_us);stats.requests++;
 if(!transmit(0))return 0;
 listen();uint32_t t=ticks();
 while(ticks()-t<control.turn_us+2500 && control.command!=3) {
  int r=receive();if(r==1) {
   if(rxbuf[11]==DATA&&source()==node&&get(rxbuf,16)==round&&get(rxbuf,20)==bit&&valid_payload(round,bit)) {if(control.node==2)relay_values[node-2]=get(rxbuf,28);off();return bit;}
   stats.invalid++;listen();
  }else if(r<0)listen();
 }
 stats.timeouts++;off();return 0;
}
static void ack(uint32_t round,uint32_t mask) {prepare(ACK,0xffff,round,mask,0);deca_usleep(200);transmit(0);deca_usleep(500);}
static void relay_send(unsigned type,uint32_t round,uint32_t mask) {
 uint32_t start=ticks();prepare(type,1,round,mask,0);deca_usleep(200);
 if(transmit(0))stats.relay_forwards++;
 phase.uplink_us+=ticks()-start;phase.uplink_calls++;
}
static void relay_collect(uint32_t round,uint32_t wanted) {
 if(relay_round!=round){relay_round=round;relay_mask=0;memset(relay_attempts,0,sizeof(relay_attempts));}
 stats.relay_collections++;
 for(unsigned b=1;b<3&&control.command!=3;b++)if(wanted&(1u<<b)) {
  uint32_t collect_start=ticks();unsigned previous_attempts=relay_attempts[b];
  while(!(relay_mask&(1u<<b))&&relay_attempts[b]<control.max_attempts&&control.command!=3) {
   if(relay_attempts[b])stats.retries++;
   relay_attempts[b]++;relay_mask|=poll_one(b+2,round);
  }
  phase.collection_us+=ticks()-collect_start;phase.leaf_poll_calls+=relay_attempts[b]-previous_attempts;
  if(control.mode==2&&(relay_mask&(1u<<b)))relay_send(FORWARD,round,1u<<b);
 }
 if(control.mode==3&&(relay_mask&wanted))relay_send(AGGREGATE,round,relay_mask&wanted);
 ack(round,relay_mask);
 prepare(DONE,1,round,relay_mask,0);deca_usleep(1000);transmit(0);listen();
}
static void responder(void) {
 int r=receive();if(!r)return;if(r<0){listen();return;}
 unsigned type=rxbuf[11],src=source();uint32_t round=get(rxbuf,16),mask=get(rxbuf,20),arg=get(rxbuf,24);
 if(src!=control.parent){stats.invalid++;listen();return;}
 if(type==ACK){listen();return;}
 if(type==COLLECT&&control.node==2&&control.mode>=2){relay_collect(round,mask);return;}
 uint32_t own=1u<<(control.node-2);
 if((type==POLL||type==GROUP)&&(mask&own)) {
  if(control.quiet_rounds&&round>=control.quiet_from&&round-control.quiet_from<control.quiet_rounds){stats.quiet_skips++;listen();return;}
  unsigned rank=pop(mask&(own-1));uint32_t offset=control.turn_us+(type==GROUP?rank*arg:0);
  uint64_t scheduled=(rxstamp+(uint64_t)offset*638976/10)&0xffffffffffULL;
  prepare(DATA,control.parent,round,own,0);transmit(scheduled);listen();return;
 }
 stats.invalid++;listen();
}
static void record(uint32_t round,uint32_t mask,int first) {
 unsigned count=pop(control.mask),rank=0;
 for(unsigned b=0;b<3;b++)if(control.mask&(1u<<b)) {
  uint32_t index=round*count+rank++;
  if(!(mask&(1u<<b))||index>=control.target)continue;
  uint8_t bit=1u<<(index%8);
  if(received[index/8]&bit){stats.duplicates++;continue;}
  received[index/8]|=bit;stats.unique++;stats.node_unique[b]++;
  if(first){stats.first_unique++;stats.node_first[b]++;}
 }
}
static uint32_t group_receive(uint32_t round,uint32_t expected) {
 prepare(GROUP,0xffff,round,expected,control.slot_us);stats.requests++;
 if(!transmit(0))return 0;
 listen();uint32_t t=ticks(),seen=0,limit=control.turn_us+(pop(expected)-1)*control.slot_us+1500;
 while(ticks()-t<limit&&control.command!=3) {
  int r=receive();if(r==1) {
   uint32_t m=get(rxbuf,20);unsigned src=source();
   if(rxbuf[11]==DATA&&src>=2&&get(rxbuf,16)==round&&m==(1u<<(src-2))&&(m&expected)&&valid_payload(round,m)) {
    record(round,m,1);seen|=m;
   }else stats.invalid++;
   listen();if(seen==expected)break;
  }else if(r<0)listen();
 }
 off();return seen;
}
static uint32_t tree_receive(uint32_t round,uint32_t expected,int first) {
 prepare(COLLECT,2,round,expected,0);stats.requests++;if(!transmit(0))return 0;
 listen();uint32_t t=ticks(),seen=0;
 while(ticks()-t<60000&&control.command!=3) {
  int r=receive();if(r==1) {
   unsigned type=rxbuf[11];uint32_t m=get(rxbuf,20);
   if(source()==2&&get(rxbuf,16)==round) {
    if((type==FORWARD||type==AGGREGATE)&&!(m&~expected)&&valid_payload(round,m)) {record(round,m,first);seen|=m;}
    else if(type==DONE){off();return seen;}
    else if(type!=ACK)stats.invalid++;
   }else stats.invalid++;
   listen();
  }else if(r<0)listen();
 }
 stats.timeouts++;off();return seen;
}
static void root_run(void) {
 uint32_t start=ticks(),count=pop(control.mask),nrounds=(control.target+count-1)/count;
 uint32_t w200_start=start,w300_start=start,w200_lost=0,w300_lost=0;
 for(uint32_t round=0;round<nrounds&&control.command!=3;round++) {
  uint32_t expected=0,remaining=control.target-round*count;unsigned rank=0;
  for(unsigned b=0;b<3;b++)if(control.mask&(1u<<b)){if(rank++<remaining)expected|=1u<<b;}
  uint32_t begin=ticks(),seen=0;
  if(control.mode>=2) {
   for(unsigned attempt=0;attempt<control.max_attempts&&seen!=expected&&control.command!=3;attempt++) {
    if(attempt)stats.retries++;
    seen|=tree_receive(round,expected&~seen,attempt==0);
   }
  } else {
   if(control.mode==1)seen=group_receive(round,expected);
   for(unsigned b=0;b<3;b++)if(expected&(1u<<b)) {
    for(unsigned attempt=control.mode==1?1:0;attempt<control.max_attempts&&!(seen&(1u<<b))&&control.command!=3;attempt++) {
     if(attempt)stats.retries++;
     uint32_t m=poll_one(b+2,round);record(round,m,attempt==0);seen|=m;
    }
   }
  }
  ack(round,seen);
  for(unsigned b=0;b<3;b++)if((expected&~seen)&(1u<<b))stats.node_missing[b]++;
  stats.missing+=pop(expected&~seen);stats.rounds++;
  uint32_t duration=ticks()-begin;
  if(expected==control.mask) {
   round_sum+=duration;stats.round_sum_lo=(uint32_t)round_sum;stats.round_sum_hi=(uint32_t)(round_sum>>32);
   stats.hist_rounds++;if(duration>stats.round_max)stats.round_max=duration;
   unsigned bin=duration/25;round_hist[bin<4095?bin:4095]++;
   if(seen==expected){stats.rounds_all++;if(duration<=100000)stats.rounds_deadline++;}
  }
  uint32_t end=ticks();w200_lost+=pop(expected&~seen);w300_lost+=pop(expected&~seen);
  if((round+1)%100==0&&phase.windows200<250){unsigned k=phase.windows200++;window200_us[k]=end-w200_start;window200_missing[k]=w200_lost;w200_start=end;w200_lost=0;}
  if((round+1)%150==0&&phase.windows300<167){unsigned k=phase.windows300++;window300_us[k]=end-w300_start;window300_missing[k]=w300_lost;w300_start=end;w300_lost=0;}
  stats.elapsed=end-start;
 }
 off();stats.state=control.command==3?5:3;
}
int main(void) {
 NRF_TIMER1->MODE=0; NRF_TIMER1->BITMODE=3; NRF_TIMER1->PRESCALER=4; NRF_TIMER1->TASKS_CLEAR=1; NRF_TIMER1->TASKS_START=1;
 NRF_CLOCK->EVENTS_HFCLKSTARTED=0; NRF_CLOCK->TASKS_HFCLKSTART=1;
 uint32_t clock_start=ticks(); while(!NRF_CLOCK->EVENTS_HFCLKSTARTED) {if(ticks()-clock_start>100000) {stats.state=110;while(1) {}}}
 SEGGER_RTT_Init(); SEGGER_RTT_SetFlagsUpBuffer(0,SEGGER_RTT_MODE_NO_BLOCK_SKIP);
 output(CS,1); output(WAKE,0); GPIO->PIN_CNF[IRQ]=0; GPIO->PIN_CNF[RESET]=0;
 output(PIN_SCK,0); output(PIN_MOSI,0); GPIO->PIN_CNF[PIN_MISO]=0;
 NRF_SPI0->PSELSCK=PINBASE+PIN_SCK; NRF_SPI0->PSELMOSI=PINBASE+PIN_MOSI; NRF_SPI0->PSELMISO=PINBASE+PIN_MISO; NRF_SPI0->CONFIG=0; rate(); NRF_SPI0->ENABLE=1;



 SEGGER_RTT_WriteString(0,"Four-board POLL experiment ready\n");
 while(1) {
  if(control.command) {
   unsigned cmd=control.command;control.command=0;
   if(cmd==3){if(stats.devid==0xDECA0302)off();stats.state=5;continue;}
   memset((void*)&stats,0,sizeof(stats));memset(received,0,sizeof(received));memset(round_hist,0,sizeof(round_hist));round_sum=0;relay_round=0xffffffffu;
   memset((void*)&phase,0,sizeof(phase));memset(relay_values,0,sizeof(relay_values));
   memset(window200_us,0,sizeof(window200_us));memset(window300_us,0,sizeof(window300_us));memset(window200_missing,0,sizeof(window200_missing));memset(window300_missing,0,sizeof(window300_missing));
   stats.run=control.run;
   if((cmd!=1&&cmd!=2)||control.node<1||control.node>4||control.mode>3||!control.target||control.target>100000||!control.mask||(control.mask&~7u)||control.max_attempts<1||control.max_attempts>5||control.turn_us<500||control.turn_us>10000||control.slot_us>5000||(control.preamble!=64&&control.preamble!=32)){stats.state=90;continue;}
   int e=setup();if(e){stats.state=100-e;continue;}
   stats.state=cmd;if(cmd==2)root_run();else listen();
  }
  if(stats.state==1)responder();
 }
}
