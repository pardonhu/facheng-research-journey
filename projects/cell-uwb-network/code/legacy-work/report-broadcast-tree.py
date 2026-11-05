from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyArrowPatch
out=Path('outputs/broadcast-tree-study');rows=json.loads((out/'summary.json').read_text());raw=[json.loads(x) for x in (out/'results.jsonl').read_text().splitlines()]
ref=next(r for r in rows if r['name']=='poll-reference');best=next(r for r in rows if r['name']=='broadcast-slot486');fault=next(r for r in rows if 'missing10' in r['name'])
font=FontProperties(fname='C:/Windows/Fonts/msyh.ttc');plt.rcParams.update({'font.family':font.get_name(),'font.size':12,'axes.unicode_minus':False,'svg.fonttype':'path'})
fig,ax=plt.subplots(figsize=(12,7));ax.set(xlim=(-.4,3.4),ylim=(-.7,9));ax.axis('off')
for i,t in enumerate(['A 中心','B 中继','C 电芯数据源','D 电芯数据源']):
 ax.text(i,8.5,t,ha='center');ax.plot([i,i],[-.2,8],color='#c5cbd1',lw=1)
steps=[(0,1,7.6,'开始本轮采集'),(1,3,6.6,'广播一次：C、D 按顺序回复'),(2,1,5.5,'C 的四字节数据'),(3,1,4.5,'D 的四字节数据'),(1,0,3.4,'收齐后合成一个包'),(1,3,2.4,'B 广播确认'),(1,0,1.4,'结束通知'),(0,3,.4,'A 广播确认')]
for k,(a,b,y,t) in enumerate(steps):
 color='#377F79' if k in (2,3) else '#B77239' if k==4 else '#66717D'
 ax.add_patch(FancyArrowPatch((a,y),(b,y),arrowstyle='-|>',mutation_scale=14,color=color,lw=1.5,linestyle='--' if k in (1,5,7) else '-'))
 ax.text((a+b)/2,y+.16,t,ha='center',fontsize=11,color=color)
ax.text(2.55,3.9,'缺谁，单独点名谁补发\n收齐后再合包',ha='center',fontsize=11,color='#B54F46',bbox=dict(facecolor='#fff7ee',edgecolor='#B77239',boxstyle='round,pad=.4'))
fig.suptitle('只改中继收数据的方式，其余两跳流程保持一致',fontsize=17)
fig.text(.5,.025,'每次广播重新提供时间起点；箭头表示先后，纵向距离不代表耗时。广播各算一次发射。',ha='center',fontsize=11)
fig.savefig(out/'广播两跳流程.png',dpi=170);fig.savefig(out/'广播两跳流程.svg');plt.close(fig)
fig,ax=plt.subplots(figsize=(12,5.5));names=['逐个点名','广播，间隔636μs','广播，间隔486μs','广播486μs\nD首包故意漏发10%'];colors=['#377F79','#B77239','#66717D']
bottom=[0]*len(rows)
for key,label,color in zip(['collection_ms','uplink_ms','other_ms'],['中继收集电芯数据','中继准备并发送合包','其余控制、等待和处理'],colors):
 vals=[r[key] for r in rows];ax.bar(range(len(rows)),vals,bottom=bottom,label=label,color=color,width=.58);bottom=[a+b for a,b in zip(bottom,vals)]
