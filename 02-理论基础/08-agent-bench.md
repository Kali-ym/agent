# AgentBench 详解

> AgentBench 的价值不在于给模型排一个总榜，而在于提醒我们：评估 Agent 不能只看最终回答，要把模型放进交互环境里，看它如何观察、决策、调用工具、处理失败并完成任务。

## 概述

AgentBench 是一个面向 **LLM-as-Agent** 的多环境评测基准。它关注的不是模型单轮问答能力，而是模型在交互式任务中的推理、决策和行动能力。

理解 AgentBench，重点看四件事：

1. **它评的是什么**：模型是否能在环境里完成任务。
2. **它为什么重要**：传统 NLP benchmark 很难覆盖工具调用、多步决策和环境反馈。
3. **它有什么局限**：benchmark 分数不等于生产可用。
4. **它如何启发项目评测**：如何把标准 benchmark 思路迁移到自己的 Agent 项目里。

和下一篇 [[09-evaluation-metrics|Agent 评估指标体系]] 的关系是：

- AgentBench 关注 **评测任务和环境**。
- Evaluation Metrics 关注 **怎么量化表现**。
- Evaluation Harness 关注 **怎么稳定运行、记录和复现评测**。

## 1. 为什么普通 LLM Benchmark 不够

传统 LLM 评测多是这样的：

```text
题目
  -> 模型回答
  -> 和标准答案比较
  -> 得分
```

这适合测知识、阅读理解、数学、代码补全等能力，但不够测 Agent。

Agent 任务通常是：

```text
目标
  -> 观察环境
  -> 选择动作
  -> 调用工具
  -> 接收反馈
  -> 修正下一步
  -> 完成或停止
```

关键差异：

| 维度 | 普通 LLM 评测 | Agent 评测 |
|:---|:---|:---|
| 输入 | 一次性题目 | 任务 + 环境状态 |
| 输出 | 文本答案 | 动作序列 + 最终状态 |
| 过程 | 通常不评 | 必须评 |
| 工具 | 通常没有 | 经常有 |
| 状态 | 静态 | 动态变化 |
| 失败来源 | 多来自答案错误 | 可能来自规划、工具、环境、恢复、安全边界 |

所以 AgentBench 的基本思路是：不要只让模型“答题”，而是让它“做任务”。

## 2. AgentBench 在评什么

AgentBench 的核心定位是：在多个不同交互环境中，评估 LLM 作为 Agent 的推理和决策能力。

它不是单一任务，而是一组环境集合。每个环境都有自己的状态、动作空间、反馈和完成标准。

可以抽象成：

```text
Agent
  -> receives observation
  -> outputs action
  -> environment executes action
  -> returns new observation
  -> repeat until success / fail / step limit
```

这个结构和 [[04-react-framework|ReAct]]、[[05-cot-and-planning|Chain-of-Thought 与规划]]、最小 Agent loop 是一致的。

## 3. AgentBench 的典型环境

AgentBench 原始设计包含多个不同类型的交互环境，用来覆盖 Agent 的不同能力面。

| 环境类型 | 主要考察 | 典型难点 |
|:---|:---|:---|
| 操作系统 / Shell | 命令理解、文件操作、终端反馈 | 命令选择、错误恢复、状态追踪 |
| 数据库 | SQL 生成、查询验证、表结构理解 | schema 理解、结果校验、避免误操作 |
| 知识图谱 | 多跳关系推理 | 路径搜索、实体消歧、关系选择 |
| 数字卡牌 / 游戏 | 策略决策、长期收益 | 局部最优、状态更新、规则遵循 |
| 网页购物 | Web 任务、筛选和约束满足 | 多条件过滤、页面状态、目标保持 |
| Web 浏览 / Web QA | 搜索、点击、信息抽取 | 噪声页面、证据定位、行动路径 |
| 文本游戏 | 语言环境中的探索和行动 | 可用动作理解、长期记忆、试错 |
| 具身 / 家居类任务 | 指令分解、环境操作 | 空间状态、动作序列、失败恢复 |

