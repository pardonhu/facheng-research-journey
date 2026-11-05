from pathlib import Path
p=Path('work/report-four.py');s=p.read_text(encoding='utf8');needle="p('本次每轮只有三个回复节点。";a=s.index(needle);s=s[:a]+'''p(f'实际全网发射总帧数从逐个点名的 {sum(b["tx_frames"] for b in ind["boards"].values()):,} 帧，变为所选分时配置的 {sum(b["tx_frames"] for b in best["boards"].values()):,} 帧。两组业务量同为 10 万条，这个差值包含点名减少和重传变化的共同效果。')
'''+s[a:];p.write_text(s,encoding='utf8')
