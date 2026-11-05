from pathlib import Path
p=Path('work/analyze-four.py');s=p.read_text();s+='''
lines=['四节点 UWB 组网实验实时汇总',f'正式完成 {len(formal)}/10 组；每组 100000 条四字节原始数据。','', '配置 | 最终收到 | 首次到达率 | 平均一轮 ms | 整轮收齐率']
for r in summary:lines.append(f"{r['name']} | {r['received']}/{r['records']} | {r['first_pdr']*100:.3f}% | {r['round_mean_ms']:.3f} | {r['round_all']*100:.3f}%")
lines+=['','逐个点名与分时回复每轮三个节点；两跳组及其直连对照每轮两个叶节点。','尚未完成的配置不纳入结果。节点数量推算见 formal-summary.json，其中200与300节点为串行耗时估算。']
(p/'四板实验实时汇总.txt').write_text('\\n'.join(lines),encoding='utf-8-sig')
''';p.write_text(s,encoding='utf8')