不同资料对环境名称翻译略有差异，但核心是同一个：用多个交互式环境测 Agent 是否能做多步决策，而不是只测它会不会说。

## 4. AgentBench 的基本运行流程

一个 AgentBench 风格的评测，一般包含这些阶段：

```text
选择任务
  -> 初始化环境
  -> 提供工具 / 动作空间
  -> Agent 观察初始状态
  -> Agent 输出动作
  -> 环境执行动作
  -> 返回观察
  -> 循环直到成功 / 失败 / 达到步数限制
  -> 记录轨迹和最终结果
  -> 评分
```

核心产物不是只有 final answer，而是：

```text
task_id
initial_state
action_trace
observations
final_state
score
cost
failure_type
```

这也是为什么项目里强调 trace。没有 trace，Agent 评测只能得到“过了/没过”，很难知道为什么。

## 5. AgentBench 关注的能力维度

AgentBench 可以拆成几个能力维度来看。

| 能力 | 说明 | 失败表现 |
|:---|:---|:---|
| 指令理解 | 是否理解目标和约束 | 忽略条件、目标漂移 |
| 规划 | 是否能拆解多步任务 | 一步步乱试、缺少全局路线 |
| 工具选择 | 是否选对动作或工具 | 调错工具、参数错误 |
| 环境理解 | 是否能读懂 observation | 看错状态、误解反馈 |
| 记忆与状态追踪 | 是否记得已做过什么 | 重复动作、循环 |
| 错误恢复 | 失败后是否能修正 | 一错到底、编造成功 |
| 停止判断 | 是否知道何时结束 | 过早停止或无限循环 |
| 约束遵循 | 是否遵守任务和安全边界 | 越权、违反规则 |

这比“最终答案准确率”更接近真实 Agent 的能力结构。

## 6. AgentBench 和 ReAct 的关系

ReAct 是常见的 Agent 行动模式：

```text
Reason
  -> Act
  -> Observe
  -> Reason
  -> Act
  -> Observe
```

AgentBench 则提供了可以跑这种模式的环境和任务。

两者关系可以理解为：

| 概念 | 角色 |
|:---|:---|
| ReAct | Agent 的一种行为模式 |
| AgentBench | 测 Agent 行为表现的任务环境 |
| Metrics | 衡量表现的指标 |
| Harness | 自动运行和记录评测的系统 |

所以你不能说“用了 ReAct 就很强”，要看它在 AgentBench 或自定义 benchmark 上是否真的提升成功率、减少重复动作、降低成本和错误率。

## 7. AgentBench 的评分思路

AgentBench 这类评测通常不只看文本相似度，而是看任务结果和轨迹。

常见评分来源：

| 评分来源 | 说明 |
|:---|:---|
| 最终状态 | 任务是否真的完成 |
| 环境反馈 | 数据库、文件、网页、游戏状态是否符合预期 |
| 动作轨迹 | 是否走了合理路径，有无无效重复 |
| 步数限制 | 是否在有限步骤内完成 |
| 约束满足 | 是否满足任务限制和规则 |
| 成本统计 | token、工具调用、时间是否可接受 |

例如数据库任务，不应只看 Agent 是否“说查询完成”，而要看数据库返回是否符合目标。

Web 任务也一样，不应只看最终回答，还要看是否真的访问页面、是否找到来源、是否没有编造页面内容。

## 8. AgentBench 给工程实践的启发

AgentBench 对工程落地最重要的启发是：**把 Agent 评测设计成环境交互，而不是问答打分。**

如果你做 Paper Agent，benchmark 不应该只是：

```text
请总结 agentic RAG 论文
```

而应该是：

```text
给定 query
  -> 允许调用论文搜索工具
  -> 允许解析 PDF
  -> 要求每条结论有证据
  -> 保存 evidence.jsonl
  -> 检查引用是否支持结论
  -> 统计成功率、引用准确率、幻觉率、成本
```

如果你做 Web Agent，也不是只看回答，而是要记录：

```text
访问了哪些 URL
点击了哪些元素
页面状态如何变化
是否拿到了真实证据
是否在失败时停止
```

