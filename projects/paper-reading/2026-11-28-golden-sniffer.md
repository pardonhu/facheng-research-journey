# Golden Sniffer 的实验论证与比较范围

论文：Ivan Palamà 等，*Golden Sniffer: Low-Complexity 5G New Radio Signal Interception Exploiting Gold Sequences*，MobiCom 2026，DOI [10.1145/3795866.3796673](https://doi.org/10.1145/3795866.3796673)。[作者机构记录](https://iris.unipa.it/handle/10447/721055)核实正式出版；实际阅读[作者仓库全文](https://github.com/5G-GoldenSniffer/5G-GoldenSniffer/blob/main/docs/assets/golden-sniffer.pdf)。以下页码均为PDF页序。

本次读正文p1–13及附录A/B p14，p15–16用于核对参考文献。实际查看p11–12渲染页，重点为图7、表2及其正文、脚注。没有运行其5G接收程序。选择两个重点：**实验段落怎样逐步回答问题**，以及**比较数字与理论解释怎样取得可信度**。论文同时给出受控测试、现场观测、复杂度分析和外推耗时，适合练习分清每类证据能支持的判断。

## 论文卡

| 项目 | 本次保留的内容与位置 |
| --- | --- |
| 问题 | 被动5G测量缺少用户配置，控制信道盲解码的搜索量大。p1–5 |
| 缺口 | 依赖注册时信息或默认扰码配置的方法受观测时机、配置变化限制。§2–3 |
| 观察 | Gold序列及相关编码操作具有可利用的结构；未知量之间存在方程约束。§4.2–4.3 |
| 方法 | 相位恢复、二元域求解、候选剪枝与缓存配合，逐步得到配置和解码结果。§4 |
| 证据 | 受控平台提供基站日志真值；相同IQ采样用于比较；现场采样检查配置假设。§5 |
| 边界 | 正文原型离线运行；相位恢复依赖信道与信号质量，部分映射及多层数据传输尚未覆盖。§4.1、§5、§7、附录A/B |

## 原文怎样带读者进入实验

§4.5先把方法中的局部操作接回完整流程，§5再分别介绍可控制的平台与实际网络。这个安排让读者先知道系统要做什么，随后知道两组实验各能回答什么。借鉴到组网论文时，可以让实验开头承接方法承诺：排程改变了等待顺序，首先检查整批是否按期限收齐；再用逐包日志解释时间花在哪里。

§5.1把功能验证和应用分析分开。§5.2接着问解码是否可靠，再讨论噪声、配置、基线、传播条件和分项耗时。阅读时可以把每个小节的首句压成一个问题，并检查后面的图是否回答它。这样发现缺少哪项证据，比给每段添加连接词更有效。

### 从图中找决定结论的变化

p11图7把信号质量变化和解码率放在一起，正文按平台区、快速下降区和失效区组织解释。这种写法适合处理存在阈值的实验：挑出决策发生变化的区间，再说明阈值两侧系统行为的区别。改UWB实验时，可以关注首次丢包开始增加之后，补发是否使整批完成时间越过期限，避免逐个复述横轴取值。

实际页面中，图7同时绘制两类授权的柱状结果、总体连线及理论虚线，图例承担方法区分。横轴在低SNR区域较密，逐点读数需要放大。用于自己的图时，可按主要比较减少同图编码种类，保留拐点附近的可读刻度。双栏格式来自会议模板；同图放哪些序列、刻度和标签属于作者设计。

**核对发现。** 图7正文写出的SNR与百分数配对，与图中部分标注不一致。例如正文把88.7%对应到15.4 dB，图中88.7的标签对应16.5 dB。本记录只借鉴区间解释的组织方式，不从该处抄取精确阈值。后续改稿需核对数据表、图轴和正文配对，确定采用哪个版本。

### 表格、脚注和结论必须连读

p12表2把检测率与耗时并排，未支持的配置用N/A表示。基线耗时的单位为千秒，脚注说明只运行了30个扰码ID，再外推到完整ID空间；另一方法的数值为实测处理时间。阅读这张表时，应先辨认数字的形成方式，再解释差距。将N/A改成零检测率，或把外推倍率写成完整规模实测加速，都会改变证据含义。

用于自己的实验表，可把“测得耗时”和“按候选数外推的耗时”直接写进列名或紧邻表注。图表只需保留理解比较所需的条件；导致结论变化的条件要让读者在读数字时看见。

## 助手原创改稿练习

以下差例与改稿均为助手自拟，服务于实验写作训练；并非论文原句或作者稿件。

**自拟差例：**

> Our method is much faster and more robust than the baseline. Table X proves the effectiveness of the algorithm in all network settings. The unsupported cases further demonstrate the advantage of our design.

差例把耗时、可靠性、支持范围混成一个判断，也省略了外推条件。读者无法知道两组计算是否完整执行，以及结果来自哪些配置。

**完整英文改稿：**

> We first compare decoding on the same recorded inputs to separate receiver behavior from changes in the radio channel. Table X reports the detection rate and processing time for each supported configuration. The baseline runtime is extrapolated from a capped search, whereas the proposed receiver is timed over its complete processing pipeline; the table therefore distinguishes measured time from projected search cost. Configurations outside the baseline's supported set are listed separately. To locate the remaining computational bottleneck, we next measure the time spent in each stage of the proposed receiver.

修改后，首句交代比较为何使用相同输入，第二句指出读表对象，第三句把计时方式放在比较旁边，第四句交代支持范围，末句引出分项计时。这里借鉴的是论证顺序。实际改作者论文时，应根据当前数据替换对应条件，并保留原有主线。

**可用于UWB论文的原创衔接：**

> The batch-level comparison establishes whether the collection procedure meets the deadline. We next examine first-attempt reception and the time spent on recovery to explain the difference in completion time. These measurements use the same batch definition as the preceding comparison, so that a reduction in per-packet waiting can be related to its effect on the complete collection cycle.

这段是写法样例。只有已有日志提供相应统计时，才可以填入具体结果。

## 怎样检查理论解释的力度

§5.2使用块成功率曲线解释实测趋势，并引入估计的实现损失。这样的曲线可帮助解释形状。若同一组数据参与选择平移量，独立验证应在另外的输入或条件上进行；拟合后的贴合不能替代这一步。用于FastSET时，应交代参数来自训练、校准还是最终测试，避免把选择参数的结果同时作为验证结果。

§4.3由未知数和方程数讨论可解性。改写自己的数学论证时，还需核对秩。例如原创二元域模型

\[
y=Ax,\quad A=\begin{bmatrix}1&1\\0&0\\1&1\end{bmatrix},\quad y=(1,0,1)^T
\]

有三个方程、两个未知数，仍同时允许\(x=(1,0)^T\)和\(x=(0,1)^T\)。这只说明“方程更多”单独不足以保证唯一解；本次没有计算原论文实际生成矩阵的秩。写论文时，将计数、满秩条件和数值稳定性分别写清，读者才能判断信息是否充分。

## 后续改稿索引

| 维度／章节 | 触发问题 | 具体改法 | 适用范围 |
| --- | --- | --- | --- |
| 篇章／实验 | 各小节都以“我们进一步测试”开头 | 先写上一比较已经解决什么，再引出尚缺的解释；功能、可靠性、开销各有问题 | 沿用原实验主线，缺少统计时只标明所需证据 |
| 图文／结果 | 大倍率掩盖外推或不同支持范围 | 同处标明实测、外推、N/A的含义，再写比较结论 | 不能将未支持配置折算为零性能 |
| 数学／方法 | 用方程数替代可辨识性判断 | 核对未知量、矩阵秩及观测条件 | 计数和玩具反例不替代实际系统证明 |

本次未将上述练习应用到作者的私人稿件。公开代码仓库提供MATLAB实现；本次只查阅来源与文档，没有下载大型IQ数据集或执行空口采集。
