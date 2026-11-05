from broadcast_tree_io import *
rows=[json.loads(x) for x in (out/'results.jsonl').read_text().splitlines() if json.loads(x)['formal']]
assert len(rows)==4 and len({r['name'] for r in rows})==4
checks=[]
for b in boards:
 expected=root/f"work/bt-{b['label']}-expected.bin"
 subprocess.run([str(root/'work/arm-gcc/bin/arm-none-eabi-objcopy.exe'),'-O','binary',str(b['build']/'uwb-broadcast-tree.elf'),str(expected)],check=True)
 actual=out/f"{b['label']}-tested-flash.bin";uicr=out/f"{b['label']}-after-uicr.bin"
 command(b,f"savebin {actual.as_posix()} 0 {expected.stat().st_size:#x}\nsavebin {uicr.as_posix()} 0x10001000 0x1000")
 assert actual.read_bytes()==expected.read_bytes()
 assert uicr.read_bytes()==(out/f"{b['label']}-before-uicr.bin").read_bytes()
 checks.append(dict(board=b['label'],serial=b['serial'],firmware_matches=True,uicr_unchanged=True))
for r in rows:
 a=r['boards']['A'];bits=(out/f"{r['name']}-received.bin").read_bytes()
 assert r['target']==50000 and a['rounds']==25000
 assert sum(v.bit_count() for v in bits)==a['unique'] and a['unique']+a['missing']==50000
 assert sum(r['round_hist_25us'])==25000
 assert len(r['windows']['200'])==250 and len(r['windows']['300'])==166
 assert sum(x['us'] for x in r['windows']['200'])==a['elapsed']
 assert sum(x['missing'] for x in r['windows']['200'])==a['missing']
 assert all(b['devid']==0xdeca0302 for b in r['boards'].values())
 if r['mode']==4:
  g=r['group_counts']['B'];p=r['sync']['B']
  assert g[0]==25000 and g[1]==50000 and g[2]+g[3]==50000
  assert p[1]['count']+p[2]['count']==g[2] and p[0]['count']==g[5]
 if r['drop_every_D']:assert r['group_counts']['D'][4]==2500 and r['boards']['B']['retries']>=2500
(out/'verification.json').write_text(json.dumps(dict(cases=len(rows),records=sum(r['target'] for r in rows),accounting_consistent=True,boards=checks),indent=2))
print('Verified 200000 leaf records, timing accounting, firmware and unchanged UICR')
