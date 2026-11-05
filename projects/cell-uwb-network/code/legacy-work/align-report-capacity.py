from pathlib import Path
import json
root=Path(__file__).resolve().parent.parent
p=root/'outputs/当前组网报告配图/plot_current.py'
s=p.read_text(encoding='utf-8').replace('帧控制与地址信息\\n72 bit','标准短地址帧头\\n72 bit').replace('实验编号、轮次等字段\\n152 bit','自定义实验管理字段\\n152 bit')
a=s.index('fig,ax=plt.subplots(figsize=(12,3.8))');b=s.index('# Consistent topology',a)
s=s[:a]+'''fig,axes=plt.subplots(2,1,figsize=(12,6))
air=135.835
for ax,slot in zip(axes,(636,486)):
 ax.set(xlim=(-20,850),ylim=(0,3.8));ax.axis('off')
 for start,t in [(0,'C数据帧'),(slot,'D数据帧')]:box(ax,start,1.45,air,.8,t)
 ax.annotate('',(0,2.85),(slot,2.85),arrowprops=dict(arrowstyle='<->',color=blue))
 ax.text(slot/2,3.1,f'相邻发包起始间隔 {slot} μs',ha='center')
 ax.annotate('',(air,.95),(slot,.95),arrowprops=dict(arrowstyle='<->',color=gray))
 ax.text((air+slot)/2,.5,f'帧间隔 {slot-air:.1f} μs',ha='center')
 ax.text(air/2,2.4,'发送135.8 μs',ha='center',fontsize=10)
 arrow(ax,(-5,1.2),(830,1.2));ax.text(820,.95,'时间',ha='right')
fig.tight_layout();save(fig,'03-帧间隔定义')
'''+s[b:]
s=s.replace("ax.text(.45,3.4,'B处理C数据\\n并恢复接收',ha='center',fontsize=10,color=gray)", "ax.annotate('',(.70,2.3),(.70,4.3),arrowprops=dict(arrowstyle='<->',color=blue))\n  ax.text(.65,3.3,'相邻发包起始间隔\\nΔt₄ − Δt₂',ha='right',va='center',fontsize=10,color=blue)")
p.write_text(s,encoding='utf-8')
p=root/'work/finalize-research-report.py';s=p.read_text(encoding='utf-8')
s=s.replace('相邻回复间隔','相邻发包起始间隔').replace('计划回复间隔','计划发包起始间隔')
s=s.replace('## 1 实验平台与研究目标','## 1 研究目标与实验平台')
s=s.replace('### 2.1 厂家帧结构','### 2.1 现有结果对应的帧结构')
anchor='### 2.2 单帧发送时间与帧间隔'
table='''**现有组网结果均采用272 bit单条数据帧、304 bit双条聚合帧，控制帧为240 bit。** 120 bit格式尚未进行重测。

| 无线发送组成 | 本次设置或长度 | 来源 |
|---|---|---|
| 前导码 | 长度64 symbol，约65.13 μs | 芯片可配置，本实验选择64 |
| 帧起始定界符 | 长度8 symbol，约8.14 μs | 本实验选用芯片支持的8 symbol格式 |
| 物理层帧头 | 21 symbol，约21.54 μs | 芯片生成，本实验采用标准速率 |
| 单条数据帧 | 72 bit短地址帧头＋152 bit实验管理字段＋32 bit电芯数据＋16 bit校验 | 短地址格式来自标准；152 bit为自定义；32 bit为实验要求；校验由芯片生成 |
| 纠错编码冗余 | 本次272 bit数据帧附加48 bit | 芯片自动编码 |

前导码中的symbol表示重复的已知脉冲序列；当前每个前导码symbol约1.01763 μs。数据字段用bit表示长度，各部分耗时统一用μs比较。上述物理层时序依据[DW3000数据手册表18与第4.5节](https://www.mouser.com/catalog/specsheets/Qorvo_DW3000.pdf)。

'''
s=s.replace(anchor,table+anchor)
old='图3. 两个等长数据帧的时间关系。'
a=s.index(old);b=s.index('\n\n',a)
s=s[:a]+'''图3. 帧间隔与相邻发包起始间隔，横向按时间比例绘制。帧间隔从C帧结束计算到D帧开始；相邻发包起始间隔从C帧开始计算到D帧开始。272 bit数据帧在本次物理层配置下计算发送时长为135.835 μs；起始间隔636、486 μs分别对应帧间隔500.165、350.165 μs，图中保留一位小数。636、486 μs为程序设置，帧间隔为计算值。'''+s[b:]
s=s.replace('参数表中的750 μs以帧内硬件时间戳为起止，图中Δt以完整接收和开始发送为起止。','参数表中的750 μs以帧内硬件时间戳为起止，图中Δt以完整接收和开始发送为起止。Δt₄−Δt₂表示两个叶节点回复开始时刻之差，对应相邻发包起始间隔；图示以广播接收作为共同时间参考。')
a=s.index('## 5 结论与后续实验');b=s.index('## 附录A',a)
rows=json.loads((root/'outputs/broadcast-tree-study/summary.json').read_text())
star=json.loads((root/'outputs/four-board-study/formal-summary.json').read_text())
cases=[('星型拓扑广播：轮询对照',3,next(r['round_mean_ms'] for r in star if r['name']=='individual-3')),('星型拓扑广播：间隔636 μs',3,next(r['round_mean_ms'] for r in star if r['name']=='group-3-guard500'))]
cases += [(label,2,rows[i]['mean_ms']) for label,i in [('树型拓扑两跳中继：轮询',0),('树型拓扑两跳中继：间隔636 μs',1),('树型拓扑两跳中继：间隔486 μs',2)]]
capacity='''## 5 100 ms内能收齐多少节点

- **相邻发包起始间隔决定连续回复速度，完整采集时延决定一轮能收齐多少节点。** 广播请求、重传、中继转发、确认及等待均需计入总时间。

### 5.1 先用帧间隔计算连续回复的时间预算

相邻发包起始间隔 S = 单帧发送时间 T + 帧间隔 G。

按每节点分配一个完整时槽计算，连续回复的预算容量为 floor(100000 / S)，其中时间单位为μs。floor表示向下取整。

| 相邻发包起始间隔S | 单帧发送时间T | 帧间隔G | 100 ms可分配的连续回复时槽 |
|---:|---:|---:|---:|
| 636 μs | 135.835 μs | 500.165 μs | 157 |
| 486 μs | 135.835 μs | 350.165 μs | 205 |

**157和205表示只安排连续数据回复时的时槽数量。** 要得到中心完整收齐的节点数，还要给广播、补发、中继转发和确认留出时间。若300节点共用100 ms，每节点的全部通信预算约333.3 μs。

### 5.2 再按实测完整流程计算节点容量

**按现有流程串行重复，星型拓扑广播在100 ms平均时间预算内可安排72节点；树型拓扑两跳中继可安排28节点。**

每组电芯数记为k，每组实测平均完整采集时延记为R（ms）。各组在同一信道依次执行相同流程：

- 100 ms容量 = k × floor(100 / R)。
- N节点采集时间 = ceil(N / k) × R；ceil表示向上取整，最后一组按完整一轮计时。

| 拓扑与调度 | 每组电芯数k | 实测平均完整时延R（ms） | 100 ms容量（节点） | 200节点推算（ms） | 300节点推算（ms） |
|---|---:|---:|---:|---:|---:|
'''
import math
for label,k,r in cases:
 capacity+=f'| {label} | {k} | {r:.3f} | {k*math.floor(100/r)} | {math.ceil(200/k)*r:.1f} | {math.ceil(300/k)*r:.1f} |\n'
