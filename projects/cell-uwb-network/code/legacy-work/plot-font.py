from pathlib import Path
p=Path('work/plot-four.py');s=p.read_text(encoding='utf8').replace("plt.rcParams['font.sans-serif']", "plt.rcParams['font.size']=13\nplt.rcParams['font.sans-serif']").replace('fontsize=9','fontsize=12');p.write_text(s,encoding='utf8')
