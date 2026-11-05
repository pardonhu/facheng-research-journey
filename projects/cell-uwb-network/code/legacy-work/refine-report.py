from pathlib import Path
p=Path('work/report-four.py');s=p.read_text();s=s.replace("['调度','中心控制重试；星形每条数据最多尝试 5 次；轮末广播确认']", "['帧长度','控制帧 30 B；单条 DATA 34 B；两条聚合帧 38 B，均含 FCS'],['调度','首个回复延迟 1000 μs；星形最多尝试 5 次；轮末广播确认']");p.write_text(s)
