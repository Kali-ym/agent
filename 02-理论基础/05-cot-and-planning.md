# Chain-of-Thought 与规划

> CoT 和规划不是让模型“想得越多越好”，而是把复杂任务拆成可检查、可执行、可恢复的中间状态。工程里更重要的不是暴露完整思维链，而是设计计划、证据、动作、检查点和失败恢复。

## 概述

这篇文档回答四个问题：

1. **CoT 是什么**：为什么分步骤推理会提升复杂任务表现。
2. **规划是什么**：为什么 Agent 不能只靠一步一步贪心行动。
3. **工程里怎么用**：如何把计划变成可执行、可验证、可中断恢复的状态机。
4. **什么时候不用**：哪些场景里 CoT / 规划会带来成本、幻觉和过度复杂度。

它和上一节 [[04-react-framework|ReAct]] 的关系是：

- ReAct 关注 **边想边行动**。
- CoT 关注 **分步骤推理**。
- Planning 关注 **先组织路线，再执行和修正**。

现代 Agent 通常不是三选一，而是组合使用：短任务用 ReAct，长任务加 Planning，高风险任务加检查点和人工确认。

## 1. CoT 到底是什么

Chain-of-Thought，直译是“思维链”。它的核心思想是：让模型在给最终答案前，先生成中间推理步骤。

简单对比：

| 模式                   | 形态                | 适合             |
| :------------------- | :---------------- | :------------- |
| Direct Answer        | 直接给结论             | 简单问答、事实查询      |
| CoT                  | 先分步推理，再给结论        | 数学题、逻辑题、多条件任务  |
| Structured Reasoning | 用固定字段记录推理摘要、证据和结论 | 工程 Agent、可审计任务 |

人话版：

```text
复杂问题
  -> 拆成几个中间判断
  -> 每一步减少不确定性
  -> 最后合成答案
```

CoT 的价值不在于“模型写了很多字”，而在于它让模型有机会把隐含的中间变量显式组织出来。

## 2. 为什么 CoT 有用

CoT 对复杂任务有帮助，主要因为它改变了模型的输出结构。

| 作用 | 解释 |
|:---|:---|
| 降低一步到位难度 | 不要求模型直接跨到最终答案 |
| 暴露中间状态 | 便于检查哪里出错 |
| 支持分解问题 | 把大任务拆成多个小判断 |
| 支持自我校验 | 可以在最终输出前检查矛盾 |
| 支持工具衔接 | 中间步骤可以转成工具调用或检索需求 |

比如论文研读任务里，直接让模型“写综述”风险很高。更稳的流程是：

```text
主题
  -> 检索论文
  -> 筛选代表论文
  -> 抽取贡献
  -> 抽取实验和局限
  -> 建立对比维度
  -> 生成综述
  -> 检查引用是否支撑结论
```

这本质上就是把 CoT 从“文本推理”升级成“任务流程”。

## 3. 但工程里不要暴露完整 Chain-of-Thought

真实系统里，不建议把完整隐藏推理链原样展示或持久化。

更推荐保存可审计摘要：

```json
{
  "step": 3,
  "goal": "select representative papers",
  "decision_summary": "Keep papers with direct relevance to agentic RAG and available full text.",
  "evidence": ["paper_id:arxiv-xxx", "paper_id:ss-yyy"],
  "next_action": "parse_pdf"
}
```

这样做更适合工程系统：

- 用户能看懂。
- 日志可审计。
- 不依赖完整思维链。
- 方便压缩进上下文。
- 方便失败恢复。

在 Agent 系统里，我们真正需要的是：

```text
reason_summary
  + evidence
  + action
  + observation
  + state_delta
```

而不是无限展开的内心独白。

## 4. CoT、Scratchpad、Trace 的区别

这几个词很容易混用。

| 概念 | 作用 | 是否适合持久化 |
|:---|:---|:---|
| CoT | 模型内部或输出中的分步推理 | 不建议完整持久化 |
| Scratchpad | 临时草稿区，用来组织中间信息 | 可以压缩后保存 |
| Trace | 工具调用、观察、状态变化的运行记录 | 必须保存 |
| Reason Summary | 可审计的推理摘要 | 推荐保存 |
| Plan | 可执行的任务分解 | 推荐保存 |

