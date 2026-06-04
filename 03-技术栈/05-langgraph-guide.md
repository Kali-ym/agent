# LangGraph 框架指南

> 本文是 [[04-langchain-guide|LangChain 框架指南]] 的下一篇。LangChain 解决“组件怎么组合”，LangGraph 解决“有状态 Agent 怎么运行、暂停、恢复、分支和循环”。

---

## 1. 先给结论

LangGraph 是 LangChain 生态里的 **Agent 状态机框架**。

如果说 LangChain 更像一条数据管线：

```text
输入 -> Prompt -> Model -> Parser -> 输出
```

那么 LangGraph 更像一个可恢复的工作流系统：

```text
任务状态
  -> 节点 A
  -> 条件判断
  -> 节点 B / 节点 C
  -> 工具执行
  -> 人工确认
  -> 回到 Planner 或结束
```

LangGraph 最适合处理这类问题：

- Agent 需要多步执行。
- 中间过程有分支。
- 需要循环、重试、反思或审查。
- 需要暂停等待人工确认。
- 需要保存 checkpoint，失败后能恢复。
- 需要多个 Agent 或多个角色协作。
- 需要把 Agent 轨迹沉淀为可观测、可评估的数据。

一句话：**Chain 适合单向流程，LangGraph 适合有状态流程。**

---

## 2. LangGraph 解决什么问题

### 2.1 普通 Chain 的边界

普通 Chain 很适合表达：

```text
输入
  -> 改写问题
  -> 检索资料
  -> 生成回答
  -> 输出
```

但当任务变成下面这样时，普通 Chain 就会吃力：

```text
用户目标
  -> 先规划
  -> 如果资料不足，继续检索
  -> 如果工具失败，重试或换工具
  -> 如果结果有风险，等待人工确认
  -> 如果审查不通过，回到修改节点
  -> 如果超过预算，停止并总结当前状态
```

这已经不是简单数据流，而是状态流转。

### 2.2 LangGraph 的核心价值

| 问题           | LangGraph 提供的能力               |
| :----------- | :---------------------------- |
| 多步任务怎么组织     | 用节点和边表达工作流                    |
| 状态怎么传递       | 用统一 state 在节点间流转              |
| 什么时候继续、分支或结束 | 用条件边控制路径                      |
| 工具失败怎么办      | 显式错误分支、重试分支、降级分支              |
| 任务中途断了怎么办    | checkpoint 保存和恢复              |
| 人需要参与怎么办     | interrupt / human-in-the-loop |
| 多个角色怎么协作     | 多节点、多 Agent、handoff           |
| 怎么复盘运行过程     | 每个节点天然可 trace                 |

LangGraph 的价值不是让 Agent “更自由”，而是让 Agent **更可控**。

---

## 3. LangGraph 在项目知识体系中的位置

结合本项目的 Agent 学习路线，可以把 LangGraph 放在这里：

```text
Agent 工程体系
├── 理论基础
│   ├── [[01-what-is-agent|什么是 Agent]]
│   ├── [[04-react-framework|ReAct 框架]]
│   └── [[05-cot-and-planning|CoT 与规划]]
│
├── 上下文工程
│   ├── [[11-context-engineering-practices|上下文工程实践]]
│   ├── [[14-context-engineering|长上下文问题与修复]]
│   └── [[15-agent-memory|Agent Memory]]
│
├── 工程架构
│   ├── [[04-langchain-guide|LangChain 组件组合]]
│   ├── 本文：LangGraph 状态编排
│   ├── [[12-factor-agent-architecture|12-Factor Agent 架构]]
│   └── [[27-agent-harness-engineering|Agent Harness Engineering]]
│
└── 质量保障
    ├── [[26-agent-evaluation-harness-guide|Evaluation Harness]]
    └── [[agent-evaluation-complete-guide|Agent 评估完全指南]]
```

它承接的是：

```text
ReAct / Planning 理论
  -> 最小 Agent Loop
  -> LangChain 组件
  -> LangGraph 状态机
  -> Harness / Eval / Trace 工程化
```

---

## 4. 核心概念

### 4.1 State：状态是唯一真相来源

LangGraph 的核心不是节点，而是状态。

一个 Agent 在运行过程中需要知道：

