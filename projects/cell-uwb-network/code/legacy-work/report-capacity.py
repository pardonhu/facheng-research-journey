from pathlib import Path
import json,math,sys,zipfile,shutil,hashlib
root=Path.cwd();out=root/'outputs/capacity-study'
rows=[json.loads(x) for x in (out/'results.jsonl').read_text().splitlines()]
q=lambda a,p:sorted(a)[min(len(a)-1,max(0,math.ceil(len(a)*p)-1))] if a else None
stage1=[];stage2=[]
for gap in (500,300,200,150,100,50,0):
 rr=[r for r in rows if r['stage']==1 and r['gap_us']==gap]
 if not rr:continue
 period=sum(r['mean_period_us']*r['interval_samples'] for r in rr)/sum(r['interval_samples'] for r in rr)
 stage1.append(dict(gap_us=gap,runs=len(rr),packets=sum(r['count'] for r in rr),pdr=sum(r['rx']['unique'] for r in rr)/sum(r['count'] for r in rr),min_run_pdr=min(r['pdr'] for r in rr),max_run_pdr=max(r['pdr'] for r in rr),period_us=period,capacity_100ms=math.floor(100000/period),estimate_200_ms=period*.2,estimate_300_ms=period*.3,max_loss_run=max(r['longest_loss_run'] for r in rr)))
keys=sorted(set((r['gap_us'],r['mode'],r['batch_size']) for r in rows if r['stage']==2))
for gap,mode,batch in keys:
 rr=[r for r in rows if r['stage']==2 and (r['gap_us'],r['mode'],r['batch_size'])==(gap,mode,batch)]
 bb=[b for r in rr for b in r['batches'] if b['size']==batch];tt=[b['us']/1000 for b in bb]
 stage2.append(dict(gap_us=gap,mode=mode,batch=batch,runs=len(rr),batches=len(bb),pdr=sum(r['rx']['unique'] for r in rr)/sum(r['count'] for r in rr),all_delivered=sum(b['all_delivered'] for b in bb)/len(bb),within_100ms=sum(b['deadline_confirmed'] for b in bb)/len(bb),mean_ms=sum(tt)/len(tt),p50_ms=q(tt,.5),p95_ms=q(tt,.95),p99_ms=q(tt,.99),max_ms=max(tt),retransmissions=sum(r['tx']['retransmissions'] for r in rr)))
summary=dict(stage1=stage1,stage2=stage2,completed_stage1=sum(r['stage']==1 for r in rows),completed_stage2=sum(r['stage']==2 for r in rows))
(out/'summary.json').write_text(json.dumps(summary,indent=2))
lines=['UWB 帧间隔与批量可靠交付实验','',f"已完成：第一项 {summary['completed_stage1']}/42 组；第二项 {summary['completed_stage2']}/24 组。",'每组100000包。第一项每个等待值双向各重复3次；第二项每个选定等待值分别测试双向、开启/关闭重传、每批200/300条。',
'统一配置：信道5，6.8Mbps，前导码128，PAC8，STS关闭；有效载荷32字节，空中帧59字节（含FCS）；开发板HF晶振启用。',
'实际周期：相邻数据帧UWB TX时间戳之差。时间戳位于帧内同一参考点，相同帧长下该差值等于帧起点间隔。',
'等待值：发送完成、读取时间戳后执行的软件等待。每包时间戳读取及统计开销包含在实测周期中。',
'第一项开始和结束各有会话控制交换；数据阶段无逐包或分组ACK、无重传。周期统计仅使用连续序号DATA帧。',
'第二项：每批独立划分32包确认窗口，批末不足32包时使用部分位图。开启重传时每包最多发送5次。',
'第二项批耗时：发送端从准备该批第一个包开始，到最后数据发完（无重传模式）或最后分组确认处理完成（重传模式）。初始握手和最终会话汇总不计入每批，整场elapsed包括这些开销。',
'100ms达标：批内全部数据最终收到、批耗时<=100ms；重传模式还要求该批全部数据已经确认。',
'无重传模式依据接收端最终位图验证全批收到，发送端没有逐批交付确认。两种模式分别统计。',
'300条一批时，100000包末尾剩余100条；分位数和整批达标率仅统计333个完整批次，末批仍计入总体收包率。',
'节点容量为两板单链路时间预算，200/300批量数据是模拟上报条目。',
'采样量每配置双向合计1000个200条批次或666个300条批次；报告P50/P95/P99。',
'连续丢包依据接收端最终去重位图，计入头部和尾部缺包。',
'', '第一项：等待(us) | 完成组数 | 成功率 | 实测周期(us) | 100ms容量估算 | 200条(ms) | 300条(ms) | 最长连续缺包']
for r in stage1:lines.append(f"{r['gap_us']} | {r['runs']}/6 | {r['pdr']*100:.6f}% | {r['period_us']:.3f} | {r['capacity_100ms']} | {r['estimate_200_ms']:.3f} | {r['estimate_300_ms']:.3f} | {r['max_loss_run']}")
lines+=['','第二项：等待(us) | 模式 | 每批条数 | 完成组数 | 全批交付率 | 100ms达标率 | 平均(ms) | P95(ms) | P99(ms) | 最大(ms)']
for r in stage2:lines.append(f"{r['gap_us']} | {'重传' if r['mode'] else '无ACK无重传'} | {r['batch']} | {r['runs']}/2 | {r['all_delivered']*100:.3f}% | {r['within_100ms']*100:.3f}% | {r['mean_ms']:.3f} | {r['p95_ms']:.3f} | {r['p99_ms']:.3f} | {r['max_ms']:.3f}")
(out/'实验结果.txt').write_text('\n'.join(lines),encoding='utf-8-sig')
sys.path.insert(0,str(root/'work/plot-libs'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
if stage1:
 fig,axs=plt.subplots(1,2,figsize=(11,4.2));rr=sorted(stage1,key=lambda r:r['period_us'])
 axs[0].plot([r['period_us'] for r in rr],[r['pdr']*100 for r in rr],'o-');axs[0].set(xlabel='Measured DATA period (us)',ylabel='Packet delivery (%)',title='No ACK, no retry')
 axs[1].plot([r['gap_us'] for r in stage1],[r['capacity_100ms'] for r in stage1],'o-');axs[1].axhline(200,color='orange',ls='--',label='200 reports');axs[1].axhline(300,color='red',ls='--',label='300 reports');axs[1].set(xlabel='Configured wait (us)',ylabel='Reports / 100 ms',title='Single-link timing estimate');axs[1].legend()
 for ax in axs:ax.grid(alpha=.3)
 fig.tight_layout();fig.savefig(out/'帧周期与容量.png',dpi=180);plt.close(fig)
print(json.dumps({k:summary[k] for k in ('completed_stage1','completed_stage2')}))
