# 研究候选的最小合成检查

对应[审查笔记](../../2026-11-27-candidate-audit.md)。这些脚本检查机制与强基线，没有使用用户实验数据，也没有运行论文原型。依赖Python 3与NumPy；在本目录逐个执行 `python 文件名.py`。脚本输出JSON并写入同名 `.json`，随机种子与假设包含在代码或输出中。

| 脚本 | 回答的问题 |
| --- | --- |
| `cfo_timing_audit.py` | 时间与频偏相消后，重排时槽能否胜过静态载频补偿？ |
| `puncture_replay_audit.py` | 删除输出LLR是否等价于删除前端曾使用的观测？ |
| `sensing_sketch_check.py` | 相同上传复数个数下，三阶投影能否胜过协调抽样？ |
| `illumination_bgpc_check.py` | 相同照明与权重下，交比关联能否增加BGPC已有能力？ |
| `mixed_version_check.py` | 删除旧版本状态会不会丢失迟到包可利用的信息？ |
| `harq_update_audit.py` | 保存投影能否支持一族新信道规则，包络外的LLR误差界是否一致？ |
| `merge_code_check.py` | 普通VQ中继合并是否结合，标准封闭码的性质是什么？ |
| `sensing_merge_review_check.py` | 空间插值是否与max交换，FSQ与同态解码器分别保证什么？ |

百分比、误差或秩仅解释对应脚本的模型。正文给出判断与文献位置；运行时间不属于性能比较。CFO脚本不含真实锁定/CRC模型，感知脚本不含真实目标散射，打孔脚本不含FastSET或LDPC训练。JSON中的100 dB条件是高信噪比近似，不标作严格零噪声。
