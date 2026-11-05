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
static void rate(void) { NRF_SPI0->FREQUENCY=0x10000000; }
static int byte(uint8_t tx,uint8_t *rx) { NRF_SPI0->EVENTS_READY=0; NRF_SPI0->TXD=tx; uint32_t s=ticks(); while(!NRF_SPI0->EVENTS_READY) { if((uint32_t)(ticks()-s)>10000) { spi_timeouts++; return -1; } } *rx=NRF_SPI0->RXD; return 0; }
static int32_t rd(uint16_t hn,uint8_t *h,uint16_t n,uint8_t *b) { uint8_t t; int e=0; NRF_P0->OUTCLR=1u<<CS; for(unsigned i=0;i<hn&&!e;i++) e=byte(h[i],&t); for(unsigned i=0;i<n&&!e;i++) e=byte(0,&b[i]); NRF_P0->OUTSET=1u<<CS; return e; }
static int32_t wrcrc(uint16_t hn,const uint8_t *h,uint16_t n,const uint8_t *b,uint8_t crc) { (void)hn;(void)h;(void)n;(void)b;(void)crc; return -1; }
/* Identification is read-only: reject all device-register writes. */
static int32_t wr(uint16_t hn,const uint8_t *h,uint16_t n,const uint8_t *b) { (void)hn;(void)h;(void)n;(void)b; return -1; }
static void wake(void) { NRF_P0->OUTSET=1u<<WAKE; deca_sleep(1); NRF_P0->OUTCLR=1u<<WAKE; deca_sleep(5); }
extern const struct dwt_driver_s dw3000_driver;
static const struct dwt_driver_s *drivers[]={&dw3000_driver};
static const struct dwt_spi_s spi={.readfromspi=rd,.writetospi=wr,.writetospiwithcrc=wrcrc,.setslowrate=rate,.setfastrate=rate};
static const struct dwt_probe_s probe={.dw=0,.spi=(void*)&spi,.wakeup_device_with_io=wake,.driver_list=(struct dwt_driver_s**)drivers,.dw_driver_num=1};
int main(void) {
 NRF_TIMER1->MODE=0; NRF_TIMER1->BITMODE=3; NRF_TIMER1->PRESCALER=4; NRF_TIMER1->TASKS_CLEAR=1; NRF_TIMER1->TASKS_START=1;
 SEGGER_RTT_Init(); SEGGER_RTT_SetFlagsUpBuffer(0,SEGGER_RTT_MODE_NO_BLOCK_SKIP);
 output(CS,1); output(WAKE,0); NRF_P0->PIN_CNF[IRQ]=0; NRF_P0->PIN_CNF[RESET]=0;
 output(25,0); output(23,0); NRF_P0->PIN_CNF[24]=0;
 NRF_SPI0->PSELSCK=25; NRF_SPI0->PSELMOSI=23; NRF_SPI0->PSELMISO=24; NRF_SPI0->CONFIG=0; rate(); NRF_SPI0->ENABLE=1;
 output(RESET,0); deca_sleep(2); NRF_P0->PIN_CNF[RESET]=0; deca_sleep(10);
 unsigned count=0;
 while(1) { char msg[240]; uint8_t h=0,b[4]={0}; int raw_status=rd(1,&h,4,b); uint32_t raw=(uint32_t)b[0]|((uint32_t)b[1]<<8)|((uint32_t)b[2]<<16)|((uint32_t)b[3]<<24);
 int p=dwt_probe((struct dwt_probe_s*)&probe); uint32_t id=0; int check=-1; if(p==0) { id=dwt_readdevid(); check=dwt_check_dev_id(); }
 snprintf(msg,sizeof(msg),"PCA10040 ID test #%u SPI0 1MHz MODE0 raw=%08lX io=%d probe=%d id=%08lX check=%d expected=DECA0302 %s timeouts=%lu\n",++count,(unsigned long)raw,raw_status,p,(unsigned long)id,check,(raw_status==0&&p==0&&id==0xDECA0302&&check==0)?"PASS":"FAIL",(unsigned long)spi_timeouts);
 SEGGER_RTT_WriteString(0,msg); deca_sleep(2000); }
}

