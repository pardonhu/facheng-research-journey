from pathlib import Path
p=Path('work/toolnail-UWB/DW3_QM33_SDK_1.1.1/Drivers/API/Build_Platforms');src=p/'nRF52832-P2P';dst=p/'nRF52832-Broadcast';dst.mkdir(exist_ok=True)
s=(src/'main.c').read_text().replace('interval,length,channel;','interval,length,channel,destination,pan,node;').replace('len<16','len<24')
s=s.replace('dwt_configuretxrf(&power);','dwt_configuretxrf(&power); dwt_setpanid(control.pan); dwt_setaddress16(control.node); dwt_configureframefilter(DWT_FF_ENABLE_802_15_4,DWT_FF_DATA_EN);')
s=s.replace('frame[0]=0xC5; memcpy(frame+1,(const void*)&stats.run,4); memcpy(frame+5,&seq,4); for(unsigned i=9;i<len;i++)', 'frame[0]=0x41; frame[1]=0x88; frame[2]=(uint8_t)seq; frame[3]=control.pan; frame[4]=control.pan>>8; frame[5]=control.destination; frame[6]=control.destination>>8; frame[7]=control.node; frame[8]=control.node>>8; memcpy(frame+9,(const void*)&stats.run,4); memcpy(frame+13,&seq,4); for(unsigned i=17;i<len;i++)')
s=s.replace('memcpy(&run,frame+1,4); memcpy(&seq,frame+5,4); good=frame[0]==0xC5&&run==stats.run&&seq<target; for(unsigned i=9;', 'memcpy(&run,frame+9,4); memcpy(&seq,frame+13,4); good=frame[0]==0x41&&frame[1]==0x88&&run==stats.run&&seq<target; for(unsigned i=17;')
(dst/'main.c').write_text(s);(dst/'build.py').write_text((src/'build.py').read_text().replace('uwb-p2p','uwb-broadcast'))
