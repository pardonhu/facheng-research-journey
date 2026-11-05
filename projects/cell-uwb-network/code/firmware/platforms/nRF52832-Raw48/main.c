#include "nrf.h"
#include "deca_device_api.h"
#include "deca_interface.h"
#include "SEGGER_RTT.h"
#include <stdio.h>
#include <stdint.h>
#define GPIO NRF_P0
#define PINBASE 0
#define PIN_SCK 25
#define PIN_MOSI 23
#define PIN_MISO 24
#define CS 22
#define RESET 18
#define WAKE 20
#define IRQ 19
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
/* A DATA frame is exactly a 32-bit test value plus hardware CRC16.
 * Requests also use 32-bit payloads, in the reverse direction.
 * This two-node test has one outstanding request; it does not implement a
 * multi-node slot/address inference scheme. No MAC header or automatic ACK. */
volatile struct {uint32_t command,run,target,preamble,fast_phr,wait_us,max_attempts,drop_every;} control;
volatile struct {uint32_t state,devid,unique,first_unique,missing,tx_frames,rx_frames,retries,invalid,phy_errors,timeouts,late_tx,elapsed_us,round_max_us,first_missing,injected_drops;
 uint64_t round_sum_us,spacing_sum_dtu;uint32_t spacing_count,spacing_min_us,spacing_max_us;int32_t gap_min_ns,gap_max_ns;int64_t gap_sum_ns;uint32_t gap_count;} stats;