工程上优先级是：

```text
Trace > Plan > Reason Summary > Scratchpad > 完整 CoT
```

没有 trace，出了问题无法复盘；只有 CoT，没有工具观察，也无法证明结论可靠。

## 5. 规划解决什么问题

ReAct 很适合短任务，但长任务只靠“下一步该干什么”容易局部贪心。

规划的作用是：先建立一个全局路线，减少盲目探索。

典型结构：

```text
目标
  -> 任务拆解
  -> 依赖关系
  -> 检查点
  -> 执行顺序
  -> 风险边界
  -> 完成标准
```

例如做一个 Paper Agent，如果没有规划，模型可能一直搜索论文；如果有规划，它会知道什么时候停止检索、什么时候读 PDF、什么时候写对比表、什么时候做引用检查。

## 6. 常见规划模式

### 6.1 Plan-and-Execute

先生成计划，再逐步执行。

```text
Plan:
  1. 明确目标和输出格式
  2. 收集必要证据
  3. 执行核心任务
  4. 检查结果
  5. 输出最终产物

Execute:
  -> 按步骤调用工具
  -> 每一步记录 observation
  -> 必要时更新计划
```

适合：

- 长任务。
- 产物明确。
- 步骤大致可预测。
- 需要中途检查和恢复。

风险：

- 初始计划可能过时。
- 模型可能为了完成计划而忽略新证据。
- 计划太细会浪费 token。

### 6.2 ReAct + Lightweight Plan

先给一个轻量计划，然后每一步仍然根据观察动态决策。

```text
短计划
  -> 第一步行动
  -> 观察结果
  -> 修正下一步
  -> 继续
```

适合：

- 信息查找。
- Web 操作。
- Debug。
- 代码修复。

这通常比一次性写 20 步大计划更稳。

### 6.3 Hierarchical Planning

先拆大阶段，再在每个阶段内部细化。

```text
阶段 A：信息收集
  -> 子步骤 A1
  -> 子步骤 A2

阶段 B：生成产物
  -> 子步骤 B1
  -> 子步骤 B2

阶段 C：验证与修正
  -> 子步骤 C1
  -> 子步骤 C2
```

适合复杂项目，比如：

- 多文件代码改造。
- 论文综述生成。
- 企业流程自动化。
- 多工具数据分析。

优点是上下文更干净：当前阶段只需要保留和本阶段有关的信息。

### 6.4 Graph Workflow

当流程分支很明确时，不要让模型自由规划，直接用图承载状态。

```text
Start
  -> Classify Task
  -> Retrieve Evidence
  -> Need More Evidence?
      -> Yes: Retrieve Evidence
      -> No: Generate Draft
  -> Review
  -> Final
```

适合：

- 业务流程稳定。
- 需要恢复和重试。
- 有人工审核点。
- 分支条件明确。

这也是为什么很多生产系统会从“自由 Agent”回到 workflow / graph。

## 7. 计划应该长什么样

一个好的计划不是“列一堆待办”，而是要能驱动执行。

推荐结构：

```json
{
  "goal": "write a literature review for agentic RAG",
  "success_criteria": [
    "include at least 5 relevant papers",
    "every major claim has evidence",
    "include limitations and open questions"
  ],
  "steps": [
    {
      "id": "search",
      "objective": "collect candidate papers",
      "tool": "search_papers",
      "done_when": "at least 10 candidates with metadata"
    },
    {
      "id": "read",
      "objective": "extract evidence from selected papers",
      "tool": "parse_pdf",
      "done_when": "each selected paper has contribution/method/limitation notes"
    }
  ],
  "risks": ["paper unavailable", "citation does not support claim"],
  "checkpoints": ["after search", "before final writing"]
}
```

关键字段：

| 字段 | 作用 |
|:---|:---|
| goal | 防止目标漂移 |
| success_criteria | 判断是否完成 |
| steps | 支持执行和恢复 |
| done_when | 防止无限循环 |
| risks | 提前定义异常情况 |
| checkpoints | 支持人工确认和阶段复盘 |

没有 `done_when` 的计划，很容易变成“永远还能再优化一点”。