for i,r in enumerate(rows):ax.text(i,r['mean_ms']+.08,f"{r['mean_ms']:.3f} ms",ha='center')
ax.set_xticks(range(len(rows)),names);ax.set_ylabel('收齐两个电芯的全程平均耗时 / ms');ax.set_ylim(0,max(bottom)*1.16);ax.spines[['top','right']].set_visible(False);ax.legend(ncol=3,loc='upper center',bbox_to_anchor=(.5,1.13),fontsize=10)
fig.suptitle('每组五万条数据：减少点名能省多少全程时间',fontsize=17);fig.subplots_adjust(top=.79,bottom=.17);fig.savefig(out/'全过程耗时比较.png',dpi=170);fig.savefig(out/'全过程耗时比较.svg');plt.close(fig)
saving=ref['mean_ms']-best['mean_ms'];percent=saving/ref['mean_ms']*100
text=f'''# 四板广播定时回复与逐个轮询对照实验

## 这次实验回答什么

**每轮只广播一次，让两个电芯按时回复，能否比逐个点名更快？时刻能否安排准确？缺包能否补回来？**

每组五万条原始电芯数据，C、D 各两万五千条，共两万五千轮。每轮从中心启动采集，到中继收齐、合包交给中心，并完成确认和规定等待为止。板子生成测试值，未计入真实传感器采样。

这次的三个判断：

1. **减少点名能缩短全过程。** 本轮轮询平均 {ref['mean_ms']:.3f} ms，486 μs 分时回复平均 {best['mean_ms']:.3f} ms，每两个电芯省 {saving:.3f} ms，减少 {percent:.1f}%。
2. **本次短时间同步足以支持486 μs回复间隔。** 中继测得两包间隔相对计划值的偏差为 {best['pair_min_ns']}～{best['pair_max_ns']} ns，共 {best['pair_samples']:,} 个有效双包样本；叶节点错过发送时刻累计 {best['late_tx']} 次。每轮广播重新同步，第二个叶节点计划在广播后的1236 μs回复。这个结果用于当前组内定时回复，未测100 ms不重新同步时的漂移。
3. **缩短间隔的障碍出现在接收处理。** 386 μs短测中，两节点都按计划发出，B在每轮首次收集时只收到C，随后点名D补发；486 μs能正常接收。B处理第一包并重新开启接收的实测程序耗时约 {best['rearm_mean_us']:.1f} μs，尚需给下一包的前导码留出接收时间。

## 怎么做，为什么这样比较

A做中心，B做中继，C、D各模拟一个电芯。四板身份与上一轮一致：A/B为nRF52832，C/D为nRF52840，UWB芯片均识别为DECA0302。摆放沿用开始本轮实验时的位置，未做距离标定。

![广播两跳流程](broadcast-tree-study/广播两跳流程.png)

轮询组：B点名C、收C，再点名D、收D。广播组：B用一条广播通知两个叶节点，C先发、D后发，随后只点名缺失的节点补发。中继转发的是实际接收并缓存的四字节数据。中心按实验号、轮号、节点号检查数据，防止旧数据被算入新一轮。

正常广播流程共八帧，原轮询流程共九帧。两组保留相同的合包发送、确认、结束通知及等待，并在同一版固件中重测轮询，避免把其他修改的收益算给广播。同步计时也会增加少量程序处理，结果代表当前带计时的程序。

## 每个参数从哪里来

| 参数 | 本次取值 | 来源与作用 |
|---|---|---|
| 每个电芯的数据量 | 4字节 | 用户指定；两条合包为8字节有效数据 |
| 每组业务量 | 50,000条 | 用户指定；补发和控制消息另计 |
| 前导码 | 64符号 | 采用上一轮最快且可靠的两跳配置，各组一致 |
| 信道与速率 | 信道5，6.8 Mbps | 沿用当前配置，各组一致 |
| 第一叶节点回复时刻 | 广播接收时间标记后750 μs | 已有测试从1000 μs降到750 μs；500 μs准备不及 |
| 两叶节点回复间隔 | 636、486 μs | 相邻回复时间标记之差；短测扫描386、486、536、636 μs后选择486 μs进入长测 |
| 转发前等待 | 200 μs | 自编实验程序中的保守等待，可改；本次保持一致 |
| 确认前、后等待 | 200、500 μs | 自编实验程序中的保守等待，可改；本次保持一致 |
| 结束通知前等待 | 1000 μs | 自编实验程序中的保守等待，可改；本次保持一致 |
| 中心等结束通知上限 | 60 ms | 实验程序的超时值；收到通知即结束等待，丢失时会拉长轮次 |
| 每个叶节点尝试上限 | 5次 | 含广播后的第一次发送；失败后单独点名补发，最多再试4次 |
| 中心请求中继上限 | 5次 | 中心缺少数据时重试，中继保留当前轮已收数据 |
| 34/38字节帧长 | 单条34、合包38字节 | 9字节MAC头＋19字节实验字段＋4/8字节电芯值＋2字节校验 |

这些等待属于可修改的程序参数，未逐项证明是最小值。板上测得的0.651 ms等阶段耗时是运行结果，不能作为芯片规定的固定时长。

“间隔486 μs”包含相邻两帧之间的一帧发送时间。按本配置单数据帧空口约135.835 μs计算，两帧之间的空闲约350.165 μs。程序参数名guard_us通过136 μs近似值换算，报告采用实际安排的时间标记间隔。

## 全过程省了多少时间

![全过程耗时比较](broadcast-tree-study/全过程耗时比较.png)

| 实验 | 最终收到/应收 | 收齐两电芯平均ms | 99%的轮次在多少ms内结束 | 叶节点补发尝试次数 |
|---|---:|---:|---:|---:|
'''
for name,r in zip(names,rows):
 text+=f"| {name.replace(chr(10),' ')} | {r['received']:,}/{r['target']:,} | {r['mean_ms']:.3f} | {r['p99_upper_ms']:.3f} | {r['relay_retries']:,} |\n"
