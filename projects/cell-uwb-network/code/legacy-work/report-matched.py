from pathlib import Path
import json,math
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
out=Path('outputs/ble-matched-study')
rs=json.loads((out/'hardware-summary.json').read_text());assert len(rs)==15
lookup={r['name']:r for r in rs}
model=json.loads((out/'model-capacity.json').read_text())
md={(r['profile'],r['case']):r for r in model}
d=Document();s=d.sections[0];s.page_width=Inches(8.5);s.page_height=Inches(11)
for border in list(d.styles.element.iter(qn('w:pBdr'))):border.getparent().remove(border)
s.top_margin=s.bottom_margin=Inches(.6);s.left_margin=s.right_margin=Inches(.65)
for name,size in [('Normal',11),('Title',22),('Heading 1',15),('Heading 2',12)]:
    st=d.styles[name];st.font.name='Microsoft YaHei';st._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'Microsoft YaHei');st.font.size=Pt(size);st.font.color.rgb=RGBColor(0,0,0)
d.styles['Normal'].paragraph_format.space_after=Pt(6);d.styles['Normal'].paragraph_format.line_spacing=Pt(15)
for style in ('Title','Heading 1','Heading 2'):
    d.styles[style].paragraph_format.line_spacing=Pt(27 if style=='Title' else 19)
    d.styles[style].paragraph_format.space_before=Pt(9)
    d.styles[style].paragraph_format.space_after=Pt(6)
def p(t):d.add_paragraph(t)
def h(t):d.add_heading(t,1)
def page(t):
    heading=d.add_heading(t,1);heading.paragraph_format.page_break_before=True
def table(headers,rows,widths):
    widths=[7.2*x/sum(widths) for x in widths];t=d.add_table(rows=1,cols=len(headers));t.autofit=False
    for i,w in enumerate(widths):t.columns[i].width=Inches(w)
    for c,v in zip(t.rows[0].cells,headers):c.text=str(v)
    repeat=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(repeat)
    for row in rows:
        for c,v in zip(t.add_row().cells,row):c.text=str(v)
    for ri,row in enumerate(t.rows):
        nr=OxmlElement('w:cantSplit');row._tr.get_or_add_trPr().append(nr)
        for ci,c in enumerate(row.cells):
            c.width=Inches(widths[ci]);c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            pr=c._tc.get_or_add_tcPr();b=OxmlElement('w:tcBorders')
            for edge in ('top','left','bottom','right'):
                e=OxmlElement('w:'+edge);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');b.append(e)
            pr.append(b);sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'DCE6F1' if ri==0 else 'FFFFFF');pr.append(sh)
            for para in c.paragraphs:
                para.paragraph_format.space_before=Pt(2);para.paragraph_format.space_after=Pt(2);para.paragraph_format.line_spacing=Pt(12.5)
                if ci:para.alignment=WD_ALIGN_PARAGRAPH.CENTER
                for run in para.runs:run.font.size=Pt(9);run.bold=ri==0
    gap=d.add_paragraph();gap.paragraph_format.space_before=Pt(0);gap.paragraph_format.space_after=Pt(0);gap.paragraph_format.line_spacing=Pt(3)
    return t