uint8_t received[1250];
static uint64_t rxstamp,last_received,air_dtu;
static uint32_t last_id=0xffffffffu;
static unsigned repeats;
static dwt_config_t config={5,DWT_PLEN_64,DWT_PAC8,9,9,1,DWT_BR_6M8,DWT_PHRMODE_STD,DWT_PHRRATE_STD,65,DWT_STS_MODE_OFF,DWT_STS_LEN_64,DWT_PDOA_M0};
static uint64_t stamp(int tx){uint8_t b[5];uint64_t v=0;if(tx)dwt_readtxtimestamp(b);else dwt_readrxtimestamp(b,DWT_IP_M);for(unsigned i=0;i<5;i++)v|=(uint64_t)b[i]<<(8*i);return v;}
static int64_t diff(uint64_t a,uint64_t b){uint64_t d=(a-b)&0xffffffffffULL;return d&(1ULL<<39)?(int64_t)d-(1LL<<40):(int64_t)d;}
static void off(void){dwt_forcetrxoff();dwt_writesysstatuslo(DWT_INT_TXFRS_BIT_MASK|DWT_INT_RXFCG_BIT_MASK|SYS_STATUS_ALL_RX_ERR|SYS_STATUS_ALL_RX_TO);}
static void listen(void){off();dwt_setrxtimeout(0);dwt_rxenable(DWT_START_RX_IMMEDIATE);}
static int setup(void){
 NRF_SPI0->FREQUENCY=0x10000000;
 if(NRF_FICR->DEVICEID[0]!=0x06E5F278u){output(RESET,0);deca_sleep(2);GPIO->PIN_CNF[RESET]=0;}deca_sleep(10);
 if(dwt_probe((struct dwt_probe_s*)&probe))return -1;
 stats.devid=dwt_readdevid();if(stats.devid!=0xDECA0302)return -2;
 if(NRF_FICR->DEVICEID[0]==0x06E5F278u){dwt_softreset(0);deca_sleep(10);}
 uint32_t t=ticks();while(!dwt_checkidlerc())if(ticks()-t>100000)return -3;
 config.txPreambLength=control.preamble;config.sfdTO=control.preamble+8+1-8;
 config.phrRate=control.fast_phr?DWT_PHRRATE_DTA:DWT_PHRRATE_STD;
 if(dwt_initialise(DWT_READ_OTP_ALL)||dwt_configure(&config))return -4;
 dwt_txconfig_t power={0x34,0xfdfdfdfd,0};dwt_configuretxrf(&power);
 dwt_configureframefilter(DWT_FF_DISABLE,0);
 /* 1.01763 us/symbol SHR; PHR 21 symbols; DATA 48 bits + RS48. */
 uint64_t ns100=(uint64_t)(control.preamble+8)*101763+21ULL*(control.fast_phr?12821:102564)+96ULL*12821;
 air_dtu=ns100*638976/1000000;
 NRF_SPI0->FREQUENCY=0x80000000;return 0;
}
static int send(uint32_t v,uint64_t when){
 uint8_t b[4];for(unsigned i=0;i<4;i++)b[i]=v>>(8*i);
 off();dwt_writetxdata(4,b,0);dwt_writetxfctrl(6,0,0);
 if(when)dwt_setdelayedtrxtime((uint32_t)(when>>8));
 if(dwt_starttx(when?DWT_START_TX_DELAYED:DWT_START_TX_IMMEDIATE)){stats.late_tx++;off();return 0;}
 uint32_t t=ticks();while(!(dwt_readsysstatuslo()&DWT_INT_TXFRS_BIT_MASK)){
  if(ticks()-t>10000||control.command==3){stats.timeouts++;off();return 0;}
 }
 dwt_writesysstatuslo(DWT_INT_TXFRS_BIT_MASK);stats.tx_frames++;return 1;
}
static int receive(uint32_t *v){
 uint32_t s=dwt_readsysstatuslo();
 if(s&DWT_INT_RXFCG_BIT_MASK){
  unsigned n=dwt_getframelength(0);uint8_t b[6];
  if(n==6)dwt_readrxdata(b,6,0);
  rxstamp=stamp(0);dwt_writesysstatuslo(DWT_INT_RXFCG_BIT_MASK);
  if(n!=6){stats.invalid++;return -1;}
  *v=(uint32_t)b[0]|((uint32_t)b[1]<<8)|((uint32_t)b[2]<<16)|((uint32_t)b[3]<<24);
  stats.rx_frames++;return 1;
 }
 if(s&(SYS_STATUS_ALL_RX_ERR|SYS_STATUS_ALL_RX_TO)){stats.phy_errors++;return -1;}
 return 0;
}
static uint32_t value(uint32_t id){return id*2654435761u^control.run;}
static void responder(void){
 uint32_t v;int r=receive(&v);if(!r)return;if(r<0){listen();return;}
 uint32_t id=v^control.run;if(id>=control.target){stats.invalid++;listen();return;}
 if(last_id!=id){last_id=id;repeats=0;}repeats++;
 if(control.drop_every&&id%control.drop_every==0&&repeats==1){stats.injected_drops++;listen();return;}
 uint64_t incoming=rxstamp;
 uint64_t when=(incoming+air_dtu+(uint64_t)control.wait_us*638976/10-dwt_gettxantennadelay())&0xffffffffffULL;
 if(send(value(id),when)){
  int32_t ns=(int32_t)((diff(stamp(1),incoming)-(int64_t)air_dtu)*10000/638976);
  if(!stats.gap_count||ns<stats.gap_min_ns)stats.gap_min_ns=ns;
  if(!stats.gap_count||ns>stats.gap_max_ns)stats.gap_max_ns=ns;
  stats.gap_sum_ns+=ns;stats.gap_count++;
 }
 listen();
}
static void root_run(void){
 uint32_t start=ticks();last_received=0;
 for(uint32_t id=0;id<control.target&&control.command!=3;id++){
  uint32_t begin=ticks();int got=0;
  for(unsigned attempt=0;attempt<control.max_attempts&&!got;attempt++){
   if(attempt)stats.retries++;
   if(!send(id^control.run,0))continue;
   listen();uint32_t t=ticks();
   while(ticks()-t<control.wait_us+1500&&control.command!=3){
    uint32_t v;int r=receive(&v);
    if(r==1){if(v==value(id)){
      got=1;stats.unique++;if(!attempt)stats.first_unique++;received[id/8]|=1u<<(id%8);
      if(last_received){uint64_t d=(uint64_t)diff(rxstamp,last_received);uint32_t us=d*10/638976;
       stats.spacing_sum_dtu+=d;if(!stats.spacing_count||us<stats.spacing_min_us)stats.spacing_min_us=us;
       if(us>stats.spacing_max_us)stats.spacing_max_us=us;stats.spacing_count++;
      }last_received=rxstamp;break;
     }stats.invalid++;listen();
    }else if(r<0)listen();
   }
   if(!got){stats.timeouts++;if(!attempt)stats.first_missing++;}
   off();
  }
  if(!got)stats.missing++;
  uint32_t dur=ticks()-begin;stats.round_sum_us+=dur;if(dur>stats.round_max_us)stats.round_max_us=dur;
  stats.elapsed_us=ticks()-start;
 }
 off();stats.state=control.command==3?5:3;
}
int main(void){
 NRF_TIMER1->MODE=0; NRF_TIMER1->BITMODE=3; NRF_TIMER1->PRESCALER=4; NRF_TIMER1->TASKS_CLEAR=1; NRF_TIMER1->TASKS_START=1;
 NRF_CLOCK->EVENTS_HFCLKSTARTED=0; NRF_CLOCK->TASKS_HFCLKSTART=1;
 uint32_t clock_start=ticks(); while(!NRF_CLOCK->EVENTS_HFCLKSTARTED) {if(ticks()-clock_start>100000) {stats.state=110;while(1) {}}}
 SEGGER_RTT_Init(); SEGGER_RTT_SetFlagsUpBuffer(0,SEGGER_RTT_MODE_NO_BLOCK_SKIP);
 output(CS,1); output(WAKE,0); GPIO->PIN_CNF[IRQ]=0; GPIO->PIN_CNF[RESET]=0;
 output(PIN_SCK,0); output(PIN_MOSI,0); GPIO->PIN_CNF[PIN_MISO]=0;
 NRF_SPI0->PSELSCK=PINBASE+PIN_SCK; NRF_SPI0->PSELMOSI=PINBASE+PIN_MOSI; NRF_SPI0->PSELMISO=PINBASE+PIN_MISO; NRF_SPI0->CONFIG=0; rate(); NRF_SPI0->ENABLE=1;





 while(1){
  if(control.command){unsigned cmd=control.command;control.command=0;
   if(cmd==3){if(stats.devid==0xdeca0302)off();stats.state=5;continue;}
   memset((void*)&stats,0,sizeof(stats));memset(received,0,sizeof(received));last_id=0xffffffffu;
   if((cmd!=1&&cmd!=2)||!control.target||control.target>10000||(control.preamble!=32&&control.preamble!=64)||control.fast_phr>1||control.wait_us>5000||!control.max_attempts){stats.state=90;continue;}
   int e=setup();if(e){stats.state=100-e;continue;}
   stats.state=cmd;if(cmd==2)root_run();else listen();
  }
  if(stats.state==1)responder();
 }
}
