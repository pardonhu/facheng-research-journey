from pathlib import Path
root=Path(__file__).resolve().parent.parent
p=root/'outputs/当前组网报告配图/plot_current.py';s=p.read_text(encoding='utf-8')
a=s.index('# Manufacturer frame field order');b=s.index('# Current packet layout',a)
s=s[:a]+'''# Supported physical field lengths and the settings used by the saved measurements.
fig,ax=plt.subplots(figsize=(13,3));ax.set(xlim=(0,13),ylim=(0,3));ax.axis('off')
for x,w,t in [(.15,3.1,'前导码\\n可选32、64、128… symbol\\n本次64 symbol，65.13 μs'),(3.25,3.0,'帧起始定界符\\n可选8或16 symbol\\n本次8 symbol，8.14 μs'),(6.25,2.9,'物理层帧头\\n长度21 symbol\\n本次21.54 μs'),(9.15,3.7,'数据帧＋纠错编码冗余\\n本次272 bit＋48 bit\\n41.03 μs')]:box(ax,x,.95,w,1.5,t,fs=10.5)
arrow(ax,(.15,.65),(12.85,.65));ax.text(6.5,.25,'发送顺序',ha='center');fig.tight_layout();save(fig,'01-厂家帧结构')
'''+s[b:];p.write_text(s,encoding='utf-8')
p=root/'work/finalize-research-report.py';s=p.read_text(encoding='utf-8')
a=s.index('图1. DW3000');b=s.index('\n\n',a)
s=s[:a]+'''图1. DW3000所用数据帧模式的字段顺序、芯片支持的长度及本次取值。前导码与帧起始定界符的长度可配置；物理层帧头为21 symbol，其发送速率可配置；数据帧长度由应用决定，纠错编码由芯片生成。本次关闭安全时间戳序列，使用标称脉冲重复频率64 MHz、数据速率6.8 Mbps和标准物理层帧头速率。图中本次各部分时长合计约135.84 μs，宽度为示意。长度与时序依据[DW3000数据手册第4.4～4.5节](https://www.mouser.com/catalog/specsheets/Qorvo_DW3000.pdf)，可选配置依据[Qorvo驱动API指南的dwt_configure](https://forum.qorvo.com/uploads/short-url/xD3TlXKvkujjdUaJWXv2b4E7GQN.pdf)。'''+s[b:]
a=s.index('| 无线发送组成 |');b=s.index('### 2.2 单帧',a)
s=s[:a]+'''**厂家定义编码格式和可选档位，实验程序选择具体参数。** 下表列明本次取值及修改权限。

| 项目 | 本次取值 | 能否修改、修改范围 | 来源 |
|---|---|---|---|
| 前导码长度 | 64 symbol，65.13 μs | 可配置，例如32、64、128、256、512、1024、1536、2048、4096 symbol | 芯片支持的长度档位，本实验选64 |
| 帧起始定界符 | Qorvo 8 symbol，8.14 μs | 可选择芯片支持的8或16 symbol序列格式 | 芯片配置项 |
| 物理层帧头 | 21 symbol，21.54 μs | 长度由所用格式定义；发送速率可选择标准速率或数据速率，时长随之变化 | 芯片编码格式及配置项 |
| 标准短地址帧头 | 72 bit | 沿用本次短地址格式时保持该长度；改变地址模式需同步修改协议 | IEEE 802.15.4格式，厂家示例采用 |
| 实验管理字段 | 152 bit | 可删除或重新设计；本轮重测采用删除后的格式 | 本实验自定义 |
| 电芯数据 | 每条32 bit | 应用可修改；本轮统一32 bit | 用户指定 |
| 帧校验 | 16 bit | 启用时长度固定；芯片提供关闭生成与校验的接口，本轮保留 | 芯片校验功能 |
| 纠错编码冗余 | 本次增加48 bit | 所用编码格式下，每个最多330 bit的数据块增加48 bit；由帧长自动决定 | 芯片编码规则 |

物理层字段、编码规则和时长依据[DW3000数据手册表18及第4.5节](https://www.mouser.com/catalog/specsheets/Qorvo_DW3000.pdf)；前导码、定界符、物理层帧头速率和校验开关依据[Qorvo驱动API指南](https://forum.qorvo.com/uploads/short-url/xD3TlXKvkujjdUaJWXv2b4E7GQN.pdf)。72 bit短地址帧头依据[Qorvo数据发送示例](https://github.com/toolnail/UWB/blob/main/DW3_QM33_SDK_1.1.1/Drivers/API/Src/examples/ex_07a_ack_data_tx/ack_data_tx.c)。

**前导码symbol表示一段已知脉冲序列；前导码长度表示该序列的重复次数。** 当前每个前导码symbol约1.01763 μs。按6.8 Mbps参考速率，可将其占用时间折算为等效bit数：

等效bit数 = 前导码长度 × 1.01763 μs/symbol × 6.8 bit/μs。

| 前导码长度 | 持续时间（μs） | 按6.8 Mbps折算的等效bit数 |
|---:|---:|---:|
| 32 symbol | 32.56 | 221.4 |
| 64 symbol | 65.13 | 442.9 |
| 128 symbol | 130.26 | 885.7 |

等效bit数表示相同发送时间在6.8 Mbps下对应的数据量，用于比较时间开销。前导码本身发送已知同步序列。数据字段长度统一标bit，前导码标symbol和μs。

'''+s[b:]
p.write_text(s,encoding='utf-8')
