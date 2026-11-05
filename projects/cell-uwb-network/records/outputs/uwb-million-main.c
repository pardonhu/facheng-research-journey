#include "nrf.h"
#include "deca_device_api.h"
#include "deca_interface.h"
#include "SEGGER_RTT.h"
#include <stdio.h>
#include <stdint.h>
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
static void output(unsigned p,unsigned v) { if(v) NRF_P0->OUTSET=1u<<p; else NRF_P0->OUTCLR=1u<<p; NRF_P0->PIN_CNF[p]=1; }
static void rate(void) { NRF_SPI0->FREQUENCY=0x80000000; }
static int byte(uint8_t tx,uint8_t *rx) { NRF_SPI0->EVENTS_READY=0; NRF_SPI0->TXD=tx; uint32_t s=ticks(); while(!NRF_SPI0->EVENTS_READY) { if((uint32_t)(ticks()-s)>10000) { spi_timeouts++; return -1; } } *rx=NRF_SPI0->RXD; return 0; }
static int32_t rd(uint16_t hn,uint8_t *h,uint16_t n,uint8_t *b) { uint8_t t; int e=0; NRF_P0->OUTCLR=1u<<CS; for(unsigned i=0;i<hn&&!e;i++) e=byte(h[i],&t); for(unsigned i=0;i<n&&!e;i++) e=byte(0,&b[i]); NRF_P0->OUTSET=1u<<CS; return e; }
static int32_t wr(uint16_t hn,const uint8_t *h,uint16_t n,const uint8_t *b) { uint8_t t; int e=0; NRF_P0->OUTCLR=1u<<CS; for(unsigned i=0;i<hn&&!e;i++) e=byte(h[i],&t); for(unsigned i=0;i<n&&!e;i++) e=byte(b[i],&t); NRF_P0->OUTSET=1u<<CS; return e; }
static int32_t wrcrc(uint16_t hn,const uint8_t *h,uint16_t n,const uint8_t *b,uint8_t crc) { (void)hn;(void)h;(void)n;(void)b;(void)crc; return -1; }
static void wake(void) { NRF_P0->OUTSET=1u<<WAKE; deca_sleep(1); NRF_P0->OUTCLR=1u<<WAKE; deca_sleep(5); }
extern const struct dwt_driver_s dw3000_driver;
static const struct dwt_driver_s *drivers[]={&dw3000_driver};
static const struct dwt_spi_s spi={.readfromspi=rd,.writetospi=wr,.writetospiwithcrc=wrcrc,.setslowrate=rate,.setfastrate=rate};
static const struct dwt_probe_s probe={.dw=0,.spi=(void*)&spi,.wakeup_device_with_io=wake,.driver_list=(struct dwt_driver_s**)drivers,.dw_driver_num=1};

