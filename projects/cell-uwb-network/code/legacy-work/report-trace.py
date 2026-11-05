from pathlib import Path
p=Path('work/report-four.py');s=p.read_text(encoding='utf8').replace('第 100 至 119 轮','轮号 100 至 119');s=s.replace('工程基于同学的 toolnail/UWB 仓库，','工程基于同学的 toolnail/UWB 仓库（github.com/toolnail/UWB，原始提交 79209d263fc536fbffd4c5af5b2e4c4b610eeedb），');p.write_text(s,encoding='utf8')
