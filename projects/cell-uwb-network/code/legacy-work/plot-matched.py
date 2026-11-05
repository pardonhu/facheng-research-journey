from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
font=FontProperties(fname='C:/Windows/Fonts/msyh.ttc')
plt.rcParams.update({'font.family':font.get_name(),'axes.unicode_minus':False,'font.size':11})
out=Path('outputs/ble-matched-study')
raw=json.loads((out/'hardware-summary.json').read_text());assert len(raw)==15
rs={r['name']:r for r in raw};md={(r['profile'],r['case']):r for r in json.loads((out/'model-capacity.json').read_text())}
fig,axes=plt.subplots(1,2,figsize=(12,5.3));x=np.arange(3)
for ax,agg,case,title in zip(axes,[1,10],['poll','poll_aggregate'],['逐条点名上报','十条合包后点名上报']):
    theoretical=[md[(f'UWB preamble {pre}',case)]['mean300_ms'] for pre in (128,64,32)]
    actual=[rs[f'p{pre}-m2-a{agg}']['cycle_mean_ms'] for pre in (128,64,32)]
    a=ax.bar(x-.19,theoretical,.36,label='150 μs 间隔时间预算',color='#A9BED2')
    b=ax.bar(x+.19,actual,.36,label='开发板实测',color='#2F668D')
    for bars in (a,b):ax.bar_label(bars,fmt='%.1f',padding=3,fontsize=10)
    ax.axhline(100,color='#AD582A',ls='--',lw=1.4,label='100 ms 目标')
    ax.set_title(title);ax.set_xticks(x,['128 符号','64 符号','32 符号']);ax.set_ylabel('收集 300 条数据的平均时间 / ms')
    ax.set_ylim(0,max(110,max(actual)*1.18));ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True)
    ax.spines[['top','right']].set_visible(False)
handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',ncol=3,bbox_to_anchor=(.5,.94),frameon=False)
fig.suptitle('前导码缩短与 300 条上报的时间预算',fontsize=16,y=.99)
fig.text(.5,.025,'每条 30 bit；POLL 与 DATA 各注入 10% 丢包；聚合数据已就绪，组内收集时间另计。',ha='center',fontsize=10)
fig.subplots_adjust(top=.80,bottom=.16,left=.07,right=.98,wspace=.22)
dest=Path('outputs/UWB前导码与300条上报耗时.png');fig.savefig(dest,dpi=180);print(dest)
