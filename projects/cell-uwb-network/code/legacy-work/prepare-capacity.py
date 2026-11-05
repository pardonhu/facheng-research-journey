from pathlib import Path
p=Path('work/toolnail-UWB/DW3_QM33_SDK_1.1.1/Drivers/API/Build_Platforms')
dst=p/'nRF52832-Capacity';dst.mkdir(exist_ok=True)
s=(p/'nRF52832-Reliable/main.c').read_text()
s=s.replace('rounds,command_role;', 'rounds,command_role,mode,batch;')
s=s.replace('static uint8_t received[12500]', 'uint8_t received[12500]')
s=s.replace('static uint32_t start_time;', '''
volatile struct { uint32_t samples, min_ticks, max_ticks, sum_lo, sum_hi, batches; } timing;
uint32_t interval_hist[2048], batch_us[500], batch_missing[500];
static uint32_t previous_ts, previous_seq, batch_end;
static int have_ts;
static uint64_t sum_ticks;
static void measure_tx(void) {
 if(txbuf[12]!=RELIABLE_P2P_MSG_DATA) { have_ts=0; return; }
 uint32_t seq=reliable_p2p_get_u32(txbuf,17), ts=dwt_readtxtimestamplo32();
 if(have_ts && seq==previous_seq+1) {
  uint32_t dt=ts-previous_ts; sum_ticks+=dt; timing.samples++;
  if(dt<timing.min_ticks) timing.min_ticks=dt;
  if(dt>timing.max_ticks) timing.max_ticks=dt;
  timing.sum_lo=(uint32_t)sum_ticks; timing.sum_hi=(uint32_t)(sum_ticks>>32);
  uint32_t us=(uint32_t)(((uint64_t)dt*10+319488)/638976);
  interval_hist[us<2047?us:2047]++;
 }
 previous_ts=ts; previous_seq=seq; have_ts=1;
}
static uint32_t start_time;''')
s=s.replace('uint32_t n=control.count-base;', 'uint32_t n=batch_end-base;')
s=s.replace('dwt_writesysstatuslo(DWT_INT_TXFRS_BIT_MASK); return 1;', 'dwt_writesysstatuslo(DWT_INT_TXFRS_BIT_MASK); measure_tx(); return 1;')
s=s.replace('field<control.count && field%32==0','field<control.count')
begin=s.index(' for(uint32_t base=0;base<control.count && control.command!=3;base+=32)')
end=s.index(' if(control.command==3) {stats.state=5;return;}',begin)
s=s[:begin]+''' for(uint32_t first=0;first<control.count && control.command!=3;first+=control.batch) {
  batch_end=first+control.batch; if(batch_end>control.count) batch_end=control.count;
  uint32_t bt=ticks(), missing_before=stats.ack_missing;
  if(control.mode==0) {
   for(uint32_t seq=first;seq<batch_end && control.command!=3;seq++) {
    prepare(RELIABLE_P2P_MSG_DATA,seq,0,0,0,0,0); reliable_p2p_fill_payload(txbuf,seq);
    if(transmit()) stats.attempts++;
    if(seq+1<batch_end) deca_usleep(control.interval);
   }
   stats.completed=batch_end;
  } else {
   for(uint32_t base=first;base<batch_end && control.command!=3;base+=32) {
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
   }
  }
  unsigned b=timing.batches;
  if(b<500) {batch_us[b]=ticks()-bt; batch_missing[b]=stats.ack_missing-missing_before; timing.batches=b+1;}
  stats.elapsed=ticks()-start_time;
  if(control.mode==0) deca_usleep(control.interval);
 }
''' + s[end:]
s=s.replace('active=finished=0; stats.run=', '''memset((void*)&timing,0,sizeof(timing)); timing.min_ticks=0xffffffffu;
   memset(interval_hist,0,sizeof(interval_hist)); memset(batch_us,0,sizeof(batch_us)); memset(batch_missing,0,sizeof(batch_missing));
   have_ts=0;sum_ticks=0;
   active=finished=0; stats.run=''')
s=s.replace('control.injection>2)', 'control.injection>2||control.mode>1||control.batch<200||control.batch>100000)')
# Use the external HF crystal for MCU timing, with bounded startup wait.
s=s.replace(' SEGGER_RTT_Init();', ''' NRF_CLOCK->EVENTS_HFCLKSTARTED=0; NRF_CLOCK->TASKS_HFCLKSTART=1;
 uint32_t clock_start=ticks(); while(!NRF_CLOCK->EVENTS_HFCLKSTARTED) {if(ticks()-clock_start>100000) {stats.state=110;while(1) {}}}
 SEGGER_RTT_Init();''')
(dst/'main.c').write_text(s)
(dst/'build.py').write_text((p/'nRF52832-Reliable/build.py').read_text().replace('uwb-reliable','uwb-capacity'))