def f(x):return f'{x:.3f}'
def pct(x):return f'{100*x:.3f}%'
a=lookup['p64-m2-a1'];b=lookup['p32-m2-a1'];c=lookup['p64-m2-a10'];e=lookup['p32-m2-a10']
d.add_heading('UWB 前导码优化与节点容量对照实验',0)
p('导师汇报材料　2026 年 11 月 4 日')
p(f'本次按蓝牙参考中的五种收发规则，比较 UWB 的 128、64、32 符号前导码。每组测试 50,000 个原始 DATA 包，共 15 组。关注的问题是：在每个节点上报 30 bit 数据时，100 ms 能容纳多少条上报，以及 300 条数据能否按时收齐。')
p(f'当前 64 符号配置下，逐条 POLL 收齐 300 条平均需要 {f(a["cycle_mean_ms"])} ms；32 符号时需要 {f(b["cycle_mean_ms"])} ms。十条合包后，两档分别为 {f(c["cycle_mean_ms"])} ms 和 {f(e["cycle_mean_ms"])} ms。聚合能够大幅减少帧数；缩短前导码的效果还受主控处理和接收响应速度影响。')
h('实验怎样对应老师的问题')
p('用 A 板作为中心、B 板作为数据源连续执行收发，每 300 条记录划成一个采集周期，统计周期耗时和是否收齐。每条记录对应一个逻辑节点的一次上报。该方法测量链路的调度时间预算；300 个实体节点的同步、入网和空间干扰仍需多节点实验验证。')
table(['条件','本次设置'],[
['前导码','128 为历史基准；64 为当前配置；32 为历史基准的 1/4'],
['无线与主控','DW3000，信道 5，6.8 Mbps，PRF 64，STS 关闭；A/B 均为 nRF52832'],
['每条业务数据','30 bit；单条按 4 B 携带，十条按位打包为 38 B'],
['帧长度','POLL 30 B；单条 DATA 34 B；十条 DATA 68 B；均包含 FCS'],
['间隔与丢包','请求 IFS 150 μs；固定五次及 POLL 模式注入 10% 独立丢包'],
['样本','每组 50,000 个原始包；补发另计；聚合组含 500,000 条记录']],[1.2,6])
h('固定空口开销减少了多少')
table(['前导码符号','30 B 控制帧 μs','34 B 数据帧 μs','68 B 聚合帧 μs'],[[pre,f(lookup[f'p{pre}-m0-a1']['poll_air_us']),f(lookup[f'p{pre}-m0-a1']['air_us']),f(lookup[f'p{pre}-m0-a10']['air_us'])] for pre in (128,64,32)],[1.2,2,2,2])
p('128→32 符号减少约 97.69 μs 空口时间。30 B 控制帧从 196.86 降至 99.17 μs，降低约 49.6%。64→32 符号减少约 32.56 μs。表中时间由芯片帧格式计算，主控处理耗时另外计入实测结果。')
page('按蓝牙同学规则计算的对照结果')
p('根据同学给出的数值重建收发规则，再把每帧空口时间换成各档 UWB 的时间。采用能重现其 155.4 ms 结果的假设：IFS 为 150 μs；一台中心依次收集；POLL 和 DATA 各以 10% 概率独立丢失；失败后再次点名。每次尝试成功概率为 0.9×0.9＝0.81。模拟运行 50,000 个 300 条采集周期。蓝牙部分为模型复现，UWB 部分另有实板验证。')
profiles=['BLE listed 60/196 us','UWB preamble 128','UWB preamble 64','UWB preamble 32']
cases=[('single','单次发送'),('aggregate','十条合包'),('repeat5','每条固定发五次'),('poll','逐条 POLL'),('poll_aggregate','十条合包 POLL')]
table(['方式','蓝牙 ms','UWB 128 ms','UWB 64 ms','UWB 32 ms'],[[label]+[f(md[(pr,case)]['mean300_ms']) for pr in profiles] for case,label in cases],[2,1.3,1.3,1.3,1.3])
p('表格为 300 条数据的平均时间预算。单次发送按理想无丢包计算；固定五次按每次 DATA 丢包率 10% 计算；POLL 持续补发直到收齐。最后一帧结束后不再计 150 μs，因而单发蓝牙为 62.85 ms，按每帧完整时隙计则为 63 ms。')
h('100 ms 内的理论容量')
table(['配置','逐条 POLL\n平均预算','逐条 POLL\nP99 预算','十条合包 POLL\n平均预算','十条合包 POLL\nP99 预算'],[[label,md[(pr,'poll')]['capacity_by_mean'],md[(pr,'poll')]['capacity_by_p99_simulation'],md[(pr,'poll_aggregate')]['capacity_by_mean'],md[(pr,'poll_aggregate')]['capacity_by_p99_simulation']] for pr,label in zip(profiles,['蓝牙','UWB 128','UWB 64','UWB 32'])],[1.2,1.4,1.4,1.6,1.6])
p('单位为每轮上报的逻辑节点数。平均预算允许部分轮次超过 100 ms；P99 预算用模拟中约 99% 轮次完成的条件估算，适合与期限要求一起讨论。聚合列假设十条数据已在发送端准备好。')
h('原表中哪些数值已经对上')
p('逐条 POLL：300÷0.81×420 μs－150 μs＝155.406 ms，与原表 155.404 ms 一致到模拟误差范围。十条合包：按表中 DATA 196 μs 得到 20.443 ms；把 DATA 换为 194 μs 得到 20.369 ms，与原表一致。本报告主表保留明确列出的 196 μs，另存 194 μs 重建结果。')
p('独立丢包率 10%、每条发送五次时，300 条全部成功的概率为 (1－0.1⁵)³⁰⁰＝99.7004%。原表的 92.84% 需要额外假设才能得到。原表 31.080 ms 的组内聚合过程缺少收集和并行规则，本次单列为待复现项。40 个信道的并行分配也未计入容量倍增。')
page('开发板实际测得的容量')
p('以下时间包含主控组包、SPI 访问、无线收发、接收处理、等待及重试。本次固件逐包生成并校验测试内容，实测包含这些处理成本，三档使用相同代码。无确认组按自然链路丢包统计；另外两类加入 10% 丢包。POLL 每包最多尝试 32 次，等待回复超时设为 1000 μs。')
labels={(0,1):'单次单条',(0,10):'单次十条',(1,1):'单条发五次',(2,1):'POLL 单条',(2,10):'POLL 十条'}
table(['前导码','方式','300 条均值\nms','P99\nms','100 ms\n平均容量','整轮收齐率'],[[r['preamble'],labels[(r['mode'],r['aggregation'])],f(r['cycle_mean_ms']),f(r['p99_ms']),r['estimated_nodes_100ms'],pct(r['all_300_rate'])] for r in rs],[.7,1.45,1.15,1,1,1.2])
p('100 ms 平均容量＝100 ms÷每条数据的平均实测耗时，聚合模式按十条向下取整。该列是时间预算推算，最终到达率与整轮收齐率单独判断。单条组有 166 个完整 300 条周期，聚合组有 1666 个完整周期；末尾不足 300 条的周期不进入均值和 P99。')
p(f'64→32 符号时，逐条 POLL 的平均时间缩短 {(1-b["cycle_mean_ms"]/a["cycle_mean_ms"])*100:.2f}%；十条合包 POLL 的平均时间缩短 {(1-e["cycle_mean_ms"]/c["cycle_mean_ms"])*100:.2f}%。')
p('整轮收齐率要求一轮的 300 条全部收到，比单包到达率更贴近电芯采集需求。无确认模式即使耗时小于 100 ms，也可能整轮缺数据；POLL 通过重新点名补齐缺失。')
page('实际瓶颈与下一步验证')
h('150 微秒间隔在开发板上实现了吗')
single=[lookup[f'p{pre}-m0-a1'] for pre in (128,64,32)]
table(['前导码','实际发包\n周期 μs','数据空口\nμs','实际空闲\n间隔 μs','无补发单包\n到达率'],[[r['preamble'],f(r['actual_period_us']),f(r['air_us']),f(r['actual_ifs_us']),pct(r['final_pdr'])] for r in single],[.8,1.6,1.5,1.7,1.6])
p('实际发包周期由 DW3000 的发送时间戳测量；相同帧型下，周期减去整帧空口时间就是两帧之间的空闲间隔。当前组包、SPI 和状态查询耗时使多数延迟发送赶不上目标时刻，程序转为立即发送。150 μs 是请求值，实测空闲间隔见上表。')
p('因此，理论表回答空口和调度规则允许多少节点；实测表回答当前程序已经做到多少。前导码优化降低了空口时间，下一项主要优化应是缩短主控处理：提前准备数据、减少 SPI 往返、提高收发切换效率，并分别记录组包结束、发送启动和接收就绪时刻。')
p(f'无补发单条模式下，64 符号单包到达率为 {pct(single[1]["final_pdr"])}，32 符号为 {pct(single[2]["final_pdr"])}。缩短前导码后的自然丢包增加，会消耗一部分节省的时间，所以最终选型应比较补发后的整轮耗时。')
h('怎样判断电芯组网可行')
p(f'本次 64 符号十条聚合 POLL 的 300 条周期有 {pct(c["all_300_in_100ms"])} 在 100 ms 内全部收齐，32 符号为 {pct(e["all_300_in_100ms"])}。这些结果验证了聚合上行的时间预算。树形方案还需把组内采集、中心上行和补发的总和控制在 100 ms 内。')
p('下一轮用现有四板搭建中心—中继—两个叶节点，实测叶节点采集加中继聚合上报的全过程；再把每层耗时代入 200、300 节点的分组数量。保持本次业务量和丢包设定，分别检查平均时间、P99 和在 100 ms 内全部收齐的比例。')
h('数据怎样保证可以复查')
p('固件按实验号、序号和内容校验每包，记录接收位图、实际发射次数、人工丢弃计数和无线错误。原始数据保存在 results.jsonl，每组接收位图单独保存；硬件结果与模型结果分别存放。随机种子为 20261104，各前导码使用同一丢包判定规则。人工丢包与自然链路错误共同影响实测耗时。')
p('测试前保存 A/B 全部 Flash 和 UICR；本轮新增独立 Matched 工程，保留原四板代码。测试后比对固件与 UICR，并核对位图、分周期缺失数和包计数。C/D 本轮未烧录。')
p('空口时间来源：Qorvo DW3000 Datasheet v1.1，Table 18 和 Section 4.5。计算包含 SHR、21 符号 PHR、数据和每 330 bit 对应的 48 bit RS 校验。文档地址：https://www.mouser.com/catalog/specsheets/Qorvo_DW3000.pdf。蓝牙参考数值来自用户提供的实验表。')
footer=s.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
footer.add_run('UWB 容量验证  ');fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');footer._p.append(fld)
dest=Path('outputs/UWB前导码优化与蓝牙同规则容量对照.docx');d.save(dest);print(dest)
