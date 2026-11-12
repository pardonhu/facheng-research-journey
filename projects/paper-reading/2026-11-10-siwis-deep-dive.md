# SiWiS 二次精读：从原文分析到可执行的改稿

这份补充回应对首轮阅读深度的追问。首轮完成了正文定向阅读、元数据和若干图表核对、标题及概述练习；本轮继续追踪信号模型、验证实验、指标定义、比较协议和图文设计。阅读的深度以这些可检查产物说明，不以篇数代表。本文是原论文的再次学习，不新增一篇收录计数。

来源为 Kunzhe Song、Qijun Wang、Shichen Zhang、Huacheng Zeng 的 *SiWiS: Fine-grained Human Detection Using Single WiFi Device*，MobiCom 2024。[DOI](https://doi.org/10.1145/3636534.3690703)；[作者公开全文](https://inss.egr.msu.edu/papers/song24_mobicom_siwis.pdf)。页码均按该 16 页 PDF 页序。下面的差例、英文改稿、计算和布局均为助手原创训练，未修改原论文或用户稿件。

## 1 原文分析：把模块列表追到设计原因

原文 §2.2–2.4（pp. 3–6）的解释可以按四个问题重组：

| 要解释的问题 | 原文依据 | 对写作的作用 |
| --- | --- | --- |
| 为什么搬到同一位置仍不够？ | 引言 p. 2 指出商用芯片缺少可用的时钟接口，外加独立振荡器仍带来偏差 | 先排除读者最容易想到的简单方案，再引出自混频 |
| 为什么接收直达信号？ | §2.3 的 RX0 接收本机发射信号，作为混频参考；其他天线接收回波 | 把器件名称转成它提供的信息及其作用 |
| 为什么只处理 L-LTF？ | §2.4.2 指出载荷变化妨碍稳定特征，L-LTF 提供固定波形；式 (5) 对相应样本求和 | 让预处理成为解决具体干扰的步骤 |
| 为什么还需要多天线和网络？ | 引理 2.1 的线性相位关系基于单个小尺寸运动物体；p. 6 再讨论复杂反射 | 先给简化模型的物理直觉，再交代人体场景的额外处理 |

这里最可迁移的写法，是把“组件叫什么”改成“它获得什么信息、消除哪个困难、交给后一步什么”。首轮概述已经压缩了器件清单，本轮把每个删除或保留的决定追到了原文。

### 从模型继续追到验证

按式 (10) 的单运动散射体模型，可把观测写成 $z=Ae^{-j4\pi f_c d/c}$。在幅度非零、幅度项不引入相位翻转，并连续解缠相位的条件下：

$$
\Delta\phi=-\frac{4\pi f_c}{c}\Delta d.
$$

这说明距离变化为何能进入相位，也说明取主值相位会出现跳变。原文图 10(b) 显示的折返应连同相位解缠理解，不能把“相位与距离线性”写成每个显示点都落在同一直线上。

本轮还进行了一个数值一致性检查。§2.5（p. 6）报告相位变化 14.5 rad、理论距离 11.9 cm、手工测量 12.5 cm。将前两个数代回上述关系，隐含载频约为 2.909 GHz。§4.1（p. 9）列出的系统工作信道为 44；若使用该信道的 [5.22 GHz 中心频率](https://www.mathworks.com/help/wlan/ug/valid-channel-number-and-bandwidth-combinations.html)计算，14.5 rad 对应约 6.63 cm。§2.5 没有另列该验证的载频，因此这里保留为需要确认实验频点及数值来源的问题，未判定作者实际实验用了哪个频点，也未自行更改原数。

这个检查比复述“理论和测量大致一致”多走一步：变量、单位和实验配置必须能支撑同一计算。后续读到关键公式旁的示例数字时，应至少复算一组。

## 2 改稿练习：把机制、条件与推论写清楚

**自拟差例：**

> SiWiS places the transmitter and receiver together, so all phase errors disappear. After preprocessing, the phase gives human positions accurately, and the neural network generalizes to new environments.

这段把物理共址直接等同于时钟一致，又把单散射体关系扩大到人体位置，最后用机制推断替代跨场景实验。

**完整英文改稿：**

> SiWiS uses a locally captured copy of the transmitted WiFi waveform as the mixing reference, avoiding a separate sensing oscillator. It aggregates the L-LTF samples and removes the static component to expose motion-dependent phase changes. The resulting phase–distance relation provides intuition under a single-scatterer model. Multiple antennas and a learned decoder then address the richer reflections produced by human bodies. Generalization to new scenes is evaluated separately through held-out-scene experiments.

改动依次解决五件事：第一句指出具体机制；第二句解释预处理目的；第三句绑定模型条件；第四句交代模型与实际任务之间的补充设计；第五句把跨场景判断交给对应实验。动词由空泛的 *improve* 换成 *uses, aggregates, removes, exposes, addresses*，每个动词对应明确对象。

句式上，*as the mixing reference* 明确角色；*under a single-scatterer model* 直接限定推导范围；*is evaluated separately through…* 说明证据来自哪里。应用时，应先确认当前论文存在相应操作和实验。

## 3 实验分析：一个结果究竟回答什么问题

重新核对 §4.2–4.6、§5（pp. 9–13）后，首轮笔记需要补充以下层次。

| 原文位置 | 实际报告内容 | 本轮分析 |
| --- | --- | --- |
| §4.2、表 1 | 510,894 帧按时间 80/20 划分，训练测试共享人员和环境；视觉模型产生监督标签 | 主实验考察已有人员、环境中的新动作样本；评价参考来自视觉模型输出 |
| §4.3 | AP 被定义为超过 IoU 或 OKS 阈值的概率，再平均十个阈值 | 引用时保留本文定义；原文未交代置信度排序的精确率—召回率积分过程，代码实现仍需核对 |
| 表 2、§4.4 | SiWiS 掩膜 mAP 0.4805，列出的 Person-in-WiFi 分数 0.3800；该基线姿态列为空 | 可计算表中差值 0.1005；原文未充分交代基线重训、统一划分和输入条件，不能据此补写双任务同条件优势 |
| 表 2、图 19 | 掩膜 AP@70 为 0.5765，AP@80 为 0.1055；有多人重叠失败样例 | 数据显示严格几何阈值下明显退化；有限天线导致空间分辨率不足是作者的解释，本文未用天线数量消融单独验证 |
| §4.6、图 22 | 五场景轮换三训练、二测试，活动在 2.5 m 内；左图 mAP，右图 PCK | 两侧指标须分别读；室外姿态 mAP 约 0.2，宽阈值 PCK 的高值不代表精细几何恢复接近满分 |
| §4.5、图 20–21 | 输入时长超过 1.7 s 后收益放缓；距离实验为单人固定距离平行移动 | 输入窗口、计算时延和端到端响应时间各有定义；距离结论保留人数与运动方式 |

式 (17) 的 PCK 归一化记号也需要核对：文中把右肩和左髋称为位置，却未清楚说明所写平方和怎样对应肢体长度。本次记录定位这个表达问题，不据此判断作者代码的实际算法。

### 结果段训练

**自拟差例：**

> SiWiS achieves high accuracy and strong generalization. Its performance confirms that adding antennas solves overlapping-person detection.

**完整英文改稿：**

> On a chronological 80/20 split across 12 scenes, SiWiS reports mask and pose mAP scores of 0.4805 and 0.3469 under its stated metric definitions. The training and test sets share the same individuals and environments. Table 2 shows a marked decline at stricter geometric thresholds: mask AP falls from 0.5765 at IoU 0.70 to 0.1055 at IoU 0.80. Figure 19 also shows failures when people overlap. These observations motivate a spatial-resolution hypothesis; testing the effect of antenna count would require a controlled comparison.

这段把实验条件、观察与待验证解释分成不同句子。改稿时先找出数据直接支撑的判断，再确定机理解释该用多强的语气。

## 4 图文练习：让机制验证图能独立回答问题

本轮实际查看 pp. 5–6、9–13。图 10 用静止／移动两行、幅度／相位两列配对，读者能比较同一状态下两个观测量的变化。图 9 标出包内 L-LTF 与跨包特征的对应关系。双栏页宽属于模板约束；这两张图的配对顺序、信号字段和数据连接是作者的内容设计。

可继续改进的地方是图 10 横轴仅给包序号，相位曲线仍有折返，而正文讨论运动距离。助手原创方案保留原四个面板，另增加解缠相位随时间与参考位移对齐的面板，并标出载频、采样窗口和参考测量方式。新增面板需要相应原始数据；本次仅形成设计方案。

**原创引图句：** *Figure X examines whether the extracted phase remains stable without motion and changes consistently with reflector displacement.*

**原创图注：** *Proposed validation layout for motion-sensitive phase features. The first two columns compare amplitude and wrapped phase under static and moving conditions. A third column aligns unwrapped phase with independently measured displacement. The caption should report the carrier frequency, observation interval, and reference measurement procedure.*

**原创解释句：** *This arrangement connects the signal-level observation to the physical quantity used in the model, making the conversion assumptions visible beside the evidence.*

## 5 怎样用于作者已有研究

迁移依据来自本仓库已公开的研究目标和明确规范，未读取或改写私人稿件。

| 已知目标或要求 | 具体改稿方法 | 迁移时保留的范围 |
| --- | --- | --- |
| FastSET 目标是快速在线适应，切分是手段 | 方法段先写适应需要的信息和约束，再解释切分决策怎样服务目标；删除重复的模块枚举 | 保留现有背景与方法逻辑，只局部补充因果连接；来源为[表达规范 §2](../../docs/fastset-journal-retrospective/03-论文与科研表达.md) |
| FastSET 需要明确计时阶段和实际测量方式 | 借鉴训练／推理分工，分别交代离线准备、在线输入处理、适应训练；让时间数字对应实际阶段 | 以当前有效计时协议为准，不沿用过期设置或搬用SiWiS指标；见[依据记录](../../docs/fastset-journal-retrospective/06-复盘依据与偏好记录.md) |
| 电芯UWB组网关注规定期限内完整收集一批数据 | 结果段先定义完整批次、期限和失败事件，再给观测；将实体节点规模、时槽工作量、单帧接收率分开 | 只报告本项目实际实验规模和数据；参考[公开项目目标与结果](../../projects/cell-uwb-network/README.md) |

以下是可用于 UWB 方法／评估过渡处的原创结构示例，具体指标值须由实际数据填写：

> The collection round completes when the coordinator has received every scheduled cell report. We evaluate completion time together with the fraction of rounds that meet the deadline. This pairing separates fast partial delivery from timely collection of the full batch.

这里迁移的是指标与任务之间的写法。SiWiS 的自混频、天线结构和视觉监督没有被当作 UWB 组网或 FastSET 的既有技术。

## 本次完成范围

本轮重新追踪 §2.2–2.5 模型与验证，完整核对 §4.1–4.6 和 §5，实际看图 7–10、16–23及表 1–2所在页。完成机制段、结果段和 UWB 指标段三组原创练习，以及机制验证图布局与配套句子；补充一项公式数值复算。原始实验数据、评测代码及全部相关工作未复现。以上均为学习产物，尚无用户论文实际修改记录。
