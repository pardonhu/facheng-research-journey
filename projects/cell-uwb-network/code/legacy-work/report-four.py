from pathlib import Path
import json,math
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
out=Path('outputs/four-board-study');raw=[json.loads(x) for x in (out/'results.jsonl').read_text().splitlines()];rs=[r for r in raw if r['formal']];lookup={r['name']:r for r in rs}
assert len(rs)>=10
ind=lookup['individual-3'];groups=[r for r in rs if r['name'].startswith('group-3-guard')];best=min(groups,key=lambda r:(-r['pdr'],r['round_mean_us']));direct=lookup['direct-2-leaves'];forward=lookup['relay-forward-2'];agg=lookup['relay-aggregate-2'];fault=[r for r in raw if r['name']=='smoke-missing-D'][-1]
d=Document();sec=d.sections[0];sec.page_width=Inches(8.5);sec.page_height=Inches(11);sec.top_margin=sec.bottom_margin=Inches(.65);sec.left_margin=sec.right_margin=Inches(.7)
for name in ('Normal','Title','Heading 1','Heading 2'):
 s=d.styles[name];s.font.name='Microsoft YaHei';s._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'Microsoft YaHei');s.font.color.rgb=RGBColor(0,0,0)
d.styles['Normal'].font.size=Pt(11);d.styles['Normal'].paragraph_format.space_after=Pt(7);d.styles['Normal'].paragraph_format.line_spacing=1.12
d.styles['Title'].font.size=Pt(22);d.styles['Heading 1'].font.size=Pt(16);d.styles['Heading 2'].font.size=Pt(12)
def p(t):d.add_paragraph(t)
def h(t):d.add_heading(t,1)
def page(t):d.add_heading(t,1)
def table(head,rows,widths=None):
 t=d.add_table(rows=1,cols=len(head));t.autofit=False
 if widths:
  widths=[v*7/sum(widths) for v in widths]
  for i,w in enumerate(widths):t.columns[i].width=Inches(w)
 for i,v in enumerate(head):t.rows[0].cells[i].text=str(v)
 repeat=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(repeat)
 for row in rows:
  for c,v in zip(t.add_row().cells,row):c.text=str(v)
 for ri,row in enumerate(t.rows):
  for ci,c in enumerate(row.cells):
   if widths:c.width=Inches(widths[ci])
   c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
   pr=c._tc.get_or_add_tcPr();b=OxmlElement('w:tcBorders')
   for edge in ('top','left','bottom','right'):
    e=OxmlElement('w:'+edge);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');b.append(e)
   pr.append(b);sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'DCE6F1' if ri==0 else 'FFFFFF');pr.append(sh)
   for para in c.paragraphs:
    para.paragraph_format.space_before=Pt(4);para.paragraph_format.space_after=Pt(4)
    if ci>0:para.alignment=WD_ALIGN_PARAGRAPH.CENTER
    for r in para.runs:r.font.size=Pt(9.5);r.bold=ri==0
 gap=d.add_paragraph();gap.paragraph_format.space_before=Pt(0);gap.paragraph_format.space_after=Pt(0);gap.paragraph_format.line_spacing=Pt(3)
 return t
