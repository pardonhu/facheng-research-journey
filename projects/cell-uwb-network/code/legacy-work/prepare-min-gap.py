from pathlib import Path
root=Path.cwd();base=root/'work/toolnail-UWB/DW3_QM33_SDK_1.1.1/Drivers/API/Build_Platforms'
dma=r'''static uint8_t dma_tx[128],dma_rx[128];
static int transfer(unsigned hn,const uint8_t *h,unsigned n,const uint8_t *b,uint8_t *r){
 unsigned len=hn+n;if(len>sizeof(dma_tx))return -1;
 for(unsigned i=0;i<hn;i++)dma_tx[i]=h[i];
 for(unsigned i=0;i<n;i++)dma_tx[hn+i]=b?b[i]:0;
 NRF_SPIM0->TXD.PTR=(uint32_t)dma_tx;NRF_SPIM0->TXD.MAXCNT=len;
 NRF_SPIM0->RXD.PTR=(uint32_t)dma_rx;NRF_SPIM0->RXD.MAXCNT=r?len:0;
 NRF_SPIM0->EVENTS_END=0;GPIO->OUTCLR=1u<<CS;NRF_SPIM0->TASKS_START=1;
 uint32_t t=ticks();while(!NRF_SPIM0->EVENTS_END)if(ticks()-t>10000){spi_timeouts++;GPIO->OUTSET=1u<<CS;return -1;}
 GPIO->OUTSET=1u<<CS;for(unsigned i=0;r&&i<n;i++)r[i]=dma_rx[hn+i];return 0;
}
static int32_t rd(uint16_t hn,uint8_t *h,uint16_t n,uint8_t *b){return transfer(hn,h,n,0,b);}
static int32_t wr(uint16_t hn,const uint8_t *h,uint16_t n,const uint8_t *b){return transfer(hn,h,n,b,0);}
'''
body=(root/'work/min-gap-body.c').read_text()
for chip in ('52832','52840'):
 old=base/f'nRF{chip}-BroadcastTree';dst=base/f'nRF{chip}-MinGap';dst.mkdir(exist_ok=True)
 full=(old/'main.c').read_text();prefix=full[:full.index('#include "dw3000_deca_regs.h"')]
 a=prefix.index('static int byte(');b=prefix.index('static int32_t wrcrc(',a);prefix=prefix[:a]+dma+prefix[b:]
 init=full[full.index(' NRF_TIMER1->MODE='):full.index(' SEGGER_RTT_WriteString(0,"Four-board')]
 init=init.replace('NRF_SPI0->PSELSCK','NRF_SPIM0->PSEL.SCK').replace('NRF_SPI0->PSELMOSI','NRF_SPIM0->PSEL.MOSI').replace('NRF_SPI0->PSELMISO','NRF_SPIM0->PSEL.MISO').replace('NRF_SPI0->CONFIG','NRF_SPIM0->CONFIG').replace('NRF_SPI0->ENABLE=1','NRF_SPIM0->ENABLE=7')
 full=prefix+body.replace('/* PLATFORM_INIT */',init)
 # Dedicated SPIM3 on nRF52840 supports 32 MHz; nRF52832 remains at 8 MHz.
 full=full.replace('static void rate(void) { NRF_SPI0->FREQUENCY=0x80000000; }','static void rate(void) { NRF_SPIM0->FREQUENCY=0x80000000; }\nstatic void slowrate(void) { NRF_SPIM0->FREQUENCY=0x10000000; }')
 full=full.replace('.setslowrate=rate','.setslowrate=slowrate')
 if chip=='52840':full=full.replace('NRF_SPIM0','NRF_SPIM3')
 (dst/'main.c').write_text(full)
 (dst/'build.py').write_text((old/'build.py').read_text().replace('uwb-broadcast-tree','uwb-min-gap'))
 print(dst)