这才是 AgentBench 思路真正有价值的地方。

## 9. 和项目评测体系的衔接

当前项目里，Agent 评测可以分成三层：

| 层级        | 对应内容                                          | 作用                   |                 |
| :-------- | :-------------------------------------------- | :------------------- | --------------- |
| Benchmark | AgentBench、WebArena、GAIA、自定义任务集               | 定义考什么                |                 |
| Metrics   | [[09-evaluation-metrics                       | Agent 评估指标体系]]       | 定义怎么打分          |
| Harness   | [[../03-技术栈/26-agent-evaluation-harness-guide | Evaluation Harness]] | 定义怎么跑、怎么记录、怎么复现 |

这三层缺一不可：

```text
Benchmark without metrics = 有题没评分
Metrics without harness = 有评分但不可复现
Harness without benchmark = 有系统但不知道考什么
```

项目里已有的 `eval-cases.jsonl` 就是一个最小 benchmark 雏形。

## 10. 自定义 AgentBench：从 20 条 Case 开始

对于自己的项目，不需要一开始就复制大型 benchmark。更务实的做法是先建立一个小型、可复现的任务集。

推荐比例：

| 类型 | 数量 | 目的 |
|:---|:---:|:---|
| 正常任务 | 10 | 测主路径能力 |
| 边界任务 | 5 | 测约束和异常输入 |
| 工具失败任务 | 3 | 测错误恢复 |
| 安全任务 | 2 | 测拒绝和人工确认 |

示例结构：

```json
{
  "id": "paper-001",
  "category": "normal",
  "task": "找 2024 年以后关于 multimodal RAG 的 3 篇代表论文，并给出每篇的一句话贡献。",
  "expected_behavior": [
    "搜索公开论文源",
    "给出标题、年份、链接",
    "区分方法贡献"
  ],
  "forbidden_behavior": [
    "编造不存在的论文",
    "不给来源链接"
  ],
  "scoring": {
    "success": 0.5,
    "citation": 0.3,
    "conciseness": 0.2
  }
}
```

这个结构和 [[../07-项目与示例/examples/eval-cases.jsonl|eval-cases.jsonl]] 保持一致。

## 11. Case 设计原则

好的 Agent benchmark case 要有明确边界。

| 设计点 | 好做法 | 坏做法 |
|:---|:---|:---|
| 任务目标 | 明确用户要完成什么 | “帮我研究一下” |
| 初始状态 | 固定输入、环境、可用工具 | 每次环境不同且不记录 |
| 成功标准 | 可检查、可量化 | “结果要好” |
| 禁止行为 | 明确安全和范围边界 | 让模型自己决定边界 |
| 失败场景 | 主动设计工具错误、信息缺失 | 只测 happy path |
| 证据要求 | 要求引用来源或环境状态 | 只看输出是否流畅 |
| 成本约束 | 限制步数、时间、token | 无限搜索和重试 |

一个可用 case 至少要回答：

```text
任务是什么？
初始状态是什么？
可用动作是什么？
成功标准是什么？
哪些行为禁止？
如何评分？
如何复现？
```

## 12. Benchmark 结果怎么读

AgentBench 分数不能孤立理解。

你至少要同时看：

| 指标 | 为什么重要 |
|:---|:---|
| success rate | 看任务是否完成 |
| avg steps | 看是否绕远或循环 |
| failure type | 看主要失败来源 |
| tool error rate | 看工具接口是否拖后腿 |
| recovery rate | 看失败后能否修正 |
| cost / latency | 看是否可落地 |
| safety pass rate | 看是否守住边界 |

如果一个 Agent 成功率高但成本极高、工具调用混乱、容易越权，这不适合生产。

如果一个 Agent 成功率稍低但拒绝危险动作、trace 清晰、失败可恢复，工程价值可能更高。

## 13. AgentBench 的局限

标准 benchmark 有价值，但不能迷信。

常见局限：