- 用户目标是什么。
- 当前执行到哪一步。
- 已经做过什么。
- 已经拿到哪些证据。
- 哪些工具失败过。
- 剩余预算是多少。
- 是否需要人工确认。
- 最终输出是否已经完成。

推荐状态结构：

```python
from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    task: str
    success_criteria: List[str]
    steps: List[Dict[str, Any]]
    evidence: List[Dict[str, Any]]
    artifacts: Dict[str, Any]
    errors: List[Dict[str, Any]]
    budget: Dict[str, Any]
    final: Optional[str]
```

理解方式：

```text
State = 当前任务的全部上下文摘要 + 可恢复执行记录
```

不要把所有聊天历史原样塞进 state。更好的方式是保存结构化事实、证据、步骤和产物。

---

### 4.2 Node：节点是确定职责单元

节点是工作流中的一个处理单元。

常见节点：

| 节点             | 职责         |
| :------------- | :--------- |
| planner        | 拆解任务，决定下一步 |
| retriever      | 检索资料       |
| tool_executor  | 执行工具       |
| writer         | 生成草稿       |
| reviewer       | 审查结果       |
| human_approval | 等待人工确认     |
| finalizer      | 输出最终结果     |

一个好的节点应该只做一件事。

不推荐：

```text
一个 node 里既规划、检索、写作、调用工具、审查、输出
```

推荐：

```text
planner -> retriever -> writer -> reviewer -> finalizer
```

这样失败时能明确知道是哪一段出了问题。

---

### 4.3 Edge：边决定状态怎么流动

边负责连接节点。

有两类常见边：

```text
普通边：A -> B
条件边：A -> 根据状态选择 B / C / END
```

示例：

```text
reviewer
  -> 如果通过：finalizer
  -> 如果证据不足：retriever
  -> 如果内容有问题：writer
  -> 如果超过预算：END
```

条件边是 LangGraph 比普通 Chain 更适合 Agent 的关键。

---

### 4.4 Graph：图是显式工作流

一个最小研究 Agent 可以表达成：

```text
START
  -> planner
  -> retrieve
  -> write
  -> review
  -> route
      ├── pass -> final
      ├── need_more_evidence -> retrieve
      ├── need_rewrite -> write
      └── budget_exceeded -> final
```

这比“让模型自己决定下一步”更稳定，因为系统明确限定了可走路径。

---

### 4.5 Checkpoint：让 Agent 可恢复

没有 checkpoint 的 Agent，一旦中断就只能从头再来。

LangGraph 的 checkpoint 能保存中间状态，适合：

- 长任务。
- 多轮对话。
- 人工审批。
- 工具调用成本高的任务。
- 线上任务失败后恢复。

工程上要关注：

```text
thread_id：一次任务或一次会话的身份
checkpoint：某一步之后保存的状态
resume：从某个 checkpoint 继续运行
```

---

### 4.6 Interrupt：让人参与关键节点

生产 Agent 不应该默认全自动。

这些场景需要人工确认：

- 发邮件、发消息、提交表单。
- 修改数据库。
- 删除、覆盖、部署、支付。
- 使用高成本工具。
- 输出会影响用户决策的重要结论。

LangGraph 的 human-in-the-loop 设计适合把 Agent 暂停在某个节点，等人确认后再继续。

---

## 5. 最小 LangGraph 示例

下面是一个极简结构，重点看模块关系，不要陷入语法细节。

```python
from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    task: str
    steps: List[str]
    final: str | None

def plan(state: State):
    return {
        "steps": state["steps"] + ["规划任务"]
    }

def execute(state: State):
    return {
        "steps": state["steps"] + ["执行任务"]
    }

def finish(state: State):
    return {
        "final": "任务完成"
    }

graph = StateGraph(State)

graph.add_node("plan", plan)
graph.add_node("execute", execute)
graph.add_node("finish", finish)

graph.add_edge(START, "plan")
graph.add_edge("plan", "execute")
graph.add_edge("execute", "finish")
graph.add_edge("finish", END)

app = graph.compile()

result = app.invoke({
    "task": "写一段 LangGraph 介绍",
    "steps": [],
    "final": None,
})

print(result)
```

这段结构对应：

```text
输入 state
  -> plan 节点更新 steps
  -> execute 节点继续更新 steps
  -> finish 节点写入 final
  -> 输出最终 state
```

