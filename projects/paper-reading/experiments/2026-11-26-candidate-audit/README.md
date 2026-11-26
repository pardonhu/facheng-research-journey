# 研究候选的原创小检验

这些程序检查特定模型下的监督偏差、观测歧义和简单基线，均不代表用户系统的实测结果。分析与去留见[候选审核](../../2026-11-26-candidate-audit.md)。

在仓库根目录运行，例如：

```powershell
python -X utf8 projects/paper-reading/experiments/2026-11-26-candidate-audit/rf_alias_random_check.py
```

其他三个脚本可用同样方式运行。程序将JSON结果输出到终端，不下载数据、不连接设备、不创建额外结果文件。

| 程序 | 检查内容 | 主要条件 |
| --- | --- | --- |
| `rf_alias_random_check.py` | 400组预先随机布局中的相位别名，以及固定空间补测 | NumPy；复用相邻 `2026-11-25-candidate-audit/rf_phase_alias.py` 的解析前向模型；相同材料、每快照固定总能量；近观测的均值距离不等于误选概率 |
| `ota_supervision_counterexample.py` | 同源标签、独立噪声标签和SURE；已有两相位I/Q辨识 | NumPy；线性增益模型、已知方差、独立测试样本；不是FastSET复现 |
| `pilot_ambiguity_counterexample.py` | 相同导频和接收网格容许相反比特梯度 | NumPy；8子载波、QPSK、无编码约束；需要进一步检查真实码约束 |
| `hidden_joint_counterexample.py` | 两种隐藏联合状态给出相同旧日志、不同整批成功率 | Python标准库；每轮状态重置，旧策略每轮只试一条链路；不包含长期队列反馈 |

已由主助手重新运行四个发布版本；论文中未执行的系统实验仍按计划记录。脚本没有实现新算法，也不以数值示例代替文献查新。
