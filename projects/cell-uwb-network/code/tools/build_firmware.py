"""Build archived MinGap applications; does not access hardware."""
from pathlib import Path
import argparse,subprocess,os
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--vendor',type=Path,required=True,help='toolnail/UWB checkout')
 p.add_argument('--toolchain',type=Path,required=True,help='directory containing arm-none-eabi-gcc')
 p.add_argument('--chip',choices=['52832','52840'],required=True)
 p.add_argument('--nordic-sdk',type=Path)
 p.add_argument('--output',type=Path)
 a=p.parse_args();project=Path(__file__).resolve().parents[2]
 api=a.vendor.resolve()/'DW3_QM33_SDK_1.1.1/Drivers/API'
 platform=project/f'code/firmware/platforms/nRF{a.chip}-MinGap'
 sdk=(a.nordic_sdk or api/'Build_Platforms/nRF52840-DK/sdk').resolve();mdk=sdk/'modules/nrfx/mdk'
 driver=api/'Shared/dwt_uwb_driver';rtt=api/'Build_Platforms/nRF52840-DK/SEGGER'
 output=(a.output or platform/'build').resolve();output.mkdir(parents=True,exist_ok=True)
 def tool(name):
  stem=a.toolchain.resolve()/('arm-none-eabi-'+name)
  for f in [stem.with_suffix('.exe'),stem]:
   if f.is_file():return str(f)
  raise FileNotFoundError(stem)
 gcc=tool('gcc');flags=['-mcpu=cortex-m4','-mthumb','-mfloat-abi=hard','-mfpu=fpv4-sp-d16',f'-DNRF{a.chip}_XXAA','-DBOARD_PCA10040' if a.chip=='52832' else '-DBOARD_PCA10056','-DDEBUG','-D__HEAP_SIZE=8192','-D__STACK_SIZE=8192','-Wall','-Wextra','-Os','-g3','-ffunction-sections','-fdata-sections','-fno-strict-aliasing']
 if a.chip=='52840':flags+=['-DCONFIG_NRF_APPROTECT_DISABLE']
 for inc in [mdk,sdk/'components/toolchain/cmsis/include',rtt,driver,driver/'dw3000',driver/'lib/qmath/include',driver/'lib/qmath/src']:
  if not inc.is_dir():raise FileNotFoundError(inc)
  flags+=['-I'+str(inc)]
 suffix='nrf52' if a.chip=='52832' else 'nrf52840'
 sources=[platform/'main.c',mdk/f'gcc_startup_{suffix}.S',mdk/f'system_{suffix}.c',rtt/'SEGGER_RTT.c',driver/'deca_interface.c',driver/'deca_compat.c',driver/'deca_rsl.c',driver/'dw3000/dw3000_device.c']+list((driver/'lib/qmath/src').glob('*.c'))
 flash,ram=('512K','64K') if a.chip=='52832' else ('1024K','256K')
 ld=output/'memory.ld';ld.write_text(f'MEMORY {{ FLASH (rx) : ORIGIN = 0, LENGTH = {flash}\n RAM (rwx) : ORIGIN = 0x20000000, LENGTH = {ram} }}\nINCLUDE "nrf52_common.ld"\n')
 objects=[]
 for i,src in enumerate(sources):
  if not src.is_file():raise FileNotFoundError(src)
  obj=output/f'{i}.o';subprocess.run([gcc,*flags,'-c',str(src),'-o',str(obj)],check=True);objects.append(str(obj))
 elf=output/'uwb-min-gap.elf'
 subprocess.run([gcc,*flags,*objects,'-L'+str(mdk),'-T'+str(ld),'-Wl,--gc-sections','-Wl,-Map='+str(output/'uwb-min-gap.map'),'--specs=nano.specs','--specs=nosys.specs','-lm','-o',str(elf)],check=True)
 subprocess.run([tool('objcopy'),'-O','ihex',str(elf),str(output/'uwb-min-gap.hex')],check=True)
 subprocess.run([tool('size'),str(elf)],check=True)
if __name__=='__main__':main()