LangGraph 的关键不是“能不能调模型”，而是每个节点都能显式读写状态。

---

## 6. 条件分支：Agent 可控的关键

一个 Agent 不应该只会一路执行到底。它需要根据状态选择下一步。

示例状态：

```python
class ResearchState(TypedDict):
    question: str
    evidence: list[str]
    draft: str
    review_result: str
    retry_count: int
    final: str | None
```

路由逻辑可以是：

```python
def route_after_review(state: ResearchState):
    if state["review_result"] == "pass":
        return "finalize"

    if state["review_result"] == "need_more_evidence" and state["retry_count"] < 3:
        return "retrieve"

    if state["review_result"] == "need_rewrite" and state["retry_count"] < 3:
        return "write"

    return "finalize"
```

对应流程：

```text
review
  -> pass：finalize
  -> need_more_evidence：retrieve
  -> need_rewrite：write
  -> retry_count 超限：finalize
```

这里的核心思想和 [[12-factor-agent-architecture|12-Factor Agent 架构]] 一致：大部分控制流由确定性代码掌握，LLM 只负责关键判断或生成。

---

## 7. 常见工作流模板

### 7.1 Planner - Executor

适合：简单多步任务。

```text
user task
  -> planner
  -> executor
  -> final
```

特点：实现简单，但审查能力弱。

---

### 7.2 Plan - Act - Observe

适合：ReAct 风格工具调用。

```text
task
  -> plan
  -> act
  -> observe
  -> route
      ├── continue -> plan
      └── done -> final
```

对应 [[04-react-framework|ReAct 框架]] 的工程化版本。

---

### 7.3 Writer - Reviewer

适合：报告、代码、文档、论文综述。

```text
task
  -> writer
  -> reviewer
  -> route
      ├── pass -> final
      └── revise -> writer
```

注意加最大重试次数，否则容易无限修改。

---

### 7.4 RAG with Review

适合：知识库问答、论文助手、政策问答。

```text
question
  -> query_rewrite
  -> retrieve
  -> answer
  -> citation_review
  -> route
      ├── supported -> final
      ├── missing_evidence -> retrieve
      └── unsupported -> answer
```

核心要求：回答必须能被证据支持。

可配合 [[20-rag-full-pipeline|RAG 全链路实战]] 学习。

---

### 7.5 Human-in-the-loop

适合：高风险动作。

```text
task
  -> planner
  -> prepare_action
  -> human_approval
      ├── approved -> execute_tool
      └── rejected -> revise_or_stop
  -> final
```

这个模式比“模型直接调用工具”安全得多。

---

## 8. LangGraph 与 RAG

LangGraph 做 RAG 的重点不是替代向量数据库，而是把 RAG 的多个阶段变成可观测状态流。

普通 RAG：

```text
question -> retrieve -> answer
```

工程化 RAG：

```text
question
  -> query_rewrite
  -> retrieve
  -> rerank
  -> compress_context
  -> answer_with_citations
  -> verify_citations
  -> route
      ├── enough_evidence -> final
      ├── weak_evidence -> retrieve
      └── contradiction -> answer_with_citations
```

推荐状态：

```python
class RAGState(TypedDict):
    question: str
    rewritten_queries: list[str]
    retrieved_docs: list[dict]
    selected_evidence: list[dict]
    draft_answer: str
    citation_check: dict
    final: str | None
```

这样你可以清楚复盘：

- 原始问题是什么。
- 改写了哪些 query。
- 检索到了哪些文档。
- 哪些证据被选中。
- 回答引用是否支持结论。
- 是否发生二次检索。

这就是 [[11-context-engineering-practices|上下文工程]] 里的 Retrieve / Reduce / Isolate 在工程层面的落地。

---

## 9. LangGraph 与工具调用

工具型 Agent 的风险不在“会不会调用”，而在“会不会乱调用”。

推荐工具执行结构：

```text
planner
  -> tool_router
  -> permission_check
  -> tool_executor
  -> observation_summarizer
  -> route
      ├── success -> next_step
      ├── retryable_error -> tool_router
      ├── permission_denied -> final
      └── fatal_error -> final
```

工具返回建议统一为：

