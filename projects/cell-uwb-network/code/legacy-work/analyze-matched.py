from pathlib import Path
import json,math,statistics
out=Path('outputs/ble-matched-study');rows=[json.loads(x) for x in (out/'results.jsonl').read_text().splitlines()];summary=[]
def air(pre,n):bits=n*8;return (pre+8)*1.01763+21*1.02564+(bits+48*math.ceil(bits/330))*.12821
for r in rows:
 if not r['formal']:continue
 cycles=[c for c in r['cycles'] if c['records']==300];ts=sorted(c['us'] for c in cycles);unit=r['elapsed_us']/(r['count']*r['aggregation']);rx=r['boards']['A'];s=r['boards'][r['controller']]
 summary.append(dict(name=r['name'],preamble=r['preamble'],mode=r['mode'],aggregation=r['aggregation'],original_packets=r['count'],actual_data_transmissions=r['boards']['B']['tx_data'],final_pdr=r['pdr'],first_pdr=rx['first_unique']/r['count'],air_us=air(r['preamble'],r['frame_bytes']),poll_air_us=air(r['preamble'],30),actual_period_us=r['period_mean_us'],actual_ifs_us=(r['period_mean_us']-air(r['preamble'],r['frame_bytes'])) if r['period_mean_us'] else None,period_excess_over_requested_us=(r['period_mean_us']-air(r['preamble'],r['frame_bytes'])-150) if r['period_mean_us'] else None,cycle_mean_ms=statistics.mean(ts)/1000,p95_ms=ts[math.ceil(.95*len(ts))-1]/1000,p99_ms=ts[math.ceil(.99*len(ts))-1]/1000,cycles=len(cycles),all_300_rate=sum(c['missing_packets']==0 for c in cycles)/len(cycles),all_300_in_100ms=sum(c['missing_packets']==0 and c['us']<=100000 for c in cycles)/len(cycles),mean_us_per_record=unit,estimated_nodes_100ms=math.floor(100000/(unit*r['aggregation']))*r['aggregation'],late_tx=sum(v['late_tx'] for v in r['boards'].values()),physical_errors=sum(v['phy_errors'] for v in r['boards'].values()),injected_poll_drops=r['boards']['B']['poll_dropped'],injected_data_drops=rx['data_dropped']))
(out/'hardware-summary.json').write_text(json.dumps(summary,indent=2))
labels={0:'单次无确认',1:'固定发五次',2:'POLL补发'}
lines=['蓝牙同规则 UWB 前导码对照','',f'已完成 {len(summary)}/15 组，每组50000个独立DATA包，重传另计。聚合包内含10条30bit数据。','测试：128符号历史基准、64符号当前配置、32符号历史基准的四分之一。','使用两板测量，按每300条数据划分采集周期；聚合数据已在发送端就绪，组内收集时间另行研究。','','前导码 | 模式 | 每包条数 | 300条平均ms | P99ms | 100ms容量估算 | 300条全部收到比例']
for r in summary:lines.append(f"{r['preamble']} | {labels[r['mode']]} | {r['aggregation']} | {r['cycle_mean_ms']:.3f} | {r['p99_ms']:.3f} | {r['estimated_nodes_100ms']} | {r['all_300_rate']*100:.3f}%")
(out/'实时容量结果.txt').write_text('\n'.join(lines),encoding='utf-8-sig');print(json.dumps(dict(completed=len(summary),latest=summary[-1] if summary else None)))
