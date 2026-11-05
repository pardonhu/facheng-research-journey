from pathlib import Path
import re
root=Path(__file__).resolve().parent.parent
p=root/'outputs/当前组网报告配图/plot_current.py';s=p.read_text(encoding='utf-8')
s=s.replace("'相邻发包起始间隔\\nΔt₄ − Δt₂'", "'相邻发包起始间隔\\n'+r'$\Delta t_4-\Delta t_2$'")
a=s.index('# Latest capacity budget.');b=s.index('# Star topology:',a)
s=s[:a]+s[b:]
p.write_text(s,encoding='utf-8')
archive=root/'work/已撤下的容量推算图';archive.mkdir(exist_ok=True)
for ext in ('png','svg'):
 p=root/f'outputs/当前组网报告配图/09-节点容量推算.{ext}'
 if p.exists():p.replace(archive/p.name)
p=root/'work/finalize-research-report.py';s=p.read_text(encoding='utf-8')
s=s.replace('回复间隔','相邻发包起始间隔')
s=re.sub(r'(\d+)个符号',r'\1 symbol',s)
s=s.replace('由芯片定义的符号数','由芯片定义的symbol数')
s=s.replace('图1先给出厂家规定的字段顺序','图1先给出所用物理层格式的字段顺序')
p.write_text(s,encoding='utf-8')
p=root/'work/check-and-package-current-report.py';s=p.read_text(encoding='utf-8')
s=s.replace("assert '152 bit自定义实验管理字段' in main", "assert '152 bit实验管理字段由本实验程序自行添加' in main\nassert '100 ms容量 = k' in main\nassert '帧间隔500.165、350.165 μs' in main\nassert '附录A' not in main")
p.write_text(s,encoding='utf-8')
p=root/'AGENTS.md';s=p.read_text(encoding='utf-8').replace('节点容量结论待常规120 bit数据帧重测后更新。','现有帧结构下的容量可按实测小分组流程推算，明确分组和平均耗时假设；120 bit帧重测后另行更新。')
p.write_text(s,encoding='utf-8')
