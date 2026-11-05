from pathlib import Path
import json,re,zipfile
root=Path('outputs').resolve();rows=json.loads((root/'broadcast-tree-study/summary.json').read_text());assert len(rows)==4
ref=rows[0];best=next(r for r in rows if r['name']=='broadcast-slot486')
p=root/'电芯UWB组网两日实验总报告.md';s=p.read_text(encoding='utf-8')
assert '## 9 补充实验' not in s
first=s.index('\n');s=s[:first+1]+'\n> 更新：一次广播、叶节点定时回复、缺包补发的四板对照已完成，见第9项。第1～6项保留此前实验配置与结果。\n'+s[first+1:]
add=f'''## 9 补充实验：一次广播代替逐个点名，完整两跳时间减少{(1-best['mean_ms']/ref['mean_ms'])*100:.1f}%

每组五万条原始电芯数据。本轮同版程序重测轮询为{ref['mean_ms']:.3f} ms/两个电芯，改成广播后按486 μs间隔回复，为{best['mean_ms']:.3f} ms，全部五万条收到。中继收集时间从{ref['collection_ms']:.3f} ms降到{best['collection_ms']:.3f} ms，合包及其他控制等待基本保持不变。

中继测得的两包到达间隔偏差为{best['pair_min_ns']}～{best['pair_max_ns']} ns；这是每轮广播重新提供时间起点、两个叶节点在约1.3 ms内回复的结果。当前瓶颈在接收处理：386 μs间隔短测需要补发第二包，486 μs通过长测。中继读包、校验并恢复接收约需302～303 μs。

另测D每十轮故意漏一次首发，补发后五万条全部收到。各组参数来源、初次收到与补发后的区别、完整图表见[广播定时回复与轮询全过程对照](广播定时回复与轮询全过程对照.md)。按每组两个电芯、同信道串行，优化后的200条平均预算{best['window200']['mean_ms']:.1f} ms，300条{best['window300']['mean_ms']:.1f} ms；距离100 ms目标仍需继续减少控制与等待。

'''
s=s.replace('## 向老师汇报的简短版本',add+'## 向老师汇报的简短版本（原两日实验）')
p.write_text(s,encoding='utf-8')
files=set();pending=[p]
while pending:
 q=pending.pop()
 if q in files:continue
 assert q.is_file(),q;files.add(q)
 if q.suffix=='.md':
  for link in re.findall(r'\]\(([^)]+)\)',q.read_text(encoding='utf-8')):
   if link.startswith(('https://','http://','#')):continue
   v=(q.parent/link.split('#')[0]).resolve();assert v.is_relative_to(root);pending.append(v)
files.update(q for q in (root/'报告配图').iterdir() if q.is_file())
files.update([root/'ble-matched-study/hardware-summary.json',root/'tree-end-to-end-study/summary.json'])
with zipfile.ZipFile(root/'电芯UWB组网两日实验总报告与配图.zip','w',zipfile.ZIP_DEFLATED) as z:
 for q in sorted(files):z.write(q,q.relative_to(root))
print('Updated main report and portable report archive',len(files))
