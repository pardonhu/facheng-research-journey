from pathlib import Path
p=Path('work/plot-four.py');s=p.read_text(encoding='utf8');s=s.replace("sys.path.insert(0,str(Path('work/plot-libs').resolve()))\n",'');p.write_text(s,encoding='utf8')