def pct(v):return f'{100*v:.3f}%'
def ms(v):return f'{v/1000:.3f}'
def q99(r):return '≥102.375' if r['round_p99']['upper_us'] is None else ms(r['round_p99']['upper_us'])
def statsrow(label,r):return [label,pct(r['pdr']),ms(r['round_mean_us']),q99(r),pct(r['all_round_rate'])]
d.add_heading('四节点 UWB 电芯组网可行性验证',0)
p('实验记录与导师汇报材料　2026 年 11 月 3 日')
p(f'本次用四块实体开发板验证集中点名、分时回复和两跳转发。正式完成 {len(rs)} 组实验，每组收集 100,000 条四字节数据，共 {sum(r["target"] for r in rs):,} 条；另外完成短样本功能检查和节点暂时掉线测试。')
p(f'逐个点名收集三个节点平均耗时 {ms(ind["round_mean_us"])} ms。分时回复在本次扫描中表现最好的配置为相邻回复间隔 {136+best["guard_us"]} μs，平均耗时 {ms(best["round_mean_us"])} ms，最终数据到达率 {pct(best["pdr"])}。两跳聚合收集两个叶节点平均耗时 {ms(agg["round_mean_us"])} ms。')
h('实验要回答的问题')
p('第一，中心依次点名多个节点时，能否正确区分来源、收齐数据，并在一个节点暂时不回复时继续采集其他节点。第二，一次点名后安排多个节点分时回复，能节省多少控制开销，回复间隔缩短到哪里会增加丢包和重传。第三，叶节点通过中继上报是否可行，合并转发能节省多少实际时间。')
h('共同实验条件')
table(['项目','本次设置'],[['硬件','A、B 为 nRF52832；C、D 为 nRF52840；均连接 DW3000 系列 UWB'],['无线参数','信道 5；6.8 Mbps；64 符号前导码；关闭 STS'],['应用数据','每个节点每轮 4 字节；内容由实验号、轮号和节点号生成并校验'],['帧长度','控制帧 30 B；单条 DATA 34 B；两条聚合帧 38 B，均含 FCS'],['调度','首个回复延迟 1000 μs；星形最多尝试 5 次；轮末广播确认'],['计时','主控 1 MHz 定时器；整轮耗时含点名、回复、重试、确认及轮间等待'],['场地记录','使用用户当前四板摆放；本次未测量距离、朝向和金属遮挡尺寸']],[1.1,5.9])
p('每组 10 万条以原始应用数据计数。聚合包内包含两条数据，实际空口发射次数另行统计。使用相同数据量比较三种方式，避免把聚合造成的帧数减少误计为业务量减少。')
page('实验一 逐个点名与暂时掉线')
p('A 依次点名 B、C、D，被点名的节点回复一条数据；缺失时由 A 再次点名，达到尝试上限后继续。完成一轮后，A 广播本轮收到哪些节点。这个实验用于建立多节点采集的基准。')
a=ind['boards']['A'];table(['节点','应收条数','首次到达','最终到达','最终缺失'],[[x,f'{(ind["target"]+2-i)//3:,}',f'{a[f"node_first_{i+2}"]:,}',f'{a[f"node_unique_{i+2}"]:,}',a[f'node_missing_{i+2}']] for i,x in enumerate('BCD')],[.6,1.4,1.6,1.6,1.3])
table(['方式','最终到达率','平均 ms','P99 ms','整轮收齐率'],[statsrow('逐个点名',ind)],[1.3,1.5,1.3,1.3,1.6])
p(f'首次数据到达率为 {pct(ind["first_pdr"])}，中心发起 {a["retries"]:,} 次额外点名。平均值反映通常耗时，P99 表示约 99% 的完整轮次在该时间内结束；这里包含达到重试上限后结束的轮次。整轮收齐率单独统计三条数据是否全部到达。')
h('掉线功能检查')
f=fault['boards']['A'];table(['设置','B 最终收到','C 最终收到','D 最终收到','总缺失'],[['D 在轮号 100 至 119不回复',f['node_unique_2'],f['node_unique_3'],f['node_unique_4'],f['missing']]],[2.7,1.1,1.1,1.1,1.0])
p('该检查共 1,000 轮、3,000 条预期数据。D 连续 20 轮主动忽略请求，随后自动恢复。B、C 的收集结果用于判断故障是否拖住其他节点；D 的缺失数量用于核对重试上限和统计是否正确。这是协议故障注入，射频遮挡与移动造成的掉线需要另做实验。')
h('从调试得到的直接结论')
p('最初轮末确认后立即开始下一轮，短测试的首次数据到达率为 85.4%。增加 500 μs 轮间等待后，同类短测试提高到 99.83%，平均整轮耗时由 7.24 ms 降为 6.04 ms。当前程序需要给接收端处理确认并重新打开接收的时间；减少这段等待会把节省的时间花在重传上。正式实验统一采用调整后的时序。')
page('实验二 一次点名后分时回复')
p('A 广播一次点名，并给 B、C、D 安排顺序。三个节点按照收到点名的无线时间戳安排发送；A 收完后只对缺失节点追加单独点名。目的在于减少三次独立点名，同时测出接收程序能连续接住数据的最短间隔。')
p('表中的回复间隔是相邻节点计划发送时间戳的差。程序参数为 136 μs 加可调余量，六档分别为 136、186、236、386、636、1136 μs。它包含帧本身占用的时间，不能把这个数直接当作前一帧结束后的空闲时间。')
table(['回复间隔 μs','首次到达率','最终到达率','平均一轮 ms','P99 ms'],[[136+r['guard_us'],pct(r['first_pdr']),pct(r['pdr']),ms(r['round_mean_us']),q99(r)] for r in sorted(groups,key=lambda r:r['guard_us'])],[1.3,1.5,1.5,1.5,1.2])
d.add_picture(str(out/'分时回复间隔扫描.png'),width=Inches(6.9))
save=(1-best['round_mean_us']/ind['round_mean_us'])*100
p(f'以最终到达率优先、再比较平均耗时，本次选择 {136+best["guard_us"]} μs 回复间隔。相对逐个点名，平均整轮耗时变化为减少 {save:.1f}%。判断间隔是否合适，要同时看首次到达率、最终到达率和整轮耗时；间隔缩短后增加的补发也计入结果。')
p(f'实际全网发射总帧数从逐个点名的 {sum(b["tx_frames"] for b in ind["boards"].values()):,} 帧，变为所选分时配置的 {sum(b["tx_frames"] for b in best["boards"].values()):,} 帧。两组业务量同为 10 万条，这个差值包含点名减少和重传变化的共同效果。')
r386=lookup['group-3-guard250'];b386=r386['boards']['A']
p(f'386 μs 间隔下，B、C、D 首次收到的条数分别为 {b386["node_first_2"]:,}、{b386["node_first_3"]:,}、{b386["node_first_4"]:,}。结合较长间隔的结果，可判断当前连续接收时序已影响可靠性。进一步应记录接收完成、读取帧和重新开启接收三个时刻，定位需要压缩的处理步骤。')
p('本次每轮只有三个回复节点。下一步扩大每轮被点名的节点数，可以继续摊薄点名和确认开销；同时需要检查远端时钟漂移、同步误差和接收端连续处理能力。')
page('实验三 两跳转发与聚合')
p('采用 A 为中心、B 为中继、C 和 D 为叶节点的两跳结构。A 请求 B 收集数据，B 分别点名 C、D，再把数据发给 A。叶节点的数据帧目的地址为 B，A 只接受来源为 B 的转发数据，并校验原始节点号对应的内容。')
p('对照组由 A 直接点名 C、D。逐包转发组由 B 收到一条就转发一条；聚合组由 B 收到两条后合并成一个包发给 A。三组均上报 10 万条四字节原始数据，每个完整轮次包含 C、D 各一条。')
table(['方式','最终到达率','平均 ms','P99 ms','整轮收齐率'],[statsrow('直接收集 C D',direct),statsrow('B 逐包转发',forward),statsrow('B 合并转发',agg)],[1.5,1.4,1.3,1.3,1.5])
d.add_picture(str(out/'两跳转发与聚合比较.png'),width=Inches(6.9))
p(f'直连、逐包转发、聚合转发的最大整轮耗时分别为 {ms(direct["boards"]["A"]["round_max"])}、{ms(forward["boards"]["A"]["round_max"])}、{ms(agg["boards"]["A"]["round_max"])} ms；100 ms 内全部收齐的轮次比例分别为 {pct(direct["deadline_100ms"])}、{pct(forward["deadline_100ms"])}、{pct(agg["deadline_100ms"])}。')
p(f'合并转发相对逐包转发，平均整轮耗时减少 {(1-agg["round_mean_us"]/forward["round_mean_us"])*100:.1f}%。它节省 B 到 A 的重复发送开销；B 向两个叶节点采集数据的过程仍然存在，因此整轮提速幅度要看实测。')
p('中继收集完成后发送结束通知，中心当前最多等待 60 ms。结束通知漏收或整次请求失败会产生长等待。后续应按下游节点数量和剩余重试次数设置等待时间，再重复测量最大耗时与按时收齐率。')
p('树形重试分两层控制：B 对每个叶节点最多点名五次，A 最多向 B 发起五次收集请求。B 在同一轮缓存已收数据，A 再次请求时只补缺失内容。树形的首次到达指标表示首次收集请求期间到达，其中可能包含 B 的下游重试；与星形单次发送成功率分别解释。')
p('本组结果验证了固定两跳路径上的采集、转发、聚合和补发。当前四板处于同一实验场地，距离与遮挡未量化。下一步放置遮挡使 A 难以直接接收 C、D，再比较经 B 转发的改善程度，才能回答中继是否扩大了可用覆盖范围。')
page('用实测耗时估算节点数量')
p('导师提出过以 100 ms 为例反推节点数，也要求计算 200、300 个节点需要多久。本报告把 100 ms 用作比较预算。每个节点在一个采集周期内产生一条四字节数据。')
p('先把完整实验总耗时除以预期数据条数，得到当前配置平均每条数据消耗的时间。200、300 条所需时间按比例计算；100 ms 内的条数按完整小组计算，先取能完成的小组数，再乘每组节点数。这里保留小组点名、确认、重试和等待的平均代价。')
sel=[('逐个点名三节点',ind),('最佳分时回复三节点',best),('两跳逐包转发两叶节点',forward),('两跳合并转发两叶节点',agg)];tab=[]
for label,r in sel:
 u=r['boards']['A']['elapsed']/r['target'];tab.append([label,f'{u:.1f}',math.floor(100000/(u*r['mask'].bit_count()))*r['mask'].bit_count(),f'{200*u/1000:.1f}',f'{300*u/1000:.1f}'])
