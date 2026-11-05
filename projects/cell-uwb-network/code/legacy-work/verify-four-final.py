from four_io import *
import hashlib
backup={r['board']:r for r in json.loads((out/'backup-manifest.json').read_text())};verified=[]
for b in boards:
 expected=root/f"work/four-{b['label']}-expected.bin"
 subprocess.run([str(root/'work/arm-gcc/bin/arm-none-eabi-objcopy.exe'),'-O','binary',str(b['build']/'uwb-four.elf'),str(expected)],check=True)
 actual=out/f"{b['label']}-tested-flash.bin";uicr=out/f"{b['label']}-after-fourboard-uicr.bin"
 command(b,f"savebin {actual.as_posix()} 0 {expected.stat().st_size:#x}\nsavebin {uicr.as_posix()} 0x10001000 0x1000")
 assert actual.read_bytes()==expected.read_bytes(),b['label']+' flash changed'
 same=hashlib.sha256(uicr.read_bytes()).hexdigest()==backup[b['label']]['uicr_sha256'];assert same,b['label']+' UICR changed'
 verified.append(dict(board=b['label'],firmware_matches=True,uicr_matches_backup=same,reset_pin_configuration_restored_after_test=(b["label"]=="D")))
(out/'post-test-verification.json').write_text(json.dumps(verified,indent=2));print(verified)