#include "dw3000_deca_regs.h"
#include <string.h>
/* Host writes fields, then command last: 1=RX, 2=TX, 3=stop. */
volatile struct { uint32_t command,run,count,interval,length,channel,destination,pan,node; } control;
volatile struct { uint32_t state,run,tx,rx,duplicate,bad,errors,timeouts,last,elapsed; } stats;
static uint8_t seen[8192];
static uint32_t high_seq; static int have_seq;
static dwt_config_t config={5,DWT_PLEN_128,DWT_PAC8,9,9,1,DWT_BR_6M8,DWT_PHRMODE_STD,DWT_PHRRATE_STD,129,DWT_STS_MODE_OFF,DWT_STS_LEN_64,DWT_PDOA_M0};
static void logstats(void) { char b[230]; snprintf(b,sizeof(b),"STAT state=%lu run=%lu tx=%lu rx=%lu duplicate=%lu bad=%lu errors=%lu timeout=%lu last=%lu elapsed_us=%lu spi_timeout=%lu\n",(unsigned long)stats.state,(unsigned long)stats.run,(unsigned long)stats.tx,(unsigned long)stats.rx,(unsigned long)stats.duplicate,(unsigned long)stats.bad,(unsigned long)stats.errors,(unsigned long)stats.timeouts,(unsigned long)stats.last,(unsigned long)stats.elapsed,(unsigned long)spi_timeouts); SEGGER_RTT_WriteString(0,b); }
static int setup(void) { NRF_SPI0->FREQUENCY=0x10000000;
 output(RESET,0); deca_sleep(2); NRF_P0->PIN_CNF[RESET]=0; deca_sleep(10);
 if(dwt_probe((struct dwt_probe_s*)&probe)||dwt_readdevid()!=0xDECA0302) return -1;
 uint32_t t=ticks(); while(!dwt_checkidlerc()) if(ticks()-t>100000) return -2;
 if(dwt_initialise(DWT_READ_OTP_ALL)) return -3;
 config.chan=control.channel==9?9:5;
 if(dwt_configure(&config)) return -4;
 dwt_txconfig_t power={0x34,config.chan==9?0xfefefefe:0xfdfdfdfd,0}; dwt_configuretxrf(&power); dwt_setpanid(control.pan); dwt_setaddress16(control.node); dwt_configureframefilter(DWT_FF_ENABLE_802_15_4,DWT_FF_DATA_EN); NRF_SPI0->FREQUENCY=0x80000000; return 0;
}
int main(void) {
 NRF_TIMER1->MODE=0; NRF_TIMER1->BITMODE=3; NRF_TIMER1->PRESCALER=4; NRF_TIMER1->TASKS_CLEAR=1; NRF_TIMER1->TASKS_START=1;
 SEGGER_RTT_Init(); SEGGER_RTT_SetFlagsUpBuffer(0,SEGGER_RTT_MODE_NO_BLOCK_SKIP);
 output(CS,1); output(WAKE,0); NRF_P0->PIN_CNF[IRQ]=0; NRF_P0->PIN_CNF[RESET]=0;
 output(25,0); output(23,0); NRF_P0->PIN_CNF[24]=0;
 NRF_SPI0->PSELSCK=25; NRF_SPI0->PSELMOSI=23; NRF_SPI0->PSELMISO=24; NRF_SPI0->CONFIG=0; rate(); NRF_SPI0->ENABLE=1;
 uint32_t start=0,report=0,next=0,target=0,len=32,interval=100000; uint8_t frame[100];
 SEGGER_RTT_WriteString(0,"P2P ready: waiting for host command\n");
 while(1) {
 if(control.command) { uint32_t cmd=control.command; control.command=0;
 if(cmd==3) { if(stats.state==1||stats.state==2||stats.state==3) dwt_forcetrxoff(); stats.state=3; logstats(); continue; }
 memset((void*)&stats,0,sizeof(stats)); memset(seen,0,sizeof(seen)); high_seq=0; have_seq=0; stats.run=control.run; target=control.count; len=control.length; interval=control.interval;
 if(target>1000000||len<24||len>64||interval>1000000) { stats.state=90; logstats(); continue; }
 int e=setup(); if(e) { stats.state=100-e; logstats(); continue; }
 stats.state=cmd; start=report=next=ticks(); if(cmd==1) { dwt_setrxtimeout(0); dwt_rxenable(DWT_START_RX_IMMEDIATE); }
 }
 if(stats.state==2 && (int32_t)(ticks()-next)>=0) {
 uint32_t seq=stats.tx; memset(frame,0,len); frame[0]=0x41; frame[1]=0x88; frame[2]=(uint8_t)seq; frame[3]=control.pan; frame[4]=control.pan>>8; frame[5]=control.destination; frame[6]=control.destination>>8; frame[7]=control.node; frame[8]=control.node>>8; memcpy(frame+9,(const void*)&stats.run,4); memcpy(frame+13,&seq,4); for(unsigned i=17;i<len;i++) frame[i]=(uint8_t)(seq+i*37);
 dwt_writesysstatuslo(DWT_INT_TXFRS_BIT_MASK); dwt_writetxdata(len,frame,0); dwt_writetxfctrl(len+2,0,0);
 if(dwt_starttx(DWT_START_TX_IMMEDIATE)) { stats.errors++; stats.state=91; }
 else { uint32_t t=ticks(); while(!(dwt_readsysstatuslo()&DWT_INT_TXFRS_BIT_MASK)) { if(ticks()-t>100000) { stats.timeouts++; stats.state=92; break; } } if(stats.state==2) stats.tx++; }
 stats.elapsed=ticks()-start; next=ticks()+interval;
 if(stats.tx>=target) stats.state=3;
 if(stats.state!=2) logstats();
 }
 if(stats.state==1) {
 uint32_t status=dwt_readsysstatuslo();
 if(status&DWT_INT_RXFCG_BIT_MASK) {
 uint32_t n=dwt_read_reg(RX_FINFO_ID)&0x3ff; uint32_t run=0,seq=0; int good=n==len+2;
 if(good) { dwt_readrxdata(frame,len,0); memcpy(&run,frame+9,4); memcpy(&seq,frame+13,4); good=frame[0]==0x41&&frame[1]==0x88&&run==stats.run&&seq<target; for(unsigned i=17;i<len&&good;i++) if(frame[i]!=(uint8_t)(seq+i*37)) good=0; }
 if(good) {
 if(!have_seq) { high_seq=seq; have_seq=1; }
 else if(seq>high_seq) { uint32_t jump=seq-high_seq; if(jump>=65536) memset(seen,0,sizeof(seen)); else for(uint32_t v=high_seq+1;v<=seq;v++) seen[(v%65536)/8]&=(uint8_t)~(1u<<(v%8)); high_seq=seq; }
 if(high_seq-seq>=65536) { stats.bad++; } else { uint32_t ix=seq%65536; if(seen[ix/8]&(1u<<(ix%8))) stats.duplicate++; else { seen[ix/8]|=1u<<(ix%8); stats.rx++; } }
 stats.last=seq;
 } else stats.bad++;
 dwt_writesysstatuslo(DWT_INT_RXFCG_BIT_MASK); dwt_rxenable(DWT_START_RX_IMMEDIATE);
 } else if(status&(SYS_STATUS_ALL_RX_ERR|SYS_STATUS_ALL_RX_TO)) { stats.errors++; dwt_forcetrxoff(); dwt_writesysstatuslo(SYS_STATUS_ALL_RX_ERR|SYS_STATUS_ALL_RX_TO); dwt_rxenable(DWT_START_RX_IMMEDIATE); }
 stats.elapsed=ticks()-start;
 }
 if(stats.state!=1 && stats.state!=2 && ticks()-report>1000000) { report=ticks(); logstats(); }
 }
}



