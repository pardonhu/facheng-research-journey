from pathlib import Path
s=Path('work/run-capacity.py').read_text()
s=s[:s.index('def execute():')]
s=s.replace('capacity-study','preamble-study').replace('nRF52832-Capacity','nRF52832-Preamble').replace('uwb-capacity','uwb-preamble').replace('STOP-CAPACITY','STOP-PREAMBLE').replace('capacity-{sn}', 'preamble-{sn}')
s=s.replace("fields='state", "profile={'preamble':128,'payload':4}\nfields='state")
s=s.replace('rounds,role,mode,batch]', "rounds,role,mode,batch,profile['preamble'],profile['payload']]")
s=s.replace('status=dict(name=name,', "status=dict(preamble=profile['preamble'],payload=profile['payload'],name=name,")
s=s.replace('row=dict(name=name,', "row=dict(preamble=profile['preamble'],payload=profile['payload'],data_frame_bytes=27+profile['payload'],name=name,")
s=s.replace('total_ticks=tm[3]', "assert sum(hist)==tm[0],'timestamp histogram mismatch'\n if mode==0:assert tm[0]==n-1,'timestamp sample count mismatch'\n total_ticks=tm[3]")
Path('work/preamble_io.py').write_text(s)