capacity+='''
表中R来自四块板的实测，包含控制、数据、重传、处理和等待；容量及200、300节点耗时为相同小分组串行重复的推算。实际测试规模为星型三个电芯节点、树型两个电芯节点。上述容量按平均耗时计算，截止时间内的成功率需进一步测试。

### 5.3 结论

- **广播定时回复提高了采集效率。** 星型拓扑广播比轮询降低32.4%的完整采集时延；树型拓扑两跳中继在636 μs起始间隔下降低8.9%，486 μs下降低10.7%。
- **现有小分组串行流程超出200～300节点、100 ms的时间预算。** 树型拓扑两跳中继的主要开销是控制、处理与等待；仅缩短叶节点回复间隔，收益有限。
- **下一步统一采用120 bit常规短地址数据帧重测，并扩大单次广播的调度节点数。** 120 bit由72 bit短地址帧头、32 bit电芯数据和16 bit校验组成；本报告的实测与容量推算均对应现有272 bit单条数据帧。

'''
s=s[:a]+capacity+s[b:]
p.write_text(s,encoding='utf-8')
p=root/'AGENTS.md';s=p.read_text(encoding='utf-8')
s+='\n- 容量分析同时给出帧间隔（前帧结束到后帧开始）、相邻发包起始间隔（两帧开始之差）和完整采集时延；图中直接标明中文名称及数值。容量公式写清按连续时槽估算还是按完整小分组串行推算，并注明现有实测帧结构。\n'
p.write_text(s,encoding='utf-8')
