from pathlib import Path
p=Path('work/toolnail-UWB/DW3_QM33_SDK_1.1.1/Drivers/API/Build_Platforms')
dst=p/'nRF52832-Preamble';dst.mkdir(exist_ok=True)
s=(p/'nRF52832-Capacity/main.c').read_text()
s=s.replace('command_role,mode,batch;', 'command_role,mode,batch,preamble,payload;')
s=s.replace('static uint32_t previous_ts, previous_seq, batch_end;', '''static uint32_t previous_ts, previous_seq, batch_end;
/* Only DATA shrinks. Control packets retain the original 59-byte RP v1 format. */
static unsigned data_frame_length(void) { return 25+control.payload+2; }
static void fill_data(uint8_t *frame,uint32_t seq) {
 for(unsigned i=0;i<control.payload;i++) frame[25+i]=(uint8_t)(seq+i*37+0x5a);
}
static int valid_data(const uint8_t *frame,uint32_t seq) {
 for(unsigned i=0;i<control.payload;i++) if(frame[25+i]!=(uint8_t)(seq+i*37+0x5a)) return 0;
 return 1;
}
static int valid_frame(const uint8_t *frame,unsigned n) {
 if(n<27 || frame[9]!='R' || frame[10]!='P' || frame[11]!=1) return 0;
 return n==(frame[12]==RELIABLE_P2P_MSG_DATA?data_frame_length():59);
}''')
s=s.replace('config.chan=control.channel==9?9:5;', '''config.chan=control.channel==9?9:5;
 config.txPreambLength=control.preamble;
 config.rxPAC=DWT_PAC8;
 config.sfdTO=control.preamble+1+8-8;''')
s=s.replace('clear_radio(); dwt_writetxdata(57,txbuf,0); dwt_writetxfctrl(59,0,0);', '''unsigned length=txbuf[12]==RELIABLE_P2P_MSG_DATA?data_frame_length():59;
 clear_radio(); dwt_writetxdata(length-2,txbuf,0); dwt_writetxfctrl(length,0,0);''')
s=s.replace('if(n==59) dwt_readrxdata(rxbuf,59,0);','if(n>=27 && n<=59) dwt_readrxdata(rxbuf,n,0);')
s=s.replace('n!=59 || !reliable_p2p_frame_is_valid(rxbuf,n)', 'n>59 || !valid_frame(rxbuf,n)')
s=s.replace('reliable_p2p_fill_payload(', 'fill_data(').replace('reliable_p2p_payload_is_valid(', 'valid_data(')
s=s.replace('control.batch>100000)', 'control.batch>100000||(control.preamble!=128&&control.preamble!=64&&control.preamble!=32)||(control.payload!=4&&control.payload!=32))')
(dst/'main.c').write_text(s)
(dst/'build.py').write_text((p/'nRF52832-Capacity/build.py').read_text().replace('uwb-capacity','uwb-preamble'))
