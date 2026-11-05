from pathlib import Path
import json,math
root=Path.cwd();out=root/'outputs/preamble-study'
rows=[json.loads(x) for x in (out/'results.jsonl').read_text().splitlines()] if (out/'results.jsonl').exists() else []
normal=[r for r in rows if r['stage']>0]
summary=[]
for payload in (32,4):
 for preamble in (128,64,32):
  for mode in (0,1):
   rr=[r for r in normal if (r['payload'],r['preamble'],r['mode'])==(payload,preamble,mode)]
   if not rr:continue
   total=sum(r['count'] for r in rr);bb=[b for r in rr for b in r['batches'] if b['size']==300]
   durations=sorted(b['us']/1000 for b in bb)
   period=sum(r['mean_period_us']*r['interval_samples'] for r in rr)/sum(r['interval_samples'] for r in rr)
   summary.append(dict(payload=payload,preamble=preamble,mode=mode,runs=len(rr),packets=total,first_pdr=sum(r['rx']['first_unique'] for r in rr)/total,final_pdr=sum(r['rx']['unique'] for r in rr)/total,mean_data_period_us=period,effective_us_per_delivered=sum(r['tx']['elapsed'] for r in rr)/sum(r['rx']['unique'] for r in rr),elapsed_s=sum(r['tx']['elapsed'] for r in rr)/1e6,retransmissions=sum(r['tx']['retransmissions'] for r in rr),batch_count=len(bb),batch_all_delivered=sum(b['all_delivered'] for b in bb)/len(bb),batch_deadline=sum(b['deadline_confirmed'] for b in bb)/len(bb),batch_mean_ms=sum(durations)/len(durations),batch_p95_ms=durations[math.ceil(len(durations)*.95)-1],batch_p99_ms=durations[math.ceil(len(durations)*.99)-1]))
(out/'summary.json').write_text(json.dumps(dict(completed=len(normal),planned=24,groups=summary),indent=2))
lines=['UWB 前导码与4字节载荷优化验证','',f'已完成正式测试 {len(normal)}/24 组，每组100000包。',
'第一部分：保持32字节载荷，前导码128/64/32。第二部分：4字节载荷，前导码128/64/32。每种配置双向分别测试无ACK无重传、32包位图ACK最多5次发送。',
'统一：信道5，6.8Mbps，PAC8，SFD8，标准PHR，STS关闭，功率寄存器0xfdfdfdfd，发送后等待0us。SFD接收超时按前导码长度相应设置为129/65/33。',
'DATA帧：9字节MAC头+16字节实验字段+32或4字节载荷+2字节CRC，总长59或31字节。控制帧保持59字节。',
'身份、会话、序号和CRC均保留；未采用固定时隙隐含身份、固定路由或预测压缩。当前实验仍为两板链路验证。',
'控制帧也使用当组前导码长度。每轮结束回报接收端实际去重收包数量。',
'实测DATA周期来自硬件TX时间戳，包含SPI和逐包采集开销。重传模式的DATA周期只统计没有控制帧插入的连续序号数据；包含确认、补发的总体效率看每交付一包的平均耗时。',
'每批300条，完整批次333个/组，尾部100条仅计入全场收包率。100ms达标要求全批收到且批耗时<=100ms，ACK模式还要求全部确认。',
'', '载荷(B) | 前导码 | 模式 | 组数 | 首次成功率 | 最终成功率 | DATA周期(us) | 每交付一包平均(us) | 补发次数 | 300条平均(ms) | P95(ms) | 100ms达标率']
for r in summary:lines.append(f"{r['payload']} | {r['preamble']} | {'重传' if r['mode'] else '无ACK'} | {r['runs']}/2 | {r['first_pdr']*100:.5f}% | {r['final_pdr']*100:.5f}% | {r['mean_data_period_us']:.3f} | {r['effective_us_per_delivered']:.3f} | {r['retransmissions']} | {r['batch_mean_ms']:.3f} | {r['batch_p95_ms']:.3f} | {r['batch_deadline']*100:.3f}%")
lines+=['','小规模验证：']
for r in rows:
 if r['stage']==0:lines.append(f"{r['name']}：{r['rx']['unique']}/{r['count']}，DATA周期{r['mean_period_us']:.3f}us，补发{r['tx']['retransmissions']}次。")
(out/'优化实验结果.txt').write_text('\n'.join(lines),encoding='utf-8-sig')
print(json.dumps(dict(completed=len(normal),planned=24)),flush=True)
