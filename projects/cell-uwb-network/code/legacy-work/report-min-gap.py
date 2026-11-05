from pathlib import Path
import json,statistics,math,hashlib,zipfile,re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Rectangle
root=Path.cwd();out=Path((root/'work/min-gap-latest.txt').read_text())
rows=[json.loads(l) for l in (out/'results.jsonl').read_text().splitlines()]
formal=[r for r in rows if r['formal'] and r['name'].startswith('v3-')]
for r in formal:r.setdefault('preamble',32)
zero=next(r for r in formal if r['preamble']==128 and r['gap_us']==0)
best=min((r for r in formal if r['pdr']==1),key=lambda r:r['mean_record_us'])
def full_batches(r):return r['batch_time_us'][:r['target']//r['batch']]
def air(r):return r['slot_us']-r['gap_us']
plt.rcParams.update({'font.family':FontProperties(fname='C:/Windows/Fonts/msyh.ttc').get_name(),'font.size':11,'axes.unicode_minus':False})
fig,ax=plt.subplots(figsize=(11,3.2));ax.axis('off');ax.set(xlim=(-3,490),ylim=(0,3))
for i,name in enumerate(['A数据帧','B数据帧','D数据帧']):
 x=i*air(zero);ax.add_patch(Rectangle((x,1),air(zero),.8,facecolor='#e1efec',edgecolor='#377f79'));ax.text(x+air(zero)/2,1.4,name,ha='center',va='center')
ax.annotate('',(0,2.2),(air(zero),2.2),arrowprops=dict(arrowstyle='<->',color='#386b91'));ax.text(air(zero)/2,2.4,f'起始间隔约{air(zero):.1f} μs',ha='center')
ax.text(air(zero),.6,'帧间隔设为0 μs',ha='center');ax.annotate('',(480,.2),(0,.2),arrowprops=dict(arrowstyle='->'));ax.text(480,.4,'时间',ha='right');fig.tight_layout();fig.savefig(out/'零帧间隔示意.png',dpi=180);plt.close(fig)
pick=[next(r for r in formal if r['name']==n) for n in ['v3-formal-gap100','v3-formal-p64-gap50','v3-formal-p64-gap30','v3-formal-p64-gap40','v3-formal-p128-gap0']]
fig,ax=plt.subplots(figsize=(10,4.3));vals=[statistics.mean(full_batches(r))/1000 for r in pick];bars=ax.bar(range(len(pick)),vals,color=['#66717d','#386b91','#377f79','#386b91','#b77239']);ax.bar_label(bars,fmt='%.2f',padding=3)
ax.set_xticks(range(len(pick)),[f"{r['preamble']} symbol\n间隔{r['gap_us']} μs" for r in pick]);ax.set_ylabel('每批300条完整采集平均耗时 / ms');ax.axhline(100,color='#b54f46',ls='--');ax.text(4.4,102,'100 ms',ha='right',color='#b54f46');ax.set_ylim(0,115);ax.spines[['top','right']].set_visible(False);fig.tight_layout();fig.savefig(out/'300条采集耗时.png',dpi=180);plt.close(fig)
zts=zero['stats']['C'];nzb=len(full_batches(zero));nb=len(full_batches(best));zmean=statistics.mean(full_batches(zero))/1000;bmean=statistics.mean(full_batches(best))/1000
report=f'''# 四板星型广播：最短帧间隔与完整采集实测

- **帧间隔参数已压到0 μs。** 48 bit自定义数据帧、前导码长度128 symbol、高速物理层帧头条件下，10000条首次全部收到，无需补发。
- **包含补发后，当前正式测试中最快的是前导码长度{best['preamble']} symbol、帧间隔{best['gap_us']} μs。** 首次接收率{best['first_pdr']*100:.2f}%，最终10000／10000；每批300条完整采集平均{bmean:.3f} ms，最大{max(full_batches(best))/1000:.3f} ms。
- **上述300条由三个实体发送节点重复承担时槽。** 本实验验证四板上的排程时间预算与连续收包，硬件规模为一个中心、三个叶节点。

## 1 实验目标与实现

**直接测量中心连续接收不同叶节点数据时所需的帧间隔。** 使用一次广播安排一批数据，叶节点按时槽发送，中心按收到的测试数据统计缺失，并对缺失项单独请求补发。

| 项目 | 本次设置 |
|---|---|
| 实体板分工 | C板为中心（nRF52840）；A、B、D为叶节点（两块nRF52832、一块nRF52840） |
| 组网形式 | 星型拓扑广播，一个中心直接接收三个叶节点的数据 |
| 虚拟排程 | 每批300条，三个叶节点轮流承担100个时槽；正式测试10000条，包含33批300条及末批100条 |
| 数据帧 | 32 bit确定性测试内容＋16 bit硬件校验，共48 bit；无标准地址帧头、无152 bit实验管理字段 |
| 测试内容 | 由样本编号生成32 bit测试值，用于逐条校验和统计；模拟电芯上报数据 |
| 信道与速率 | 信道5、6.8 Mbps；Qorvo 8 symbol定界符；高速物理层帧头；安全时间戳序列关闭 |
| 前导码对照 | 32、64、128 symbol |
| 接收路径 | SPI使用DMA；开启双接收缓冲，先重开接收，再读取上一包；按缓冲区CRC成功标志读取数据 |
| SPI时钟 | 正式结果均为8 MHz，C、D板使用SPIM3，A、B板使用SPIM0 |
| 首次回复安排 | 每批广播接收时间戳后1000 μs安排首个数据时间戳，随后按时槽依次发送 |
| 批尾等待 | 中心按本批计划结束时间额外等待500 μs，再检查缺失项 |
| 补发 | 每条缺失数据最多再请求4次，回复帧间等待设置500 μs；补发耗时计入完整采集时间 |
| 参数来源 | 前导码档位、硬件定时发送和双缓冲由芯片支持；时槽、批大小和上述等待由本测试程序设置 |

首次回复安排与批尾等待保留在总计时中。三块叶节点的时槽映射及配置通过调试接口预先设置；广播携带本批起始样本编号。真实电芯数据的动态时槽分配、节点加入和配置下发仍需单独实现和计时。

## 2 零帧间隔：数据帧基本首尾相接

**128 symbol前导码下，标称帧间隔0 μs完成了10000条首次接收。**

![零帧间隔时序](零帧间隔示意.png)

图1. 48 bit数据帧、前导码长度128 symbol、高速物理层帧头下的连续发送示意。每个数据帧计算发送时间约153.398 μs，时槽按相同长度设置，额外帧间隔为0 μs。A、B、D为三个不同叶节点，图中宽度按时间比例绘制；帧内前导码等字段未展开。

中心在每批开始附近采样连续接收硬件时间戳，观察到的相邻时间戳间隔为{zts['dt_min_ns']/1000:.3f}～{zts['dt_max_ns']/1000:.3f} μs。与153.398 μs计算帧时长相差约±0.02 μs，说明相邻数据帧基本首尾相接。采样覆盖每批开始附近的连续数据，额外间隔0 μs为程序设定值；各节点时钟、路径和时间戳误差仍反映在实测间隔中。

| 零帧间隔正式测试 | 实测结果 |
|---|---:|
| 首次收到／应收 | 10000／10000 |
| 补发次数 | {zts['retries']} |
| 最终收到／应收 | 10000／10000 |
| 300条完整批次数 | {nzb} |
| 每批300条平均完整耗时 | {zmean:.3f} ms |
| 每批300条最大完整耗时 | {max(full_batches(zero))/1000:.3f} ms |
| 100 ms内收齐的完整批次 | {sum(t<=100000 for t in full_batches(zero))}／{nzb} |

## 3 最短间隔与最快采集分别比较

**64 symbol前导码、30 μs帧间隔的完整采集更快。** 128 symbol前导码支持零额外间隔，其前导码本身占用更多时间；32 symbol前导码配过短间隔会产生大量缺失和补发。

![完整采集耗时](300条采集耗时.png)

图2. 每批300条虚拟上报数据的完整采集实测平均值，每个配置正式测试10000条，图中使用其中33个完整300条批次。计时从中心准备广播开始，到本批数据接收和缺包补发结束；包含广播、首节点安排、批尾等待、处理及补发。虚线为100 ms目标。

| 前导码长度 | 帧间隔设置（μs） | 单帧时长：计算（μs） | 首次接收率：实测 | 最终收到／应收：实测 | 300条平均／最大耗时：实测（ms） | 100 ms内收齐批次 |
|---:|---:|---:|---:|---:|---:|---:|
'''
for r in formal:
 times=full_batches(r)
 report+=f"| {r['preamble']} symbol | {r['gap_us']} | {air(r):.3f} | {r['first_pdr']*100:.2f}% | {r['stats']['C']['unique']}／{r['target']} | {statistics.mean(times)/1000:.3f}／{max(times)/1000:.3f} | {sum(t<=100000 for t in times)}／{len(times)} |\n"
report+='''
表中最终接收率为本次测试观察结果；批次耗时包含实际发生的补发。不同配置按顺序测试，当前结果用于选择后续复测候选。

## 4 200～300节点与100 ms目标

**300条虚拟上报已在四板实验中完成整批计时。** 最快正式配置的33个300条批次均在100 ms内收齐；零帧间隔配置的33个300条批次也均在100 ms内收齐。

| 配置 | 200条时间：线性推算（ms） | 300条时间：批次实测平均（ms） | 300条时间：批次实测最大（ms） |
|---|---:|---:|---:|
'''
for label,r in [('64 symbol，30 μs间隔',best),('128 symbol，0 μs间隔',zero)]:
 times=full_batches(r);report+=f"| {label} | {r['mean_record_us']*200/1000:.3f} | {statistics.mean(times)/1000:.3f} | {max(times)/1000:.3f} |\n"
report+='''
200条按正式10000条测试的平均每条耗时线性推算；300条列实际完整批次计时。实体300节点的空间信道、独立时钟分布和动态配置开销需要在扩大硬件规模后测量。

## 5 结论

- **此前约350 μs帧间隔不是本次硬件能达到的最短设置。** 改善接收路径后，已完成零额外帧间隔的四板正式测试。
- **当前目标应使用完整采集耗时选参数。** 本轮最快候选为64 symbol前导码、30 μs帧间隔；128 symbol、0 μs用于证明可以基本首尾相接。
- **48 bit帧、DMA和双缓冲接收已接入实际星型广播。** 最终数据逐条校验，缺失数据按请求补发，报告保留首次接收和最终接收两项统计。

数据：[正式测试记录](正式测试记录.jsonl)；代码和固件：[本次代码与固件](本次代码与固件.zip)。四块板原固件及UICR均已备份，测试结束后已停止收发。
'''
(out/'最短帧间隔与星型广播实测报告.md').write_text(report,encoding='utf-8')
(out/'正式测试记录.jsonl').write_text('\n'.join(json.dumps(r,ensure_ascii=False) for r in formal)+'\n',encoding='utf-8')
with zipfile.ZipFile(out/'本次代码与固件.zip','w',zipfile.ZIP_DEFLATED) as z:
 for n in ['min-gap-body.c','prepare-min-gap.py','run-min-gap.py','finish-min-gap.py','sweep-preamble-min-gap.py','confirm-min-gap.py','report-min-gap.py']:z.write(root/'work'/n,n)
 base=root/'work/toolnail-UWB/DW3_QM33_SDK_1.1.1/Drivers/API/Build_Platforms'
 for chip in ('52832','52840'):
  p=base/f'nRF{chip}-MinGap'
  for n in ['main.c','build.py','build/uwb-min-gap.elf','build/uwb-min-gap.hex']:z.write(p/n,chip+'/'+n)
verified=[]
for r in formal:
 bits=(out/(r['name']+'-received.bin')).read_bytes()
 assert sum((bits[i//8]>>(i%8))&1 for i in range(r['target']))==r['stats']['C']['unique']==10000
 assert len(r['batch_time_us'])==34
 assert abs(sum(r['batch_time_us'])-r['elapsed_us'])<1000
 verified.append(dict(case=r['name'],bitmap_verified=True,all_received=True))
for target in re.findall(r'\]\(([^)]+)\)',report):assert (out/target).is_file(),target
(out/'verification.json').write_text(json.dumps(dict(formal_groups=len(formal),formal_records=len(formal)*10000,checks=verified,backup_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*-before-*.bin')}),indent=2))
with zipfile.ZipFile(root/'outputs/最短帧间隔与星型广播实验结果.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in out.iterdir():
  if p.is_file():z.write(p,p.name)
print(json.dumps(dict(folder=str(out),best_name=best['name'],zero_batch_mean_ms=zmean,best_batch_mean_ms=bmean,formal_groups=len(formal),formal_records=len(formal)*10000),ensure_ascii=False))