## 8. 计划不是一次性产物

长任务中，计划需要随着观察结果更新。

推荐状态演变：

```text
initial_plan
  -> execute step 1
  -> observation
  -> update state
  -> revise plan if needed
  -> execute next step
```

计划更新要有边界：

- 只因新证据更新。
- 不因模型“突然觉得”更新。
- 更新要记录原因。
- 不要频繁重写整个计划。
- 关键目标和安全边界不能被模型自行删除。

推荐记录：

```json
{
  "plan_revision": 2,
  "changed": ["replace Semantic Scholar with OpenAlex"],
  "reason": "Semantic Scholar returned rate_limited; OpenAlex is available.",
  "unchanged_constraints": ["public sources only", "claims require evidence"]
}
```

## 9. Reflection：反思有用，但不能神化

Reflection 是让模型在执行后复盘：哪里可能错了，下一步怎么修正。

它适合：

- 代码生成后检查测试失败。
- 论文综述后检查引用是否充分。
- Web 操作后检查是否达到页面状态。
- Agent 失败后归纳失败类型。

但 Reflection 也可能幻觉。如果没有真实观察，它只是另一次生成。

所以工程上建议：

```text
reflection = observation + checklist + constraints + proposed_fix
```

而不是：

```text
reflection = 模型自由自我批评
```

推荐检查表：

| 场景 | 检查项 |
|:---|:---|
| 论文综述 | 每条 claim 是否有引用支撑 |
| 代码修复 | 测试是否通过，是否引入新错误 |
| Web Agent | 页面状态是否真的变化 |
| RAG 回答 | 检索证据是否覆盖问题 |
| 数据分析 | 统计口径是否一致 |

## 10. CoT 与工具调用的关系

工具调用让 CoT 从“想”变成“验证”。

没有工具时：

```text
模型推理
  -> 结论
```

有工具时：

```text
模型提出下一步
  -> 工具执行
  -> 环境返回观察
  -> 模型根据观察修正
  -> 结论
```

这也是 Agent 比普通 prompt 更可靠的原因之一：关键中间步骤可以落到真实环境里验证。

但这要求工具返回足够好的观察结果：

| 差的工具返回 | 好的工具返回 |
|:---|:---|
| `error` | `rate_limited, retryable=true, wait_seconds=30` |
| 直接返回 10000 行 | 返回摘要、数量、前几条、分页 cursor |
| 只返回 HTML 全文 | 返回标题、主要文本、链接、可点击元素 |
| 只返回测试失败 | 返回失败测试名、错误摘要、相关日志 |

工具观察越清晰，模型越不需要靠“猜”。

## 11. CoT 与上下文工程

CoT 和规划都会消耗上下文。如果把所有草稿、计划、反思、工具结果都塞进去，成本会快速失控。

更稳的做法是分层保存：

| 信息 | 保存方式 | 是否进入上下文 |
|:---|:---|:---|
| 当前目标 | 明文 | 必须进入 |
| 当前计划 | 压缩结构 | 必须进入 |
| 最近观察 | 摘要 + 必要原文 | 选择进入 |
| 历史 trace | JSONL / 数据库 | 按需检索 |
| 长期经验 | Memory / 向量库 | 按需检索 |
| 原始大文件 | 文件系统 / 对象存储 | 不直接全量进入 |

这对应项目里的核心判断：Agent 开发本质上是上下文工程。CoT 不是越长越好，计划也不是越详细越好，关键是给模型当前决策所需的最小充分信息。

## 12. 常见失败模式

| 失败 | 表现 | 修复 |
|:---|:---|:---|
| 过度思考 | 简单任务生成很长推理 | 简单任务禁用规划，直接回答 |
| 计划太细 | token 浪费，执行僵硬 | 只规划阶段和检查点 |
| 目标漂移 | 执行几轮后偏离用户目标 | 固定 goal 和 success criteria |
| 计划不更新 | 新证据出现仍按旧路线走 | 允许有边界的 plan revision |
| 频繁重写计划 | 一直规划，不进入执行 | 限制 revision 次数 |
| 虚假反思 | 没有观察结果却自我批评 | reflection 必须引用 observation |
| 无限循环 | 一直搜索、一直检查 | 最大步数、done_when、重复动作检测 |
| 证据不足 | 推理看似完整但无来源 | evidence gate、引用检查 |

