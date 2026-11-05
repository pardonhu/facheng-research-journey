from pathlib import Path
p=Path('work/report-four.py');s=p.read_text(encoding='utf8');needle="p('本次每轮只有三个回复节点。";a=s.index(needle);s=s[:a]+'''r386=lookup['group-3-guard250'];b386=r386['boards']['A']
p(f'386 μs 间隔下，B、C、D 首次收到的条数分别为 {b386["node_first_2"]:,}、{b386["node_first_3"]:,}、{b386["node_first_4"]:,}。结合较长间隔的结果，可判断当前连续接收时序已影响可靠性。进一步应记录接收完成、读取帧和重新开启接收三个时刻，定位需要压缩的处理步骤。')
'''+s[a:];p.write_text(s,encoding='utf8')
