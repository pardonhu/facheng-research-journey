from pathlib import Path
s=Path('work/four_io.py').read_text().replace('four-board-study','tree-end-to-end-study').replace('-Four/','-Tree/').replace('uwb-four','uwb-tree').replace('work/four-','work/tree-').replace('STOP-FOUR','STOP-TREE').replace('range(2):','range(4):')
s=s.replace('attempts,quiet=None):','attempts,quiet=None,pre=64):').replace('mask,qfrom,qlen]','mask,qfrom,qlen,pre]')
s=s.replace('quiet=None,formal=True):','quiet=None,formal=True,pre=64):').replace('turn,attempts,quiet)','turn,attempts,quiet,pre)').replace('turn,attempts)\n status','turn,attempts,pre=pre)\n status')
s=s.replace('name=name,mode=mode,count=n','name=name,mode=mode,preamble=pre,count=n').replace('name=name,mode=mode,target=n','name=name,mode=mode,preamble=pre,target=n')
point=" with (out/'results.jsonl').open('a') as f:f.write(json.dumps(row)+'\\n')"
assert point in s
extra=''' row['phase']={b['label']:dict(zip(('collection_us','uplink_us','leaf_poll_calls','uplink_calls','windows200','windows300'),struct.unpack('<6I',rawread(b,'phase',24)))) for b in boards}
 row['windows']={}
 for size in (200,300):
  count=row['phase']['A'][f'windows{size}']
  if count:
   us=list(struct.unpack('<'+'I'*count,rawread(boards[0],f'window{size}_us',count*4)))
   missing=list(struct.unpack('<'+'I'*count,rawread(boards[0],f'window{size}_missing',count*4)))
   row['windows'][str(size)]=[dict(us=t,missing=m) for t,m in zip(us,missing)]
  else:row['windows'][str(size)]=[]
'''
s=s.replace(point,extra+point)
Path('work/tree_io.py').write_text(s)
print('Tree host prepared')