## 13. 什么时候不该用 CoT / Planning

以下情况不建议强行上规划：

- 简单事实问答。
- 单步文本改写。
- 用户只要一个短答案。
- 工具反馈极快且路径很短。
- 任务风险低、失败成本低。
- 固定 workflow 已经能稳定解决。

判断标准很简单：

```text
如果任务不需要中间状态，就不要制造中间状态。
如果任务路径固定，就优先 workflow。
如果任务开放且多步，再引入规划。
```

## 14. 工程推荐模式

### 14.1 简单任务

```text
User Task
  -> Direct Answer
```

适合：定义解释、简单总结、格式转换。

### 14.2 中等任务

```text
User Task
  -> Lightweight Plan
  -> Execute
  -> Final
```

适合：小型资料整理、单文件修复、短流程工具调用。

### 14.3 长任务

```text
User Task
  -> Goal + Success Criteria
  -> Stage Plan
  -> Execute Stage
  -> Checkpoint
  -> Revise Plan
  -> Continue
  -> Final + Trace Summary
```

适合：代码库改造、论文综述、数据分析、调试排障。

### 14.4 高风险任务

```text
User Task
  -> Plan
  -> Risk Classification
  -> Human Approval
  -> Execute Safe Step
  -> Verify
  -> Continue / Stop
```

适合：删除、提交、部署、付款、发消息、写数据库。

## 15. 面试怎么讲

一个合格回答：

> CoT 是让模型显式组织中间推理，适合复杂推理任务；Planning 是把目标拆成可执行、可检查的步骤，适合长任务和 Agent。工程里我不会依赖完整 chain-of-thought，而是保存 plan、reason summary、tool observation 和 trace。对生产 Agent，我会加 success criteria、done_when、最大步数、plan revision 边界、reflection checklist 和 human-in-the-loop，防止目标漂移、无限循环和虚假反思。

如果面试官追问“CoT 为什么不能直接都展示出来”，可以答：

> 生产系统更需要可审计、可压缩、可验证的中间状态。完整 CoT 成本高，也不等于真实证据。我更倾向保存 reason summary、工具观察、引用证据和状态变化，这些更适合调试和评测。

## 16. 与 Agent 项目的连接

做项目时，可以按下面方式落地：

| 项目 | CoT / Planning 用法 |
|:---|:---|
| Paper Agent | 计划检索、筛选、阅读、对比、写作、引用检查 |
| Travel Agent | 计划预算、日期、地点、约束、候选方案、最终行程 |
| Web Agent | 计划页面路径，执行后检查 DOM / 页面状态 |
| Coding Agent | 计划阅读、修改、验证、回归，失败后按日志修正 |
| RAG Agent | 计划检索范围、证据过滤、回答生成、引用验证 |

最小可交付不是“看起来会思考”，而是能输出：

```text
plan.json
trace.jsonl
evidence.jsonl
final.md
eval_summary.md
```

这几个产物比一段长 CoT 更有工程价值。

## 17. 学习路径

建议顺序：

1. 先读 [[04-react-framework|ReAct]]，理解行动闭环。
2. 再读本篇，理解 CoT、Plan-and-Execute、Reflection。
3. 接着读 [[../03-技术栈/11-context-engineering-practices|上下文工程实践]]，理解如何控制计划和观察进入上下文。
4. 再读 [[../03-技术栈/26-agent-evaluation-harness-guide|Evaluation Harness]]，用评测证明规划是否真的提升成功率。
5. 最后做 [[../07-项目与示例/projects/01-paper-agent/README|Paper Agent]] 或 [[../07-项目与示例/examples/minimal-agent-loop|最小 Agent Loop]]，把计划、工具、trace 串起来。

## 一句话总结

CoT 让模型把复杂推理拆开，Planning 让 Agent 把复杂任务拆开。真正可靠的 Agent 不是“想很多”，而是能把目标、计划、动作、观察、证据、检查点和恢复机制组织成一个可执行、可评测的系统。