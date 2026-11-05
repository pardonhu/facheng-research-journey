from pathlib import Path
import json,sys,math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['font.size']=13
plt.rcParams['font.sans-serif']=['Microsoft YaHei'];plt.rcParams['axes.unicode_minus']=False
out=Path('outputs/four-board-study');rows=[json.loads(x) for x in (out/'results.jsonl').read_text().splitlines()];rows=[x for x in rows if x['formal']]
if sum(r['name'].startswith('group-3-guard') for r in rows)<6:raise SystemExit('waiting for six interval cases')
g=sorted([r for r in rows if r['name'].startswith('group-3-guard')],key=lambda r:r['guard_us'])
fig,ax=plt.subplots(1,2,figsize=(10,3.5),layout='constrained');x=[136+r['guard_us'] for r in g]
ax[0].plot(x,[r['first_pdr']*100 for r in g],'o-',label='首次数据到达率');ax[0].plot(x,[r['pdr']*100 for r in g],'s--',label='重传后到达率');ax[0].set(xlabel='相邻回复的计划发送间隔 / μs',ylabel='到达率 / %');ax[0].legend(fontsize=12)
ax[1].plot(x,[r['round_mean_us']/1000 for r in g],'o-',label='整轮平均');ax[1].plot(x,[r['round_p99']['upper_us']/1000 if r['round_p99']['upper_us'] else float('nan') for r in g],'s--',label='整轮 P99 上界');ax[1].set(xlabel='相邻回复的计划发送间隔 / μs',ylabel='收集三个节点耗时 / ms');ax[1].legend(fontsize=12)
for a in ax:a.grid(alpha=.2)
fig.savefig(out/'分时回复间隔扫描.png',dpi=180);plt.close(fig)
lookup={r['name']:r for r in rows};names=['direct-2-leaves','relay-forward-2','relay-aggregate-2'];
if any(n not in lookup for n in names):raise SystemExit(0)
rs=[lookup[n] for n in names]
fig,ax=plt.subplots(1,2,figsize=(10,3.4),layout='constrained');labels=['直接收集 C D','B 逐包转发','B 合并转发']
v=[r['round_mean_us']/1000 for r in rs];ax[0].bar(labels,v,color=['#6589ab','#acb7c0','#447c64']);ax[0].set(ylabel='每轮两个节点平均耗时 / ms')
for i,y in enumerate(v):ax[0].text(i,y,f'{y:.3f}',ha='center',va='bottom')
v=[sum(b['tx_data'] for b in r['boards'].values())/r['target'] for r in rs];ax[1].bar(labels,v,color=['#6589ab','#acb7c0','#447c64']);ax[1].set(ylabel='每条数据对应的全网 DATA 发射次数')
for i,y in enumerate(v):ax[1].text(i,y,f'{y:.3f}',ha='center',va='bottom')
for a in ax:a.set_ylim(0,a.get_ylim()[1]*1.15);a.grid(axis='y',alpha=.2);a.set_axisbelow(True)
fig.savefig(out/'两跳转发与聚合比较.png',dpi=180);plt.close(fig)
print('charts saved')
