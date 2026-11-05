from pathlib import Path
import json, math
p=Path('outputs/four-board-study')
rows=[json.loads(x) for x in (p/'results.jsonl').read_text().splitlines()]
formal=[x for x in rows if x['formal']]
for x in formal:
 a=x['boards']['A'];assert a['unique']+a['missing']==x['target'];assert sum(x['round_hist_25us'])==a['hist_rounds']
 assert sum(a[f'node_unique_{i}'] for i in (2,3,4))==a['unique']
summary=[]
for x in formal:
 a=x['boards']['A'];unit=a['elapsed']/x['target'];n=x['mask'].bit_count()
 summary.append(dict(name=x['name'],records=x['target'],received=a['unique'],missing=a['missing'],first_pdr=x['first_pdr'],final_pdr=x['pdr'],round_mean_ms=x['round_mean_us']/1000,round_p99=x['round_p99'],round_all=x['all_round_rate'],slot_us=136+x['guard_us'],us_per_record=unit,serial_200_ms=200*unit/1000,serial_300_ms=300*unit/1000,records_in_100ms=math.floor(100000/(unit*n))*n,mean_rate_records_in_100ms=math.floor(100000/unit),tx_frames=sum(b['tx_frames'] for b in x['boards'].values()),tx_data_frames=sum(b['tx_data'] for b in x['boards'].values())))
(p/'formal-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(summary,ensure_ascii=False))

lines=['四节点 UWB 组网实验实时汇总',f'正式完成 {len(formal)}/10 组；每组 100000 条四字节原始数据。','', '配置 | 最终收到 | 首次到达率 | 平均一轮 ms | 整轮收齐率']
for r in summary:lines.append(f"{r['name']} | {r['received']}/{r['records']} | {r['first_pdr']*100:.3f}% | {r['round_mean_ms']:.3f} | {r['round_all']*100:.3f}%")
lines+=['','逐个点名与分时回复每轮三个节点；两跳组及其直连对照每轮两个叶节点。','尚未完成的配置不纳入结果。节点数量推算见 formal-summary.json，其中200与300节点为串行耗时估算。']
(p/'四板实验实时汇总.txt').write_text('\n'.join(lines),encoding='utf-8-sig')
