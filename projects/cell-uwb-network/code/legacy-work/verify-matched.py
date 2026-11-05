from pathlib import Path
import json,hashlib,subprocess
import runpy
io=runpy.run_path('work/run-matched.py');root=io['root'];out=io['out'];p=io['p']
assert json.loads((out/'status.json').read_text())['state']=='complete'
rows=[json.loads(x) for x in (out/'results.jsonl').read_text().splitlines() if json.loads(x)['formal']]
assert len(rows)==15 and len({r['name'] for r in rows})==15
expected=root/'work/matched-expected.bin'
subprocess.run([str(root/'work/arm-gcc/bin/arm-none-eabi-objcopy.exe'),'-O','binary',str(p/'uwb-matched.elf'),str(expected)],check=True)
checks=[]
for b in io['boards']:
    actual=out/f'{b}-tested-flash.bin';uicr=out/f'{b}-after-uicr.bin'
    io['command'](b,f'savebin {actual.as_posix()} 0 {expected.stat().st_size:#x}\nsavebin {uicr.as_posix()} 0x10001000 0x1000')
    assert actual.read_bytes()==expected.read_bytes(),b+' firmware mismatch'
    assert uicr.read_bytes()==(out/f'{b}-before-uicr.bin').read_bytes(),b+' UICR changed'
    checks.append(dict(board=b,serial=io['boards'][b],firmware_matches=True,uicr_unchanged=True))
for r in rows:
    assert r['count']==50000
    bits=(out/f"{r['name']}-received.bin").read_bytes()
    assert sum(b.bit_count() for b in bits)==r['boards']['A']['unique']
    assert sum(c['packets'] for c in r['cycles'])==50000
    assert sum(c['missing_packets'] for c in r['cycles'])==50000-r['boards']['A']['unique']
    assert sum(r['period_hist'])==r['boards'][r['controller']]['period_n']
    assert all(s['tx_errors']==0 for s in r['boards'].values())
rejected={r['name']:sum(s['invalid'] for s in r['boards'].values()) for r in rows}
(out/'post-test-verification.json').write_text(json.dumps(dict(formal_cases=15,original_packets=750000,bitmap_and_cycle_checks=True,rejected_frames_by_case=rejected,boards=checks),indent=2))
print('Verified 15 cases, bitmaps, cycles, firmware and UICR')
