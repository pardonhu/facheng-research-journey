from pathlib import Path
p=Path('work/report-four.py');s=p.read_text(encoding='utf8');needle="h('达到 300 节点预算需要什么')";a=s.index(needle);s=s[:a]+"p('此前双板实验采用连续发送和批量确认；本次采用节点点名与回复，并设置首个回复延迟 1000 μs。两组测量的通信流程不同。评估组网效率应使用本次完整采集时间，后续再分别压缩回复等待、控制帧数量和接收处理时间。')\n"+s[a:];p.write_text(s,encoding='utf8')
