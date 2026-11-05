from pathlib import Path
p=Path('work/toolnail-UWB/DW3_QM33_SDK_1.1.1/Drivers/API/Build_Platforms')
dst=p/'nRF52832-Reliable'; dst.mkdir(exist_ok=True)
old=(p/'nRF52832-Broadcast/main.c').read_text()
prefix=old[:old.index('/* Host writes')]
setup=old[old.index('static dwt_config_t config='):old.index('int main(void)')]
setup=setup[:setup.index('static void logstats')]+setup[setup.index('static int setup'):]
setup=setup.replace('control.pan','0xDECA').replace('control.node','control.command_role==1?0x5258:0x5458')
init=old[old.index(' NRF_TIMER1->MODE='):old.index(' uint32_t start=0')]
body=Path('work/reliable-body.c').read_text()
decl, funcs=body.split('/* PLATFORM_SETUP */')
(dst/'main.c').write_text(prefix+decl+setup+funcs.replace('/* PLATFORM_INIT */',init))
build=(p/'nRF52832-Broadcast/build.py').read_text().replace('uwb-broadcast','uwb-reliable')
build=build.replace("incs=[mdk,", "incs=[p.parents[1]/'Src/examples/ex_08_reliable_p2p',mdk,")
build=build.replace("'-Os','-g3'", "'-Wall','-Wextra','-Os','-g3'")
(dst/'build.py').write_text(build)
