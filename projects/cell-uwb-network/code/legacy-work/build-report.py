from pathlib import Path
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import json,collections
root=Path.cwd();d=Document();sec=d.sections[0];sec.page_width=Inches(8.5);sec.page_height=Inches(11);sec.top_margin=sec.bottom_margin=Inches(.65);sec.left_margin=sec.right_margin=Inches(.7)
for name in ('Normal','Title','Heading 1','Heading 2'):
 s=d.styles[name];s.font.name='Microsoft YaHei';s._element.rPr.rFonts.set(qn('w:eastAsia'),'Microsoft YaHei');s.font.color.rgb=RGBColor(0,0,0)
d.styles['Normal'].font.size=Pt(10.5);d.styles['Normal'].paragraph_format.space_after=Pt(6);d.styles['Normal'].paragraph_format.line_spacing=1.1
d.styles['Title'].font.size=Pt(23);d.styles['Heading 1'].font.size=Pt(16);d.styles['Heading 2'].font.size=Pt(12)
def p(s):d.add_paragraph(s)
def h(s):d.add_heading(s,1)
def pageh(s):
 q=d.add_heading(s,1);q.paragraph_format.page_break_before=True
def table(headers,rows):
 t=d.add_table(rows=1,cols=len(headers));t.autofit=True
 for i,x in enumerate(headers):t.rows[0].cells[i].text=str(x)
 rep=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(rep)
 for row in rows:
  for c,x in zip(t.add_row().cells,row):c.text=str(x)
 for ri,row in enumerate(t.rows):
  for c in row.cells:
   tc=c._tc.get_or_add_tcPr(); borders=OxmlElement('w:tcBorders')
   for edge in ('top','left','bottom','right'):
    el=OxmlElement('w:'+edge);el.set(qn('w:val'),'single');el.set(qn('w:sz'),'4');el.set(qn('w:color'),'D9D9D9');borders.append(el)
   tc.append(borders);shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'DCE6F1' if ri==0 else ('F4F6F8' if ri%2==0 else 'FFFFFF'));tc.append(shade)
   for para in c.paragraphs:
    para.paragraph_format.space_after=Pt(4);para.paragraph_format.space_before=Pt(4)
    for run in para.runs:run.font.size=Pt(9);run.bold=ri==0
 return t
matrix=json.loads((root/'outputs/broadcast-matrix-summary.json').read_text());mp=root/'outputs/100k-provisional-runs/results.jsonl';million=[json.loads(x) for x in mp.read_text().splitlines()] if mp.exists() else []
d.add_heading('电芯级 UWB 通信实验阶段汇报',0)
p('汇报准备日期 2026 年 11 月 3 日　｜　实验平台 PCA10040 与 DWM3000EVB')
p('本次为位置尚未固定的探索性摸底，不能作为严格控制位置条件的性能对照。本次实验围绕导师提出的单信道时间预算展开：缩短包间等待，测量实际服务时间，并估算 100 ms 内可安排的上报次数。同时验证广播地址与网络过滤，扩大样本观察可靠性。当前只有两个物理节点，尚未验证 200 或 300 节点组网。')
h('主要发现')
p('已完成 197 轮万包广播扫描，共 1,970,000 包。位置未固定的历史扫描中，信道 5 各配置的合计接收成功率为 99.8775%—99.9518%，信道 9 为 98.7725%—99.4281%。位置未固定构成混杂因素，该差异必须在固定位置、控制距离并随机化顺序后复测，不能直接归为信道的固有优劣。')
p('缩短主动等待可以提高发送速率，但等待为零仍存在空口与软件处理开销。此前 32 字节测试帧、128 符号前导码的间隔扫描中，平均每包约 429 μs，对应 300 次连续发送约 129 ms。该值属于当前实现，不能视作 UWB 物理极限。')
h('单轮十万包摸底实验')
if million:
 table(['轮次与方向','参数','发送与唯一接收','接收率'],[[f"{r['run']}  A→B" if r['tx_serial']=='JLINK_A' else f"{r['run']}  B→A",f"Ch{r['channel']} / {r['frame_bytes']} B / {r['post_tx_gap_us']} μs",f"{r['tx']['tx']:,} / {r['rx']['rx']:,}",f"{r['pdr']*100:.4f}%"] for r in million[:2]])
 p('表中仅列已结束并冻结统计的完整轮次；每轮目标为 100,000 个发送完成事件。接收成功数按实验编号和序号去重，不含主动重传。运行中计数分时读取，不用于计算最终丢包率。')