| 局限 | 说明 |
|:---|:---|
| 环境简化 | 真实业务环境更脏，权限、异常、延迟更多 |
| 数据污染 | 模型可能在训练中见过部分任务或答案 |
| 评分偏窄 | 标准答案可能无法覆盖合理替代方案 |
| 工具差异 | 同一模型换 harness 后表现可能变化很大 |
| 安全不足 | 很多 benchmark 不覆盖生产级权限和合规 |
| 成本缺失 | 排名常不充分体现 token、延迟、工具成本 |

所以 benchmark 更适合回答：

```text
这个 Agent 在某类标准环境中大概有什么能力？
这个改动是否比上个版本更好？
失败主要集中在哪些任务类型？
```

不适合直接回答：

```text
它能不能无监督上线生产？
它是否能处理所有真实用户任务？
```

## 14. 常见误区

| 误区 | 更稳的理解 |
|:---|:---|
| 分数高就是生产可用 | 还要看权限、成本、恢复、安全和业务约束 |
| 只看最终成功率 | 还要看轨迹和失败类型 |
| 用公开榜单替代项目 eval | 项目必须有自己的场景 case |
| 单次运行代表能力 | Agent 有非确定性，要多次 trial |
| LLM judge 万能 | 关键指标要用规则、环境状态或人工抽检校准 |
| benchmark 越大越好 | 小而稳定、可复现、覆盖风险的 case 更有用 |

## 15. 面试怎么讲

一个合格回答：

> AgentBench 是评估 LLM-as-Agent 的多环境 benchmark，它把模型放到操作系统、数据库、网页、知识图谱等交互环境中，看模型能否通过多步观察、决策和行动完成任务。它和传统问答 benchmark 的区别是：不仅看最终答案，还看动作轨迹、环境状态、工具使用和失败恢复。工程上我不会只看 AgentBench 总分，而会结合 task success、tool accuracy、avg steps、recovery rate、cost、latency 和 safety 指标，并为自己的业务场景构造自定义 eval case。

如果面试官追问“怎么给自己的 Agent 做 benchmark”，可以答：

> 我会先做 20 条最小评测集，覆盖正常、边界、工具失败和安全拒绝四类任务。每条 case 写清 task、initial state、available tools、expected behavior、forbidden behavior 和 scoring。运行时保存 trace、observation、final state、token、latency 和 cost，再用规则评分、LLM judge 和人工抽检组合评估。

## 16. 和其他 Agent Benchmark 的区别

| Benchmark | 侧重点 | 适合理解什么 |
|:---|:---|:---|
| AgentBench | 多环境交互式 Agent 能力 | 通用 Agent 行动能力 |
| WebArena | Web 浏览和真实网站任务 | 浏览器 Agent、网页操作 |
| GAIA | 通用助手任务、工具和多模态推理 | 综合任务完成能力 |
| SWE-bench | 真实代码仓库修复 | Coding Agent 工程能力 |
| OSWorld | 操作系统和桌面操作 | Computer-use Agent |
| BrowserGym | 浏览器任务训练和评测环境 | Web Agent 研究与回归测试 |
| τ-bench / ToolBench | 工具调用和交互任务 | 工具使用与多轮任务 |

选择 benchmark 时，不要问“哪个最权威”，而要问：

```text
它的任务环境是否接近我的 Agent？
它的评分是否覆盖我的风险？
它能否复现并进入回归测试？
```

## 17. 落地检查清单

给自己的 Agent 做一个 AgentBench 风格评测前，先确认：

- [ ] 是否有固定 eval case。
- [ ] 是否有初始状态和可用工具说明。
- [ ] 是否有成功标准和禁止行为。
- [ ] 是否保存每步 action、observation 和 final state。
- [ ] 是否统计步数、成本、延迟和失败类型。
- [ ] 是否覆盖工具失败和安全拒绝。
- [ ] 是否至少跑多次 trial，而不是单次演示。
- [ ] 是否能作为回归测试反复运行。

## 一句话总结

AgentBench 的核心启发是：Agent 评测必须进入环境、记录轨迹、验证最终状态。真正有用的评测不是“模型说得像不像”，而是“它在有限步骤、有限成本和明确边界下，是否真的把任务做成了”。