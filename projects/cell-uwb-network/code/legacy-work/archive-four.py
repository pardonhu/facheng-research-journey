from pathlib import Path
import json,hashlib,zipfile
root=Path.cwd();out=root/'outputs/four-board-study';base=root/'work/toolnail-UWB/DW3_QM33_SDK_1.1.1/Drivers/API/Build_Platforms'
files=[root/'work'/n for n in ('four-body.c','prepare-four.py','four_io.py','run-four.py')]
for chip in ('52832','52840'):
 p=base/f'nRF{chip}-Four';files.extend(p/n for n in ('main.c','build.py','memory.ld','build/uwb-four.hex','build/uwb-four.elf'))
with zipfile.ZipFile(out/'tested-source-and-firmware.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in files:z.write(p,str(p.relative_to(root)))
meta=dict(payload_bytes=4,preamble_symbols=64,channel=5,rate_mbps=6.8,per_case_application_records=100000,turn_us=1000,root_ack_postwait_us=500,attempt_limit=5,round_histogram_bin_us=25,slot_spacing_us=[1136,636,386,236,186,136],boards={'A':'JLINK_A nRF52832','B':'JLINK_B nRF52832','C':'JLINK_C nRF52840','D':'JLINK_D nRF52840'},D_reset_workaround='Software reset selected by FICR DEVICEID[0]=06E5F278 because driving P1.08 low rebooted MCU. Physical wiring cause remains unverified.',files={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
(out/'experiment-manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf8')
print('source archive and manifest saved')