table(['按小组串行复制','每条 μs','100 ms 条数','200 条 ms','300 条 ms'],tab,[2.3,1.1,1.3,1.1,1.2])
p('这些数值是四节点实测后的串行时间预算推算。200、300 个实体节点的同步、管理和信道竞争尚需扩展实验；本次数据不包含这些额外开销。P99 仅报告真实小组轮次，不把小组 P99 直接乘成大网络 P99。')
p('此前双板实验采用连续发送和批量确认；本次采用节点点名与回复，并设置首个回复延迟 1000 μs。两组测量的通信流程不同。评估组网效率应使用本次完整采集时间，后续再分别压缩回复等待、控制帧数量和接收处理时间。')
h('达到 300 节点预算需要什么')
p('若采用 300 节点、100 ms 的比较目标，平均每个节点可分配 333.3 μs。这份时间必须容纳数据发送、点名摊销、接收准备、同步保护和补发。四字节载荷缩短了数据部分，多节点协议仍要支付控制和处理时间。')
p('优先扩大一次点名安排的节点数，减少每个节点分摊的控制帧；其次优化接收端读取与重新开启接收的路径，再缩短回复间隔。树形聚合用于减少上级链路的帧数，同信道各层仍需安排发送顺序，增加层数本身不会自动增加空口容量。')
h('下一步实验顺序')
p('先在固定摆放下重复最佳间隔与相邻两档，检查结果是否稳定；再增加一次点名的回复节点数，并记录每轮全部到齐的时间。随后加入金属遮挡，比较直接通信与中继通信。最后测试中继失效后的重新选路，测恢复时间和恢复期间丢失的数据。每一步只改变一项主要条件，保留上一组作为对照。')
page('数据核对与复现记录')
p('每条数据包含实验编号、轮号和来源校验信息。中心使用位图去重；正式组结束后检查“唯一收到数加最终缺失数等于 100,000”，并核对各节点计数之和、位图计数和整轮直方图总数。报告使用已结束的完整组，运行中的分时读取计数不参与最终计算。')
p('整轮时间从开始构造首个请求计到轮末确认和 500 μs 等待完成。直方图每档 25 μs，P99 按所在档的上界报告；最后一档为 102.375 ms 及以上。三节点组最后一轮只有一条数据，该轮计入数据总数和总耗时，不计入三个节点完整轮次的分布。')
p('一组 10 万条全部收到时，报告观测到达率 100%。这组样本用于验证当前配置可连续工作；五个九的长期可靠性需要更大样本、不同位置和重复实验支撑。节点暂时不回复的短测试与正式射频性能数据分开保存。')
h('文件与代码')
table(['文件','用途'],[['results.jsonl','所有完整组的计数、时延直方图、配置及固件摘要'],['formal-summary.json','正式组汇总及时间预算推算'],['*-received.bin','中心唯一接收位图，可重新统计收到的数据'],['experiment-manifest.json','硬件编号、参数与程序文件校验摘要'],['tested-source-and-firmware.zip','本次测试源代码、构建脚本和固件'],['*-before-fourboard-flash.bin 与 uicr.bin','四板实验开始前的程序与配置备份']],[3.2,3.8])
p('工程基于同学的 toolnail/UWB 仓库（github.com/toolnail/UWB，原始提交 79209d263fc536fbffd4c5af5b2e4c4b610eeedb），在独立的 nRF52832-Four 和 nRF52840-Four 目录实现。A、B、C、D 调试器编号依次为 JLINK_A、JLINK_B、JLINK_C、JLINK_D。')
p('D 板驱动 P1.08 低电平时观察到主控重启，本次按芯片唯一编号选择 UWB 软件复位，已完成初始化与收发验证。接线或硬件导致复位联动的具体原因尚未测量。所有正式组采用相同固件；每组开始前重启主控并重新初始化 UWB。')
p('收尾检查发现 D 板的两个 PSELRESET 字段为 0xFFFFFFFF，实验前备份为 0x00000012。已保留测试结束时的配置文件，并按备份恢复这两个字段。四板程序均与归档固件逐字节一致，当前板卡配置均与实验前备份一致；恢复后另做分时回复与两跳聚合短测试。该差异和恢复记录保存在 D-uicr-restoration.json。')
p('本次实验为组网协议可行性验证，使用模拟电芯数据。真实电芯采样、整包电池内传播、功耗、移动时重选父节点和数百实体节点扩展，分别作为后续实验任务。')
foot=sec.footer.paragraphs[0];foot.text='四节点 UWB 电芯组网可行性验证　2026 年 11 月 3 日　|　第 ';foot.runs[0].font.size=Pt(9)
for style in d.styles:
 for e in list(style.element.iter(qn('w:pBdr'))):e.getparent().remove(e)
field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');foot._p.append(field);foot.add_run(' 页').font.size=Pt(9);d.styles['Footer'].font.size=Pt(9)
path=Path('outputs/四节点UWB组网可行性实验报告.docx');d.save(path);print(path.resolve())
