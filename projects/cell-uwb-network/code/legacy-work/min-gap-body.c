#include "dw3000_deca_regs.h"
#include "dw3000_deca_vals.h"
#include <string.h>
/* 32-bit test payload + hardware CRC16, no MAC header. Four-board timing test. */
volatile struct {uint32_t command,run,target,preamble,fast,gap_us,rank,leaves,batch,max_retries,reply_wait_us;} control;
volatile struct {uint32_t state,devid,unique,first_unique,missing,tx_frames,rx_frames,invalid,phy_errors,overruns,late_tx,retries,elapsed_us,first_pass_us,batches,duplicates,dt_min_ns,dt_max_ns,dt_count,node_count[3];} stats;
uint8_t received[1250];
volatile uint32_t profile[16];
uint32_t batch_time_us[34],batch_missing[34];
static uint64_t air_dtu,slot_dtu,last_rx;
static uint32_t expected_base;
static unsigned host_buffer;
static dwt_config_t config={5,DWT_PLEN_32,DWT_PAC8,9,9,1,DWT_BR_6M8,DWT_PHRMODE_STD,DWT_PHRRATE_DTA,33,DWT_STS_MODE_OFF,DWT_STS_LEN_64,DWT_PDOA_M0};
static uint64_t stamp(int tx){uint8_t b[5];uint64_t v=0;if(tx)dwt_readtxtimestamp(b);else dwt_readrxtimestamp(b,DWT_IP_M);for(unsigned i=0;i<5;i++)v|=(uint64_t)b[i]<<(8*i);return v;}
static int64_t diff(uint64_t a,uint64_t b){uint64_t d=(a-b)&0xffffffffffULL;return d&(1ULL<<39)?(int64_t)d-(1LL<<40):(int64_t)d;}
static void off(void){dwt_forcetrxoff();dwt_writesysstatuslo(DWT_INT_TXFRS_BIT_MASK|DWT_INT_RXFCG_BIT_MASK|SYS_STATUS_ALL_RX_ERR|SYS_STATUS_ALL_RX_TO);}
static uint32_t value(uint32_t id){return id*2654435761u^control.run;}
static void record_data(const uint8_t *b,uint64_t ts){
 uint32_t v=(uint32_t)b[0]|((uint32_t)b[1]<<8)|((uint32_t)b[2]<<16)|((uint32_t)b[3]<<24);
 uint32_t id=(v^control.run)*244002641u;
 stats.rx_frames++;
 if(id>=control.target){stats.invalid++;return;}
 if(ts&&last_rx){int64_t d=diff(ts,last_rx);if(d>0&&d<63897600000LL){uint32_t ns=d*10000/638976;
  if(!stats.dt_count||ns<stats.dt_min_ns)stats.dt_min_ns=ns;
  if(ns>stats.dt_max_ns)stats.dt_max_ns=ns;stats.dt_count++;
 }}last_rx=ts;
 if(received[id/8]&(1u<<(id%8)))stats.duplicates++;
 else {received[id/8]|=1u<<(id%8);stats.unique++;stats.node_count[id%control.leaves]++;}
}
static void rx_ok(const dwt_cb_data_t *cb){
 dwt_rxenable(DWT_START_RX_IMMEDIATE);
 if(cb->datalength!=6){stats.invalid++;return;}
 uint8_t b[4];dwt_readrxdata(b,4,0);record_data(b,stamp(0));
}
static void rx_err(const dwt_cb_data_t *cb){stats.phy_errors++;if(cb->status&DWT_INT_RXOVRR_BIT_MASK)stats.overruns++;dwt_rxenable(DWT_START_RX_IMMEDIATE);}
static dwt_callbacks_s callbacks={.cbRxOk=rx_ok,.cbRxErr=rx_err};
static void center_listen(void){
 off();dwt_setdblrxbuffmode(DBL_BUF_STATE_EN,DBL_BUF_MODE_MAN);host_buffer=0;last_rx=0;dwt_setcallbacks(&callbacks);
 dwt_setinterrupt(DWT_INT_RXFCG_BIT_MASK|SYS_STATUS_ALL_RX_ERR,0,DWT_ENABLE_INT_ONLY);
 dwt_writesysstatuslo(DWT_INT_RCINIT_BIT_MASK|DWT_INT_SPIRDY_BIT_MASK);
 dwt_rxenable(DWT_START_RX_IMMEDIATE);
}
static void leaf_listen(void){off();dwt_setrxtimeout(0);dwt_rxenable(DWT_START_RX_IMMEDIATE);}
static int setup(void){
 NRF_SPIM0->FREQUENCY=0x10000000;
 if(NRF_FICR->DEVICEID[0]!=0x06E5F278u){output(RESET,0);deca_sleep(2);GPIO->PIN_CNF[RESET]=0;}deca_sleep(10);
 if(dwt_probe((struct dwt_probe_s*)&probe))return -1;stats.devid=dwt_readdevid();if(stats.devid!=0xdeca0302)return -2;
 if(NRF_FICR->DEVICEID[0]==0x06E5F278u){dwt_softreset(0);deca_sleep(10);}
 uint32_t t=ticks();while(!dwt_checkidlerc())if(ticks()-t>100000)return -3;
 config.txPreambLength=control.preamble;config.sfdTO=control.preamble+1;config.phrRate=control.fast?DWT_PHRRATE_DTA:DWT_PHRRATE_STD;
 if(dwt_initialise(DWT_READ_OTP_ALL)||dwt_configure(&config))return -4;
 dwt_txconfig_t power={0x34,0xfdfdfdfd,0};dwt_configuretxrf(&power);dwt_configureframefilter(DWT_FF_DISABLE,0);
 dwt_setdblrxbuffmode(DBL_BUF_STATE_DIS,DBL_BUF_MODE_MAN);dwt_configciadiag(DW_CIA_DIAG_LOG_MIN);
 uint64_t ns100=(uint64_t)(control.preamble+8)*101763+21ULL*(control.fast?12821:102564)+96ULL*12821;
 air_dtu=ns100*638976/1000000;slot_dtu=air_dtu+(uint64_t)control.gap_us*638976/10;
 NRF_SPIM0->FREQUENCY=0x80000000;profile[0]=NRF_SPIM0->FREQUENCY;return 0;
}
static int send(uint32_t v,uint64_t when){
 uint32_t prep=ticks();
 uint8_t b[4];for(unsigned i=0;i<4;i++)b[i]=v>>(8*i);
 off();dwt_writetxdata(4,b,0);dwt_writetxfctrl(6,0,0);
 if(when)dwt_setdelayedtrxtime((uint32_t)(when>>8));
 profile[1]=ticks()-prep;if(profile[1]>profile[2])profile[2]=profile[1];
 if(dwt_starttx(when?DWT_START_TX_DELAYED:DWT_START_TX_IMMEDIATE)){stats.late_tx++;return 0;}
 uint32_t t=ticks();while(!(dwt_readsysstatuslo()&DWT_INT_TXFRS_BIT_MASK))if(ticks()-t>10000||control.command==3)return 0;
 dwt_writesysstatuslo(DWT_INT_TXFRS_BIT_MASK);stats.tx_frames++;return 1;
}
static void leaf(void){
 uint32_t s=dwt_readsysstatuslo();
 if(s&DWT_INT_RXFCG_BIT_MASK){
  uint8_t b[4];unsigned n=dwt_getframelength(0);if(n!=6){stats.invalid++;leaf_listen();return;}
  dwt_readrxdata(b,4,0);uint64_t ts=stamp(0);
  uint32_t v=(uint32_t)b[0]|((uint32_t)b[1]<<8)|((uint32_t)b[2]<<16)|((uint32_t)b[3]<<24);v^=control.run;
  if(v&0x80000000u){uint32_t id=v&0x7fffffffu;
   if(id<control.target&&id%control.leaves==control.rank){uint64_t when=(ts+air_dtu+(uint64_t)control.reply_wait_us*638976/10-dwt_gettxantennadelay())&0xffffffffffULL;send(value(id),when);}
  }else if(v>=expected_base&&v<control.target&&v%control.batch==0){
   unsigned count=control.target-v;if(count>control.batch)count=control.batch;
   for(unsigned k=0;k<count;k++)if((v+k)%control.leaves==control.rank){
    uint64_t when=(ts+63897600ULL+(uint64_t)k*slot_dtu-dwt_gettxantennadelay())&0xffffffffffULL;
    send(value(v+k),when);
   }expected_base=v+count;
  }else stats.invalid++;
  leaf_listen();
 }else if(s&(SYS_STATUS_ALL_RX_ERR|SYS_STATUS_ALL_RX_TO)){stats.phy_errors++;leaf_listen();}
}
static void pump(uint32_t duration){
 uint32_t begin=ticks();unsigned idle=0;
 while(ticks()-begin<duration&&control.command!=3){
  uint8_t h[2]={0x42,0x90},db;rd(2,h,1,&db);
  if(db&(host_buffer?0x10:1)){
   uint32_t t=ticks();dwt_rxenable(DWT_START_RX_IMMEDIATE);
   uint8_t b[4];dwt_readrxdata(b,4,0);
   /* Capture consecutive timestamps near each batch start; skip diagnostics
      in the steady-state throughput path. CRC-good status is always checked. */
   uint64_t ts=stats.rx_frames%control.batch<24?stamp(0):0;
   uint8_t clear=host_buffer?0xf0:0x0f;h[0]=0xc2;wr(2,h,1,&clear);
   dwt_signal_rx_buff_free();host_buffer^=1;
   record_data(b,ts);uint32_t cost=ticks()-t;profile[3]=cost;if(cost>profile[4])profile[4]=cost;
  }else if((++idle&15u)==0){
   uint32_t status=dwt_readsysstatuslo();
   if(status&SYS_STATUS_ALL_RX_ERR){stats.phy_errors++;if(status&DWT_INT_RXOVRR_BIT_MASK)stats.overruns++;dwt_writesysstatuslo(SYS_STATUS_ALL_RX_ERR);dwt_rxenable(DWT_START_RX_IMMEDIATE);}
  }
 }
}
static void root_run(void){
 uint32_t begin=ticks();last_rx=0;
 for(uint32_t base=0;base<control.target&&control.command!=3;base+=control.batch){
  uint32_t batch_begin=ticks(),before=stats.unique;
  uint32_t count=control.target-base;if(count>control.batch)count=control.batch;
  dwt_setinterrupt(0xffffffffu,0xffffffffu,DWT_DISABLE_INT);off();dwt_setdblrxbuffmode(DBL_BUF_STATE_DIS,DBL_BUF_MODE_MAN);
  send(base^control.run,0);center_listen();
  pump(1000+(uint64_t)count*slot_dtu*10/638976+500);
  uint32_t first=stats.unique-before;stats.first_unique+=first;stats.first_pass_us+=ticks()-batch_begin;
  for(uint32_t id=base;id<base+count&&control.command!=3;id++)if(!(received[id/8]&(1u<<(id%8)))){
  for(unsigned k=0;k<control.max_retries&&!(received[id/8]&(1u<<(id%8)));k++){
   dwt_setinterrupt(0xffffffffu,0xffffffffu,DWT_DISABLE_INT);off();dwt_setdblrxbuffmode(DBL_BUF_STATE_DIS,DBL_BUF_MODE_MAN);
   stats.retries++;send((id|0x80000000u)^control.run,0);center_listen();pump(control.reply_wait_us+500);
  }}
  if(stats.batches<34){batch_time_us[stats.batches]=ticks()-batch_begin;batch_missing[stats.batches]=count-first;}
  stats.batches++;
 }
 stats.elapsed_us=ticks()-begin;stats.missing=control.target-stats.unique;off();stats.state=3;
}
int main(void){
/* PLATFORM_INIT */
 while(1){
  if(control.command){unsigned cmd=control.command;control.command=0;
   if(cmd==3){if(stats.devid==0xdeca0302)off();stats.state=5;continue;}
   memset((void*)&stats,0,sizeof(stats));memset((void*)profile,0,sizeof(profile));memset(received,0,sizeof(received));expected_base=0;
   if((cmd!=1&&cmd!=2)||!control.target||control.target>10000||!control.batch||!control.leaves||control.leaves>3){stats.state=90;continue;}
   int e=setup();if(e){stats.state=100-e;continue;}stats.state=cmd;
   if(cmd==2)root_run();else leaf_listen();
  }
  if(stats.state==1)leaf();
 }
}