```json
{
  "ok": false,
  "error": "rate_limited",
  "retryable": true,
  "message": "请求频率过高，可以稍后重试",
  "partial_result": []
}
```

状态里不要只保存自然语言描述，至少保存：

```text
tool_name
args
observation
latency
cost
ok / error
```

这样后续才能做 trace、eval 和失败归因。

---

## 10. LangGraph 与 Memory

LangGraph 的 state 不等于长期记忆。

推荐区分：

```text
State
├── 当前任务状态
├── 当前步骤和中间结果
├── 当前上下文所需证据
└── 当前运行预算

Memory
├── 用户长期偏好
├── 历史任务摘要
├── 已沉淀知识
└── 可检索经验
```

一次运行中：

```text
任务开始
  -> 从 Memory 检索相关信息
  -> 写入 State
  -> 执行多个节点
  -> 从 State 提炼值得长期保存的信息
  -> 写回 Memory
```

这样能避免两个问题：

- 把长期记忆污染进当前任务状态。
- 把一次任务里的临时噪声永久保存。

Memory 设计建议继续看 [[15-agent-memory|Agent Memory - 从原理到实战]]。

---

## 11. LangGraph 与多 Agent

多 Agent 不等于多开几个模型实例。

更合理的理解是：不同节点承担不同角色。

```text
researcher：找资料
analyst：抽取结构化信息
writer：生成报告
reviewer：检查证据和风险
coordinator：决定下一步流转
```

LangGraph 适合表达这种角色协作：

```text
coordinator
  -> researcher
  -> analyst
  -> writer
  -> reviewer
  -> coordinator
      ├── need_more_research -> researcher
      ├── need_rewrite -> writer
      └── done -> final
```

关键点：

- 每个角色只看到必要上下文。
- 角色之间通过 state 交接结构化结果。
- coordinator 不应该只是“聊天式主持人”，而应该是明确的路由逻辑。
- 需要最大步数、成本预算和失败出口。

更多多智能体框架可以放到 [[06-multi-agent-frameworks|Multi-Agent 框架详解]] 中继续比较。

---

## 12. 生产工程检查清单

### 12.1 状态设计

- state 字段是否足够表达当前任务。
- 是否区分业务状态、执行状态和上下文状态。
- 是否能序列化和恢复。
- 是否避免保存无意义的完整原始历史。

### 12.2 节点设计

- 每个节点是否职责单一。
- 节点输入输出是否稳定。
- 节点失败是否有结构化错误。
- 节点是否方便单独测试。

### 12.3 路由设计

- 是否有 END 出口。
- 是否有最大重试次数。
- 是否有预算耗尽处理。
- 条件分支是否由确定性规则控制。

### 12.4 工具安全

- 是否只暴露当前任务需要的工具。
- 是否有权限确认。
- 是否有参数校验。
- 是否记录工具调用 trace。

### 12.5 评估与观测

- 是否保存每次运行的 state 轨迹。
- 是否有固定 eval case。
- 是否能比较不同图版本的成功率、成本和延迟。
- 是否能定位失败发生在哪个节点。

---

## 13. 常见坑

### 13.1 把图画得太复杂

初学者容易把所有可能性都画进图里，最后变成不可维护的蜘蛛网。

更好的方式：

```text
先做主路径
再加失败分支
最后加人工确认和恢复
```

### 13.2 让 LLM 决定所有路由

LLM 可以参与判断，但不应该掌握所有控制权。

推荐做法：

```text
LLM 输出结构化判断
  -> 确定性代码校验
  -> route 函数选择下一节点
```

### 13.3 state 里塞太多原文

state 是运行状态，不是垃圾桶。

大文本应该进入：

- 文件系统。
- 数据库。
- 向量库。
- artifact store。

state 中保存引用、摘要和必要证据即可。

### 13.4 没有最大步数

任何循环都必须有上限。

最小限制：

```text
max_steps
max_retries_per_node
max_tokens
max_cost
timeout
```

### 13.5 没有离线评估

图一旦复杂，靠手测一定会漏。

至少准备：

```text
正常任务
边界任务
工具失败任务
证据不足任务
权限拒绝任务
预算耗尽任务
```

---

## 14. 什么时候不用 LangGraph

不是所有 LLM 应用都需要 LangGraph。

不需要的情况：

