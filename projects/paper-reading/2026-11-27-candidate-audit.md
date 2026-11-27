# 2026-11-27：研究候选的近邻与强基线审查

本轮按作者要求，先核对最接近的方法，再判断能否形成独立研究贡献。这份记录保留已经排除的机制及可复算原因，供后续选题避开重复。所有数值检查均为助手编写的合成算例，没有运行作者的无线原型、神经接收机或用户硬件。

研究背景沿用公开项目中的批量短记录采集、FastSET在线接收机和协同无线感知。归档里的三叶节点重复300个时槽与300个物理节点分别处理；本文不把前者外推为后者实测。

## 1. 用频偏感知的排程改善LoRa并发

**判定：当前机制淘汰。** 时间错位和载频偏移可以在解调坐标中相互抵消，因而值得检查并发条件。这个关系已有基础文献；只按频偏重新排列发射顺序尚无独立贡献。

近邻阅读：[HydraNet，MobiCom 2025](https://ningning-hou.github.io/homepage/files/MobiCom_25_HydraNet_camera_ready.pdf) §4.2，PDF pp.5–6；[Choir，SIGCOMM 2017](https://www.cs.princeton.edu/courses/archive/spring21/cos563/papers/lora.pdf) §6；[LoRaSyNc干扰消除](https://iris.unipa.it/retrieve/handle/10447/517999/1238379/Interference_Cancellation_for_LoRa_Gateways_and_Impact_on_Network_Capacity.pdf) 式6。HydraNet的部分发射硬件共用参考时钟，独立设备频偏不是其所有实验的默认条件。

原创算例使用SF8、125 kHz带宽：256 μs错位可被15.625 kHz频偏抵消。该结果仅描述波形相关性，没有模拟芯片锁定、报头、CRC或接收率。进一步固定八个发射位置，枚举8!个顺序；12组频偏中，按频偏排序全部输给枚举最优顺序。更简单的静态载频补偿在相同理想频偏知识下又胜过全部枚举排程，按约61 Hz频率步进量化后仍然如此。

决定性对照因此是实际频偏估计及载频补偿，不应拿未校准的固定排程作为唯一基线。0.1倍带宽只作比较尺度，不能当作新推导的商用芯片接收门限。[复算代码](experiments/2026-11-27-candidate-audit/cfo_timing_audit.py)

## 2. 用旧包的虚拟打孔结果指导神经接收机码率

**判定：基本方法已有直接近邻；保留一个评价错误的反例。** [Sony公开申请US20240187920A1](https://patents.google.com/patent/US20240187920A1/en) Examples 3-B/4-A、Table 1及Claims 14/17已用同一接收块的部分解码评估多个码率。[SoftRate](https://www.cs.princeton.edu/courses/archive/spring17/cos598A/papers/softrate.pdf) §3、§6也已用软信息推算其他速率。

更细的问题来自[DeepRx](https://arxiv.org/pdf/2005.01494) §V-C，PDF pp.21–25：前端会利用未知数据符号辅助信道推断。因此，删除某个输出LLR，仍可能留下该符号对其他LLR的影响。

原创检验用两个BPSK信息符号加一个奇偶符号、弱导频和两种可能信道。保留全部试验，不按母码成功与否筛选。每个SNR运行120,000块：在6 dB下，先用三符号推断再删除奇偶LLR，信息块错误率为0.554%；先删除奇偶观测再完整重算，为0.898%。预设0.7%门限会得到相反决策。这个反例验证“删除输出不等于删除已使用的输入信息”，未验证FastSET发生同样问题。

强基线是按真实保留观测重新运行完整前端。目前缺少超出正确重算的独立算法，故不推荐把“虚拟打孔”作为新贡献。实际换调制、功率、时长或把释放资源交给另一用户，也不等价于本算例的观测删除。[复算代码](experiments/2026-11-27-candidate-audit/puncture_replay_audit.py)

## 3. 通过三阶随机投影保留分布式雷达相位关系

**判定：同通信量的简单抽样更好。** 近邻包括[Fronthaul-Constrained Distributed Radar Sensing](https://arxiv.org/abs/2409.17753)的方法与评价、[Uncertainty-Aware Fusion](https://arxiv.org/abs/2607.22357)的融合与量化模型，以及[Compressive Radio-Interferometric Sensing](https://pure.hw.ac.uk/ws/portalfiles/portal/152218718/Compressive_radio-interferometric_sensing_with_random_beamforming_as_rank-one_signal_covariance_projections.pdf)的随机协方差投影。随机矩估计本身不能充当新机制。

原创模型包含三条有粗时间对齐的双基地测量边、一个静止点目标、逐帧未知节点载波相位及独立接收噪声。对256帧进行三边闭合乘积估计，上传48个复数：三阶随机投影的均方误差约17.27，协调抽取相同16帧仅约0.00413；完整上传768个复数约0.000269。两种压缩使用相同公共种子元数据约定。

该算例已足以淘汰当前投影。它没有把“节点本地拥有一条双基地边”与“中心需要先构造跨节点协方差”混为同一观测模型。[复算代码](experiments/2026-11-27-candidate-audit/sensing_sketch_check.py)

## 4. 用共同照明的交比关联多个雷达目标

**判定：经典盲增益标定直接覆盖当前模型。** 起点是在各接收机增益和目标散射强度未知时，用三次照明响应的交比构造共同指纹。对照阅读包括[Joint Beamforming and Association Design for MIMO Radar](https://arxiv.org/abs/1809.03389) §II–IV、[MULTI-SCOUT](https://arxiv.org/abs/2507.02613) §II、IV–V及[多雷达多特征融合](https://doi.org/10.3390/app16073159) §3.4–4。

进一步查到直接数学近邻：[Optimal Sample Complexity for Blind Gain and Phase Calibration](https://arxiv.org/abs/1512.07293)，PDF pp.3–5模型、pp.7–8可辨识条件。三次照明、两发射天线时，每个接收机的复数观测就是 `Y=diag(g)AX`。已知3×2照明矩阵A，取其左零向量n，再求 `Yᵀdiag(conj(n))` 的最小右奇异向量，即可估计增益倒数；随后恢复X，以其两行比值估计共同发射方向。这是已有BGPC的特例。

两接收机、四目标、每条件400次合成试验，双方使用相同三次照明与已知权重：

| 条件 | 交比不变量 | 行列增益交替最小二乘 | BGPC后按方向关联 |
| --- | ---: | ---: | ---: |
| 20 dB | 99.5% | 99.75% | 99.75% |
| 10 dB | 56.25% | 63.75% | 67.5% |
| 20 dB，目标×照明模型扰动尺度0.3 | 69% | 73.25% | 86.5% |

指标是整组排列全部正确的比例。点目标可分离、每次照明共用接收增益等假设均写在脚本中；功率观测与复数观测的模型不同。当前交比没有超出该强基线的能力。[复算代码](experiments/2026-11-27-candidate-audit/illumination_bgpc_check.py)

## 5. 动态数据更新后继续利用旧编码包

**判定：版本消元与安全窗口推进已有基础机制。** 读完[Practical Rateless Set Reconciliation，SIGCOMM 2024](https://cs.stanford.edu/~keithw/sigcomm2024/sigcomm24-final47-acmpaginated.pdf) pp.1–12正文；§4.1已支持编码缓存随集合更新，§9列出同步中变化的问题。追加读[ConflictSync](https://arxiv.org/pdf/2505.01144) §III-E/F、IV；[稀疏函数更新](https://arxiv.org/pdf/1605.01105) §I、III-A、V-A；[多版本相关编码](https://arxiv.org/pdf/1708.06042) §II、III-A；[Evict Early, Decode Efficiently](https://arxiv.org/pdf/2610.28097) §III–IV相关方法与实验。

原创有限域算例确实能从含旧变量的包提取当前变量信息，但完整多版本高斯消元获得相同结果。过早删除旧变量的枢轴行，还会丢失与迟到包联合解码的机会。确认后续不会引用再推进窗口，已有[Tetrys RFC 9407](https://www.rfc-editor.org/rfc/rfc9407.html) §4.2、5.4与[MillWheel](https://www.vldb.org/pvldb/vol6/p1033-akidau.pdf) §4.5作直接基线。

一个小下界也说明不能随意承诺常数内存：若已收 `rᵢ=x+zᵢ`，未来允许任意迟到包透露某个独立旧值zⱼ，保留完整缓存的零错误恢复能力需区分全部r向量。这个本轮构造用于排除过强目标，未作为新定理宣称。已知少量节点的补发还要与位图、缺包ID列表比较。[复算代码](experiments/2026-11-27-candidate-audit/mixed_version_check.py)

## 6. 用电池总压替代缺失单节数据的补发

**判定：普通物理冗余加按秩补发缺少新构造。** [Xia与Mi，Journal of Power Sources 2016](https://chrismi.sdsu.edu/publications/109.pdf)，DOI 10.1016/j.jpowsour.2016.01.057，PDF pp.2–6、9、11已经用相邻电芯电压和形成矩阵观测，并处理故障识别、噪声传播及顺序采样。另读[Karnehm与Neve，Batteries 2024](https://doi.org/10.3390/batteries10090305) §2–3的电流—电压拟合压缩和重构实验。

现有硬件若只增加一个独立总压，就只增加一条独立方程；缺m个任意电压仍需m−1个独立值。由相同无线值相加得到的总压新增秩为零。电压和也不能恢复温度、状态位或完整32 bit原记录。当前方案没有跨过这些限制。

## 7. 两项已排除的实现建议

短帧流水线方面，公开项目已实现双接收缓冲和先重开RX再取数。[CLoc预印本](https://arxiv.org/abs/2611.09619) PDF pp.2–4、10、12–15又已有共用前导的多节点STS接收和局部CIR提取。测距时间戳不等于多个独立载荷的解码；不能把现成DMA或共享捕获改名为新协议。

接收机方面，“排除当前符号证据，再给固定解映射器外信息”需要与消息传递和神经外信息接收机比较。只把冻结后端、外信息计算或低维在线适应组合起来，还没有独立增量。后续机制另行记录，避免在此把未完成的查新写成新颖性结论。

## 写作训练：让强基线决定段末判断

本轮最有用的写法是先交代同条件基线，再用具体差异决定结论。以下差例与改稿均由助手自拟，不是论文原句或用户稿。

差例：*Our invariant representation enables accurate target association without calibration. The high accuracy demonstrates its effectiveness and novelty.*

改稿：*We first test whether the proposed invariant adds information beyond blind gain calibration. Both methods receive the same three illumination responses and the same transmit weights. At 10 dB, the invariant recovers the complete association in 56.25% of trials, compared with 67.5% for the BGPC baseline. This comparison does not support an additional association capability under the separable point-target model.*

这段改稿把对照的信息条件、完整排列指标和结论范围连接起来。它用于本次合成算例的科研判断，尚未迁移到作者论文。

Rateless IBLT还提供了实验衔接案例：§7.3先在固定带宽下比较任务时间与字节，再用小任务时间线观察等待，最后改变带宽区分处理瓶颈。图13的起点是socket打开，首个编码符号约在一个RTT后到达；不能写成整个同步只需一个RTT。已查看PDF第4、11页渲染，未复算附录证明或运行作者实现。

可迁移的原创句组：*We next examine which costs determine collection time. The first experiment fixes the payload and varies link capacity. A second experiment reports the packet and feedback timeline under the same workload. Together, these measurements separate transmission cost from protocol waiting.* 只有实际存在这些实验时，才能用于论文正文。

| 维度 | 适用章节 | 触发问题 | 具体改法 | 来源 | 边界 |
| --- | --- | --- | --- | --- | --- |
| 创新定位、实验可信度 | Design / Evaluation | 仅与未校准、少信息的基线比较 | 列出双方观测与已知参数，加入同信息强基线，再决定段末贡献表述 | BGPC核对及本次关联算例 | 合成结果只覆盖所写模型 |
| 实验衔接、成本定义 | Evaluation | 总时延全部归因于少发字节 | 依次用总指标、时间线和带宽扫描区分传输、等待、处理 | Rateless IBLT §7.3，Fig.12–14 | 分清预计算成本、计时起点和完整任务 |
