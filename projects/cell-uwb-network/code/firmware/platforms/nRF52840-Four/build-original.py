from pathlib import Path
import subprocess
p=Path(__file__).resolve().parent
root=p.parent/'nRF52840-DK'; sdk=root/'sdk'; mdk=sdk/'modules/nrfx/mdk'; driver=p.parents[1]/'Shared/dwt_uwb_driver'
workspace=next(x for x in p.parents if (x/'work/arm-gcc').exists())
bin=workspace/'work/arm-gcc/bin'; gcc=str(bin/'arm-none-eabi-gcc.exe')
build=p/'build'; build.mkdir(exist_ok=True)
(p/'memory.ld').write_text('MEMORY { FLASH (rx) : ORIGIN = 0, LENGTH = 1024K\n RAM (rwx) : ORIGIN = 0x20000000, LENGTH = 256K }\nINCLUDE "nrf52_common.ld"\n')
incs=[p.parents[1]/'Src/examples/ex_08_reliable_p2p',mdk,sdk/'components/toolchain/cmsis/include',root/'SEGGER',driver,driver/'dw3000',driver/'lib/qmath/include',driver/'lib/qmath/src']
flags=['-mcpu=cortex-m4','-mthumb','-mfloat-abi=hard','-mfpu=fpv4-sp-d16','-DNRF52840_XXAA','-DBOARD_PCA10056','-DCONFIG_NRF_APPROTECT_DISABLE','-DDEBUG','-D__HEAP_SIZE=8192','-D__STACK_SIZE=8192','-Wall','-Wextra','-Os','-g3','-ffunction-sections','-fdata-sections','-fno-strict-aliasing']
for i in incs: flags+=['-I'+str(i)]
sources=[p/'main.c',mdk/'gcc_startup_nrf52840.S',mdk/'system_nrf52840.c',root/'SEGGER/SEGGER_RTT.c',driver/'deca_interface.c',driver/'deca_compat.c',driver/'deca_rsl.c',driver/'dw3000/dw3000_device.c']+list((driver/'lib/qmath/src').glob('*.c'))
objs=[]
for i,s in enumerate(sources):
 o=build/(str(i)+'.o'); subprocess.run([gcc,*flags,'-c',str(s),'-o',str(o)],check=True); objs.append(str(o))
elf=build/'uwb-four.elf'
subprocess.run([gcc,*flags,*objs,'-L'+str(mdk),'-T'+str(p/'memory.ld'),'-Wl,--gc-sections','-Wl,-Map='+str(build/'uwb-four.map'),'--specs=nano.specs','--specs=nosys.specs','-lm','-o',str(elf)],check=True)
subprocess.run([str(bin/'arm-none-eabi-objcopy.exe'),'-O','ihex',str(elf),str(build/'uwb-four.hex')],check=True)
subprocess.run([str(bin/'arm-none-eabi-size.exe'),str(elf)],check=True)