- 单轮问答。
- 简单分类。
- 简单摘要。
- 固定 RAG 问答，没有循环和分支。
- 业务流程本来就很稳定，用普通代码更清楚。

可以先用 LangChain Chain 或普通函数组合。

需要的情况：

- 有多步状态。
- 有循环和分支。
- 有人机协作。
- 有工具执行和失败恢复。
- 有多 Agent 协作。
- 需要中断恢复和运行轨迹。

---

## 15. 推荐落地路径

### 第一步：先写最小 Agent Loop

先不要急着上框架，先理解：

```text
state
  -> build_context
  -> model_decide
  -> execute_action
  -> observe
  -> update_state
  -> stop_or_continue
```

可参考 [[../07-项目与示例/examples/minimal-agent-loop|最小 Agent Loop 模板]]。

### 第二步：把流程画成状态图

例如：

```text
planner -> retriever -> writer -> reviewer -> final
```

再标出可能回路：

```text
reviewer -> retriever
reviewer -> writer
```

### 第三步：定义 state schema

先定义数据结构，再写节点。

不建议边写节点边临时往 state 里塞字段。

### 第四步：逐个实现节点

每个节点都能单独测试：

```text
给定 state
  -> 节点处理
  -> 返回 state patch
```

### 第五步：加路由、重试和 END

先保证能结束，再追求智能。

### 第六步：加 checkpoint、trace 和 eval

没有这三项，就很难进入生产级迭代。

---

## 16. 一个实战方向：Paper Agent Graph

结合 [[../07-项目与示例/projects/01-paper-agent/README|Paper Agent：论文研读与综述助手]]，可以设计成：

```text
START
  -> clarify_topic
  -> plan_search
  -> search_papers
  -> rank_papers
  -> parse_papers
  -> extract_evidence
  -> write_review
  -> verify_citations
  -> route
      ├── pass -> export_report
      ├── weak_evidence -> search_papers
      ├── citation_error -> extract_evidence
      └── budget_exceeded -> export_report
  -> END
```

推荐 state：

```python
class PaperAgentState(TypedDict):
    topic: str
    search_queries: list[str]
    candidate_papers: list[dict]
    selected_papers: list[dict]
    evidence: list[dict]
    draft_review: str
    citation_report: dict
    artifacts: dict
    errors: list[dict]
    budget: dict
    final_report: str | None
```

这个项目能体现 LangGraph 的核心价值：

- 多步骤研究流程。
- 证据不足时回到检索。
- 引用失败时回到证据抽取。
- 超预算时带着当前结果退出。
- 最终产物和 trace 都可复盘。

---

## 17. 面试表达

如果面试官问“LangGraph 和 LangChain 有什么区别”，可以这样答：

```text
LangChain 更偏组件组合，例如 Prompt、Model、Parser、Retriever、Tool；LangGraph 更偏有状态 Agent 编排。

如果任务是单向数据流，用 Chain 就够了；如果任务需要循环、分支、checkpoint、人工确认或多 Agent 协作，就更适合用 LangGraph。

我会把 LangGraph 理解成 Agent 的状态机层：State 是唯一真相来源，Node 是职责单元，Edge 是流转规则，Checkpoint 负责恢复，Interrupt 负责人机协作。生产里我会特别关注最大步数、工具权限、结构化错误、trace 和 eval。
```

如果面试官继续问“为什么不用模型自己决定下一步”，可以补充：

```text
完全让模型决定控制流会导致不可预测、难复盘、难评估。更稳的方式是让模型输出结构化判断，再由确定性代码根据状态和规则选择下一节点。这样既保留模型的语义判断能力，又能保证系统可控。
```

---

## 18. 总结

LangGraph 的核心不是“画图”，而是把 Agent 从自由发挥变成可控状态机。

你需要重点掌握：

- State：保存当前任务的可恢复状态。
- Node：把复杂任务拆成职责单一的处理单元。
- Edge：用普通边和条件边控制流转。
- Checkpoint：让任务可以中断和恢复。
- Interrupt：让人在高风险节点参与。
- Trace / Eval：让系统可以复盘和迭代。

最终目标不是“用上 LangGraph”，而是构建一个能稳定运行、能解释过程、能失败恢复、能持续评估的 Agent 工作流。