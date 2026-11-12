# 发成的科研探索之旅

记录我的科研探索：逐步形成自己的科研习惯与判断标准，学习如何评价一项工作、准备组会、寻找问题和设计实验，也保存尚未成熟的想法与值得反复阅读的论文。这不是一份完成的方法论，而是一份由我持续书写、修正和积累的研究笔记。

## 目录

- [如何评价一份工作](如何评价一份工作.md)
- [如何制作组会](如何制作组会.md) · [实验报告制作经验](docs/experimental-progress-report/制作经验.md) · [空白模板](docs/experimental-progress-report/实验进展组会模板.md) · [UWB 报告范例](docs/experimental-progress-report/范例/星型拓扑效率优化报告.md)
- [如何写一篇论文](如何写一篇论文.md) · [段落衔接、读图与结论的写法](如何写一篇论文.md#5-让读者从一个问题读到下一个问题)
- [如何写一份论文的 Review](如何写一份论文的Review.md)

## AI 平时就该怎样说人话

我喜欢 insight 式的表达交流：从第一性原理出发，让我快速 get 重点。AI 平时就该这样说话，贯穿日常交流、科研讨论和知识解释。

解释一个概念、公式或设计时，先抓住我当前想解决的问题，用一句话点出关键直觉，再从需求和基本约束推导：为什么需要它？它解决了什么？关键的数学或物理含义是什么？对看似可行的替代办法，用具体例子说明它在哪里失效、为什么满足不了当前需求；然后给出正式表达，解释符号如何对应前面的直觉，最后留下一句简洁的理解。

从已有知识接到新概念，用小例子让抽象关系可见。例如，已理解交叉熵后，解释 KL 散度可以从“按模型分布编码真实数据，会多付出多少理想编码成本”切入，再连接熵、交叉熵与二者之差。例子要服务于当前问题，避免顺势展开多个新主题。

避免术语堆砌、照本宣科的定义和一次讲太多内容。篇幅围绕一个核心问题展开，让我理解这个概念为什么会出现、为什么这样定义，以及它与我已知内容的联系。

## 项目记录

- [电芯 UWB 组网：代码、实验记录与跨模型交接](projects/cell-uwb-network/README.md)
- [论文研读与改稿训练](projects/paper-reading/README.md)
- [Codex 交接索引](<projects/codex arxive/README.md>)
- [全部项目](projects/README.md)

## 科研协作复盘

[FastSET 转期刊复盘：跨领域防错、有效经验与交付规范](docs/fastset-journal-retrospective/README.md)

从一次长期科研协作中总结错误模式和有效做法，供以后设计实验、调度远程计算、修改论文、制作图表和 PPT 时参考。重点是可迁移的判断方法和工作经验，而不是某个项目的参数清单。

- 先读：[八种错误模式与防错机制](docs/fastset-journal-retrospective/01-错误模式与防错机制.md)
- 有效经验：[值得复用的科研工作方法](docs/fastset-journal-retrospective/09-值得复用的科研工作方法.md)
- 远程计算：[服务器与多 GPU 实验调度](docs/fastset-journal-retrospective/08-远程服务器与多GPU实验调度.md)
- 写作与展示：[论文与科研表达](docs/fastset-journal-retrospective/03-论文与科研表达.md) · [图表与 PPT 交付](docs/fastset-journal-retrospective/04-图表与PPT交付.md)
- 快速使用：[开工与交付模板](docs/fastset-journal-retrospective/07-开工与交付模板.md)
- 核对来源：[复盘依据与偏好台账](docs/fastset-journal-retrospective/06-复盘依据与偏好台账.md)

原有指南保留原主线，新增经验以注明来源的补充章节维护。复盘中的建议、明确偏好和项目限定条件分别标注，后续任务以最新要求为准。

### RFDT 组会 PPT 复盘（2026-10）

[方法问题链、公式解释、实验证据与局部回退](docs/rfdt-ppt-retrospective/README.md) · [备稿与交付检查表](docs/rfdt-ppt-retrospective/checklist.md)

记录一次有进展但尚未完全可用的 PPT 协作：重点是如何让第一次接触论文的人理解作者解决问题的过程，以及怎样保护用户手动修改。