else:p('首轮正在进行，定稿时补入完整轮次结果。当前不宣称十万包单轮已完成。')
h('实验条件')
p('两块 PCA10040 主控分别连接 DWM3000EVB，主控序列号 A 为 JLINK_A，B 为 JLINK_B。物理层使用 6.8 Mbps、128 符号前导码，关闭 STS；SPI 初始化 1 MHz，收发 8 MHz。')
p('当前轮询接收，未启用 ACK 或重传。帧长不含 2 字节 FCS；位置尚未固定，距离未测量。统计经 SWD 读取，RTT 使用非阻塞输出。表中选取最先完成的两轮十万包结果，其他轮次保留在原始记录中。')
pageh('单信道上报时间预算')
p('导师的要求可归纳为：先测最小可用包间隔，再反算容量。200 次上报在 100 ms 内完成，平均每次预算为 500 μs；300 次则为 333.3 μs。预算必须包含发送、处理、同步、保护时间和重传，不能仅使用配置的等待值。')
table(['32 B 帧后等待','实测平均耗时','100 ms 次数估算','200 次估算','300 次估算'],[['500 μs','927 μs','107','185 ms','278 ms'],['150 μs','577 μs','173','115 ms','173 ms'],['0 μs','429 μs','233','86 ms','129 ms']])
p('上表来自最初两方向各 1,000 包的间隔扫描，含 9 字节实验头，不等同于后续含 MAC 地址的广播帧。等待定义为上一包 TXFRS 完成后至准备下一包前的主动延迟；0 μs 仅代表没有主动等待。')
d.add_picture(str(root/'outputs/advisor-gap-results.png'),width=Inches(6.4))
p('图 1　两节点单信道时间扫描。红线为 300 次上报在 100 ms 内完成的平均预算。曲线使用主控计时器测得的总发送时间除以实际发送数，包含软件与 SPI 开销，并非精确空口起始间隔。')
h('如何解释容量')
p('次数估算取 floor(100000 / 平均每包微秒数)。200 或 300 次耗时按平均服务时间线性外推，只表示理想串行服务预算，不保证所有包成功送达，也没有纳入多节点切换、同步误差、保护间隔或重传。不能将该估算写成已验证的节点容量。')
p('下一步优先比较 64 与 128 符号前导码、减少每包 SPI 操作和接收重启开销。改变前导码可能影响接收可靠性，必须同时报告时间与成功率。射频带宽、物理层速率和应用有效吞吐不是同一指标；录音中的 KB/s 与 kb/s 需要核实。')
pageh('广播可靠性与地址过滤')
d.add_picture(str(root/'outputs/broadcast-matrix.png'),width=Inches(6.2))
p('图 2　197 轮万包广播测试。点为各配置合计接收率，误差线为逐轮最小值和最大值，不是置信区间。各配置包含两方向和重复轮次；测试顺序固定，未做随机化，环境随时间变化可能影响对比。')
table(['对照条件','发送','唯一接收','解释'],[['同 PAN 广播','3,000','2,998','广播接收正常'],['匹配 B 地址的单播','3,000','2,998','地址匹配正常'],['发往其他地址的单播','3,000','0','硬件过滤符合预期'],['不同 PAN 的广播','3,000','0','网络过滤符合预期'],['B 改地址后接收广播','3,000','2,999','广播不依赖固定目的单播地址']])
p('MAC 使用 16 位短地址数据帧，目的广播地址为 0xFFFF，PAN 为 0x1234。启用硬件帧过滤，不是通过混杂接收模式证明广播。上述每项三轮、每轮 1,000 包，属于功能对照，不属于后续单轮十万包摸底实验。')
p('两个负对照中的过滤拒绝计入旧版 errors 字段，不能作为无线随机丢包统计。广播长样本的应用数据为帧长减 17 字节，包括 9 字节 MAC 头和 8 字节实验头；32 字节帧对应 15 字节可用测试载荷。')
h('一对多的验证边界')
p('当前只验证 A 发广播、B 能接收。改变 B 地址是依次测试不同地址，不能模拟两个接收器同时存在。加入 C 后，应对齐实验编号和序号，分别报告 B 接收率、C 接收率、两者同时成功的比例和共同丢包概率；反馈需调度，避免多个接收器同时 ACK。')
pageh('统计方法和可信范围')
p('发送分母只计硬件 TXFRS 确认完成的帧。接收端校验帧长度、实验编号、序号和确定性内容，并检查 FCS。完整轮次在发送结束后留出接收余量，再停止接收端读取最终计数。中断轮次另存，不混入完整轮次汇总。')
p('接收固件使用 65,536 序号滑动位图，在 nRF52832 的 64 KB RAM 内完成去重。窗口内重复不重复计数；超过窗口的异常旧帧归入 bad，不作为新的成功接收。程序验证了窗口回绕、缺包、重复与窗口内乱序。该方案适用于本次单发送端顺序发送测试，不等同于任意乱序网络的全局百万位图。')
p('本次没有记录完整逐包空口时间戳、丢包突发长度、CIR、RSSI 校准或电流波形。CPU 轮询、SPI 传输、接收重启和调试读数均可能影响性能，因此这是系统实现的实测，不能解释成纯射频信道误码率。未进行独立功率、频谱或计时器频率校准。')
h('下一阶段实验')
table(['优先级','实验','要回答的问题'],[['1','固定位置后重复与换向','长期丢包是否稳定，是否具有方向差异'],['2','前导码和软件路径优化','300 次上报能否接近 100 ms，同时保持可靠性'],['3','ACK 与有限重传和掉线恢复','最终可靠性、尾时延和恢复时间的代价'],['4','至少三个实体节点的调度','广播共同成功率和多节点反馈冲突'],['5','金属板 空盒 模拟电芯排列','布置、遮挡和多径造成的失效规律'],['6','传感采集与电流测量','每次可靠上报的能耗和采样开销']])
h('建议向导师汇报的结论')
p('我们已经完成主控移植、双向收发、广播与地址过滤验证，并建立了可重复的单信道参数扫描。等待时间减少可以提高吞吐，但当前软件与空口开销使 300 次上报的 100 ms 目标仍有缺口。下一步要在可靠性约束下缩短服务时间，再用第三个节点验证调度与广播共同成功率。')
p('可复现依据：toolnail/UWB，提交 79209d263fc536fbffd4c5af5b2e4c4b610eeedb；独立 nRF52832-Broadcast 工程；原始逐轮 JSONL、固件、构建日志和补丁随实验目录保存。两块板物理距离与朝向尚未量化，复现实验需补录。')
footer=sec.footer.paragraphs[0];footer.text='电芯级 UWB 实验记录　|　2026 年 11 月 3 日';footer.runs[0].font.size=Pt(9)
for style in d.styles:
 for border in list(style.element.iter(qn('w:pBdr'))):border.getparent().remove(border)
for border in list(d.element.iter(qn('w:pBdr'))):border.getparent().remove(border)
path=root/'outputs/UWB实验阶段汇报.docx';d.save(path);print(path)