text+='''
收益包括少发一条点名消息，以及C、D收到同一广播后可同时准备各自的回复。原轮询需要等C交完，再点名D启动准备。

上表P99来自25 μs分箱，取所在箱的上界。少量结束通知漏收造成的长超时会拉高平均值，因此平均值可能高于P99。最终收到包含补发；初次广播收到多少单独列在下面，避免把补发后的成功率当成首发成功率。

| 实验 | 初次广播应交条数 | 初次收到 | 需要补的条数 | 中心再次请求中继次数 |
|---|---:|---:|---:|---:|
'''
for name,r in zip(names[1:],rows[1:]):text+=f"| {name.replace(chr(10),' ')} | {r['first_leaf_expected']:,} | {r['first_leaf_received']:,} | {r['first_leaf_missing']:,} | {r['root_retries']:,} |\n"
text+='''
耗时分解进一步显示：中继收集两个叶节点从2.711 ms降到1.882 ms；准备和发送合包均约0.635 ms；其余控制等待均约4.42 ms。因此，本次收益主要来自改变收集方式，尚未压缩其余等待。

## 同步到底测了什么

叶节点以收到B广播的硬件时间标记为起点，通过UWB芯片定时发送。B用自己的同一个硬件时钟记录C、D到达时刻，计算“实际间隔减计划间隔”。这个量直接回答两包有没有按安排错开。

| 广播配置 | 双包样本数 | 间隔偏差最小ns | 间隔偏差最大ns | 平均偏差ns | 错过发送时刻次数 |
|---|---:|---:|---:|---:|---:|
'''
for name,r in zip(names[1:],rows[1:]):text+=f"| {name.replace(chr(10),' ')} | {r['pair_samples']:,} | {r['pair_min_ns']} | {r['pair_max_ns']} | {r['pair_mean_ns']:.2f} | {r['late_tx']} |\n"
text+=f'''
1 ns等于0.001 μs。486 μs相邻回复之间有约350 μs空闲，当前观察到的时刻偏差远小于这段空闲。正式测试中，数据最终收到 {best['received']:,}/{best['target']:,} 条。

上述时间统计来自两包都收到的轮次；丢失的包没有接收时间标记，因此首发缺失数必须一起看。叶节点同时记录实际发送时间标记相对请求值的偏差。芯片回读的发射天线延迟寄存器为16405个芯片时间单位，约0.257 μs，会使该原始偏差带固定偏移；它不等于时钟随机抖动。两包到达间隔的计算会抵消大部分共同偏移。本次没有外接示波器，也未做绝对时间标定。

## 为什么386 μs更慢

短测每档600条，仅用来筛选长测参数。386 μs下首次收到300/600条，缺失的D数据经轮询补齐；486、536、636 μs短测首次均收到600/600条。

386 μs已经大于单帧约136 μs的空口长度，因此这个短测中的失败不能仅用“两个无线包重叠”来解释。B接收第一包后，读取帧、校验、记录时间并重新开启接收需要约302～303 μs；下一包的前导码开始时可能还没准备好。把间隔放到486 μs，首轮接收恢复。该结果支持优先优化中继接收处理，而不是继续压缩同步误差。

## 缺包补发有没有真的工作

正式故障组让D每十轮主动跳过一次广播后的首发，实际注入 {fault['injected_D']:,} 次，相当于D首发的10%、全部五万条业务数据的5%。被点名补发时D恢复正常。最终收到 {fault['received']:,}/{fault['target']:,} 条，叶节点补发尝试 {fault['relay_retries']:,} 次。该组是确定性漏发检查，不模拟独立随机无线丢包。

另做600条短测：D在指定十轮保持不回复，中心记录D缺十条，C零缺失。这说明程序会如实记录收不到的数据，没有用本地生成的预期值代替漏收内容。

## 对200～300节点目标意味着什么

下面仍按“每组两个电芯，同一信道各组依次工作”推算。用四板连续采集100组/150组的实测段计时，代表200/300条数据的串行时间预算；没有部署200/300块实体电芯板。

| 方案 | 200条平均ms | 300条平均ms | 100ms内收齐200条的段数/250 |
|---|---:|---:|---:|
'''
for name,r in zip(names,rows):text+=f"| {name.replace(chr(10),' ')} | {r['window200']['mean_ms']:.3f} | {r['window300']['mean_ms']:.3f} | {r['window200']['within100ms']}/250 |\n"
text+='''
广播安排已经减少点名和重复等待。当前仍保留每轮结束通知、两级确认及固定等待，下一步优先逐项缩短等待、合并控制消息，再测全过程。两节点广播方案通过后，再增加实体叶节点，测更大组的时钟漂移、接收恢复和丢包补发成本。

## 数据与代码

- [原始记录](broadcast-tree-study/results.jsonl)：含短测、四组正式数据、四板计数、接收位图对应计数及时间直方图。
- [正式结果汇总](broadcast-tree-study/summary.json)。
- [备份清单](broadcast-tree-study/backup-manifest.json)：烧录前四板固件和UICR哈希。
- [完成后核对](broadcast-tree-study/verification.json)：固件、UICR、接收位图、200/300条计时段和同步计数一致性。
- [实验代码与数据包](广播定时回复实验代码与数据.zip)。

所有自然丢包组按当前摆放完成，每组顺序运行。结论对应本次位置与程序；后续不同距离、金属遮挡和温度变化应重复这套对照。
'''
Path('outputs/广播定时回复与轮询全过程对照.md').write_text(text,encoding='utf-8')
print('Report and two diagrams created')
