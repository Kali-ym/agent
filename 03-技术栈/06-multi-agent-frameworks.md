# Multi-Agent 框架详解

> 本文是 [[05-langgraph-guide|LangGraph 框架指南]] 的下一篇。LangGraph 解决「有状态 Agent 怎么编排」，Multi-Agent 解决「多个角色如何分工协作」。两者有交集，但不是一回事。

---

## 1. 先给结论

Multi-Agent 不是「多开几个模型实例」这么简单。

更准确的理解：

```text
Multi-Agent System = 多个 (Model + Harness) + 协作协议 + 协调器
```

它适合解决单 Agent 的三个瓶颈：

1. **上下文爆炸**：一个角色扛规划、执行、审查，prompt 和 history 都太长。
2. **职责混乱**：工具太多、任务太杂，模型经常选错动作。
3. **并行子任务**：多个独立子任务可以同时推进，例如并行检索 5 篇论文。

但它也会引入新复杂度：协议设计、冲突解决、责任归因、成本控制和评测难度都会上升。

一句话：**Multi-Agent 是分工手段，不是智能增强手段。职责不清晰时，多 Agent 只会更乱。**

在本项目知识体系里，Multi-Agent 应该放在这里：

```text
Agent 系统
├── 单 Agent Loop          ← 最小闭环，先跑通这个
├── LangGraph 状态编排      ← 单系统内的多步骤 / 多角色
├── Multi-Agent 协作        ← 本文：多决策者分工
├── Harness Engineering   ← 工具、权限、trace、eval
└── Evaluation Harness    ← 证明系统真的变好了
```

---

## 2. Multi-Agent 解决什么问题

### 2.1 单 Agent 的边界

单 Agent 很适合：

```text
用户目标
  -> 规划
  -> 检索
  -> 生成
  -> 审查
  -> 输出
```

只要步骤可控、state 设计合理，**一个 Agent + LangGraph 多节点** 往往就够了。

但当任务变成下面这样时，才值得认真考虑 Multi-Agent：

```text
用户目标
  -> 3 个研究员并行搜不同来源
  -> 分析师各自抽取结构化字段
  -> 写作者汇总成报告
  -> 审稿人独立审查证据
  -> 协调者决定是补检索、重写还是结束
```

这里的核心变化不是「步骤变多」，而是：

- 子任务**彼此独立**，可以并行。
- 每个角色需要**不同的工具子集和上下文窗口**。
- 角色之间需要**显式交接协议**，而不是共享一坨 messages。

### 2.2 Multi-Agent 的核心价值

| 问题 | Multi-Agent 提供的能力 |
|:---|:---|
| 上下文太长 | 每个角色只看必要字段 |
| 工具太多 | 按角色分配工具白名单 |
| 职责混乱 | 角色 prompt 更专注 |
| 子任务可并行 | 多个 worker 同时执行 |
| 质量要求高 | reviewer / critic 独立审查 |

### 2.3 Multi-Agent 不能自动解决的事

| 它不能替你做 | 你仍然要自己做 |
|:---|:---|
| 判断该不该上 Multi-Agent | 先用单 Agent + 好 state 试一遍 |
| 设计角色边界 | 职责重叠 = 重复劳动或互相甩锅 |
| 解决冲突 | 两个 Agent 结论矛盾，听谁的？ |
| 控制成本 | N 个 Agent × M 步 = token 爆炸 |
| 归因失败 | 失败发生在 planner 还是 executor？ |

这和 [[27-agent-harness-engineering|Agent Harness Engineering]] 里的判断一致：

> **什么时候用 multi-agent？** 子任务独立性强、上下文隔离有收益、最后能汇总。

三个条件**同时满足**才值得上。

---

## 3. 在项目知识体系中的位置

```text
Agent 工程体系
├── 理论基础
│   ├── [[01-what-is-agent|什么是 Agent]]（L5 = Multi-Agent System）
│   ├── [[04-react-framework|ReAct 框架]]
│   └── [[05-cot-and-planning|CoT 与规划]]
│
├── 编排框架
│   ├── [[04-langchain-guide|LangChain 组件组合]]
│   ├── [[05-langgraph-guide|LangGraph 状态编排]]
│   └── 本文：Multi-Agent 框架对比
│
├── 工程架构
│   ├── [[12-factor-agent-architecture|12-Factor Agent 架构]]
│   └── [[27-agent-harness-engineering|Agent Harness Engineering]]
│
└── 质量保障
    ├── [[26-agent-evaluation-harness-guide|Evaluation Harness]]
    └── [[agent-evaluation-complete-guide|Agent 评估完全指南]]
```

推荐学习顺序：

```text
ReAct / Planning 理论
  -> 最小 Agent Loop
  -> LangChain 组件
  -> LangGraph 状态机（单系统多角色）
  -> Multi-Agent 框架（多决策者协作）
  -> Harness / Eval / Trace 工程化
```

---

## 4. 先分清两种「Multi-Agent」

很多人会把它们混在一起。面试和工程里，一定要先分清。

| | 伪 Multi-Agent（多角色单系统） | 真 Multi-Agent（多决策者） |
|:---|:---|:---|
| **本质** | 一个 Agent 的不同步骤 | 多个 Agent 各自决策 |
| **上下文** | 共享一份 State | 各自有 session / messages |
| **通信** | 通过 state 字段交接 | 通过消息、handoff、协议 |
| **控制权** | 图的路由函数决定流向 | 每个 Agent 自己选下一步 |
| **典型实现** | LangGraph 多节点 | AutoGen GroupChat、CrewAI Crew |
| **复杂度** | 较低，更稳 | 较高，需协议和 eval |
| **类比** | 流水线不同工位 | 不同同事各自干活再对齐 |

### 4.1 LangGraph 多角色 ≠ 真 Multi-Agent

[[05-langgraph-guide|LangGraph 框架指南]] 里的多角色模式：

```text
coordinator
  -> researcher
  -> analyst
  -> writer
  -> reviewer
  -> coordinator
```

这是**伪 Multi-Agent**：共享 `AgentState`，不同节点读写不同字段。工程上更常见，也更稳。

### 4.2 真 Multi-Agent 长什么样

```text
coordinator（独立 loop）
  -> 发任务给 researcher_A（独立 messages[]）
  -> 发任务给 researcher_B（独立 messages[]）
  -> 收集结构化结果
  -> 交给 writer（独立 messages[]）
  -> 交给 reviewer（独立 messages[]）
```

每个角色有自己的 harness：工具白名单、prompt、步数上限、trace。

Claude Code 的 Sub-Agent 就是这种设计——子代理拿**全新的 messages[]**，保持主对话干净。详见 [[17-claude-code-best-practices|Claude Code 最佳实践]]。

---

## 5. 四种协作模式

无论用什么框架，底层协作模式就这几类。

### 5.1 流水线（Pipeline / Sequential）

```text
researcher -> analyst -> writer -> reviewer -> END
```

- **特点**：固定顺序，像工厂流水线。
- **适合**：步骤依赖强、顺序明确的任务。
- **框架**：CrewAI `Process.sequential`、LangGraph 普通边。

### 5.2 协调者-工人（Orchestrator-Worker）

```text
coordinator
  ├── worker A（搜 arXiv）
  ├── worker B（搜 Semantic Scholar）
  └── worker C（搜内部知识库）
coordinator 汇总 -> writer
```

- **特点**：协调者分配任务，工人并行或串行执行。
- **适合**：子任务独立、可并行。
- **框架**：AutoGen Magentic-One、OpenAI Agents SDK handoff。

### 5.3 层级（Hierarchical）

```text
manager
  ├── team lead A -> worker A1, A2
  └── team lead B -> worker B1, B2
```

- **特点**：递归拆解，适合复杂项目。
- **适合**：软件开发、大型研究任务。
- **框架**：MetaGPT、CrewAI `Process.hierarchical`、AutoGen nested chat。

### 5.4 对话 / 辩论（GroupChat / Debate）

```text
proposer <-> critic（多轮）
或
agent_A, agent_B, agent_C 在 GroupChat 里轮流发言
```

- **特点**：通过多轮对话达成共识或交叉审查。
- **适合**：质量要求高、允许高 token 成本的场景。
- **风险**：容易空转、跑题、成本失控。
- **框架**：AutoGen `GroupChat`、CAMEL-AI。

---

## 6. 框架全景对比

| 框架 | 类型 | 核心抽象 | 协作模式 | 生产适用性 | 学习难度 |
|:---|:---|:---|:---|:---|:---|
| **LangGraph** | 图编排 | State / Node / Edge | 多角色单系统、子图 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **AutoGen** | 对话协作 | ConversableAgent / GroupChat | 群聊、嵌套、Magentic-One | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **CrewAI** | 角色任务 | Agent / Task / Crew / Process | 顺序、层级 | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **OpenAI Swarm** | 教学框架 | Agent / Handoff | handoff 链 | ⭐（教育用） | ⭐⭐ |
| **OpenAI Agents SDK** | 官方 SDK | Agent / Handoff / Guardrail | handoff、多 Agent | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **MetaGPT** | 场景框架 | Role / Action / SOP | 软件公司流水线 | ⭐⭐⭐ | ⭐⭐⭐ |
| **AgentScope** | 国产框架 | MsgHub / Pipeline | 消息中心、管道 | ⭐⭐⭐ | ⭐⭐⭐ |
| **Claude Code** | 生产 Harness | Sub-Agent / Agent Teams | 子代理隔离、任务链 | ⭐⭐⭐⭐⭐ | 读架构而非调 API |

选型时不要问「哪个框架最好」，而要问：

```text
1. 是真 Multi-Agent 还是多角色单系统？
2. 协作模式是流水线、协调者-工人还是群聊？
3. 是否需要 checkpoint、HITL、权限控制？
4. 团队语言栈是 Python 还是 TypeScript？
5. 有没有 eval 和 trace 能力？
```

---

## 7. 主流框架详解

### 7.1 AutoGen（Microsoft）

**定位**：以**对话**为核心的 Multi-Agent 框架。

**核心抽象**：

| 概念 | 作用 |
|:---|:---|
| `ConversableAgent` | 可对话的 Agent，能发消息、调工具、执行代码 |
| `GroupChat` | 多 Agent 轮流发言的群聊 |
| `GroupChatManager` | 决定下一个发言者 |
| `UserProxyAgent` | 代表人类，可执行代码或确认动作 |

**适合场景**：

- 研究员 + 程序员 + 测试员协作。
- 需要代码执行和 human-in-the-loop。
- 探索性任务，路径不完全固定。

**优势**：

- 生态成熟，AutoGen Studio 可视化。
- Magentic-One 提供通用任务 Agent 参考实现。
- 支持 nested chat、工具、代码执行。

**劣势**：

- GroupChat 容易空转，需要限制轮数和发言策略。
- 状态管理偏消息流，结构化 state 需自己设计。
- 成本随轮数线性增长，需要 cost guard。

**最小示例思路**：

```python
# 伪代码：研究员-程序员-测试员
researcher = ConversableAgent("researcher", system_message="...")
coder = ConversableAgent("coder", system_message="...")
tester = ConversableAgent("tester", system_message="...")

groupchat = GroupChat(agents=[researcher, coder, tester], messages=[], max_round=12)
manager = GroupChatManager(groupchat=groupchat)
user_proxy.initiate_chat(manager, message="实现一个快排并写测试")
```

**学习资源**：[AutoGen 官方文档](https://microsoft.github.io/autogen/)、[Magentic-One](https://github.com/microsoft/autogen/tree/main/python/packages/autogen-magentic-one)

---

### 7.2 CrewAI

**定位**：以**角色 + 任务 + 流程**为核心的 Multi-Agent 框架。

**核心抽象**：

| 概念        | 作用                                     |
| :-------- | :------------------------------------- |
| `Agent`   | 角色定义：goal、backstory、tools              |
| `Task`    | 具体任务：description、expected_output、agent |
| `Crew`    | 把 Agent 和 Task 组织成团队                   |
| `Process` | 执行流程：sequential / hierarchical         |

**适合场景**：

- 投研报告、内容生产、运营自动化。
- 角色分工清晰、任务可写成「谁做什么」。
- 快速搭建 MVP。

**优势**：

- API 直观，上手快。
- 角色驱动，适合简历项目（信息搜集 + 分析 + 撰写）。
- 支持 sequential 和 hierarchical 两种流程。

**劣势**：

- 灵活性不如 LangGraph 状态图。
- 复杂分支和失败恢复需额外工程。
- 工具集成深度取决于社区生态。

**最小示例思路**：

```python
# 伪代码：旅行规划团队
planner = Agent(role="旅行规划师", goal="...", tools=[search_tool])
guide = Agent(role="本地向导", goal="...", tools=[local_db])
booker = Agent(role="预订专员", goal="...", tools=[booking_api])

plan_task = Task(description="制定行程", agent=planner)
guide_task = Task(description="推荐景点", agent=guide)
book_task = Task(description="预订酒店", agent=booker)

crew = Crew(agents=[planner, guide, booker], tasks=[plan_task, guide_task, book_task], process=Process.sequential)
result = crew.kickoff()
```

**学习资源**：[CrewAI 官方文档](https://docs.crewai.com/)、[[../06-路线图/learning-roadmap-development|开发岗学习路线]] 第 6 周

---

### 7.3 OpenAI Swarm

**定位**：OpenAI 发布的**教学框架**，强调 handoff 思想。

**核心抽象**：

| 概念 | 作用 |
|:---|:---|
| `Agent` | 带 instructions 和 functions 的角色 |
| `handoff` | 把对话控制权交给另一个 Agent |

**适合场景**：

- 学习 handoff 概念。
- 快速验证「分诊 -> 专员处理」模式。

**不适合**：

- 直接上生产。Swarm 已明确为 educational framework，无 checkpoint、无完整 observability。

**价值**：

理解 handoff 比记住 API 更重要：

```text
用户 -> triage_agent
         ├── 账单问题 -> billing_agent
         ├── 技术问题 -> support_agent
         └── 其他 -> general_agent
```

这个模式被 OpenAI Agents SDK 继承并工程化。

---

### 7.4 OpenAI Agents SDK

**定位**：OpenAI 官方的 Agent 开发 SDK，轻量、带 handoff 和 guardrail。

**核心抽象**：

| 概念 | 作用 |
|:---|:---|
| `Agent` | 带 instructions、tools、handoffs 的 Agent |
| `handoff` | 结构化移交控制权 |
| `guardrail` | 输入/输出安全检查 |
| `Runner` | 执行 Agent loop，带 tracing |

**适合场景**：

- 需要 handoff 的客服分诊、多技能路由。
- 希望比 Swarm 更工程化，又比 AutoGen 更轻量。
- TypeScript / Python 双栈团队。

**和 LangGraph 的对比**：

| 维度 | OpenAI Agents SDK | LangGraph |
|:---|:---|:---|
| 编排方式 | handoff 链 + loop | 显式状态图 |
| 状态管理 | 消息流为主 | 结构化 State |
| checkpoint | 有限 | 一等公民 |
| 框架绑定 | OpenAI 模型优先 | 模型无关 |

---

### 7.5 MetaGPT

**定位**：模拟**软件公司**的多角色协作框架。

**核心抽象**：

| 概念 | 作用 |
|:---|:---|
| `Role` | 产品经理、架构师、工程师、测试等 |
| `Action` | 角色可执行的动作 |
| `SOP` | 标准作业流程，规定角色间交接 |

**适合场景**：

- 从需求到代码的软件开发自动化。
- 研究 Multi-Agent SOP 设计。
- 理解「角色 + 流程模板」范式。

**优势**：

- 场景完整，适合看「分工之后怎么串起来」。
- SOP 思想对设计自己的 Multi-Agent 很有启发。

**劣势**：

- 绑定软件开发场景，泛化需大量改造。
- 生产可控性和 eval 需自己补。

---

### 7.6 LangGraph 的 Multi-Agent 能力

LangGraph 不是专门的 Multi-Agent 框架，但它的**子图（subgraph）和 handoff** 能表达真 Multi-Agent。

两种用法：

**用法 1：多角色单系统（推荐新手）**

```text
共享 AgentState，不同节点 = 不同角色
```

**用法 2：子图隔离（更接近真 Multi-Agent）**

```text
parent graph
  -> invoke researcher_subgraph（独立 messages）
  -> invoke writer_subgraph（独立 messages）
```

LangGraph 的优势在于：checkpoint、interrupt、条件路由、trace 都是一等公民。详见 [[05-langgraph-guide|LangGraph 框架指南]] 第 11 节。

---

### 7.7 AgentScope（阿里 / ModelScope）

**定位**：国产开源 Multi-Agent 框架，强调**消息中心**和**易用性**。

**核心抽象**：

| 概念 | 作用 |
|:---|:---|
| `MsgHub` | Agent 间消息广播中心 |
| `Pipeline` | 顺序执行多个 Agent |
| `Service` | 工具和应用封装 |

**适合场景**：

- 中文生态、国产模型接入。
- 游戏、模拟、多角色对话类应用。
- 对 AgentScope Studio 可视化感兴趣。

**学习资源**：[AgentScope GitHub](https://github.com/modelscope/agentscope)

---

### 7.8 生产级参考：Claude Code 的 Multi-Agent

Cursor、Claude Code 这类 Coding Agent **不是** LangGraph 应用，而是自研 Harness。但它们的 Multi-Agent 设计非常值得学。

Claude Code 的分层（摘自项目面试备战材料）：

| 层 | 机制 | 关键洞察 |
|:---|:---|:---|
| s04 Sub-Agents | 子代理拿全新 messages[] | 保持主对话干净 |
| s09 Agent Teams | 持久化队友 + 异步邮箱 | 真正并行 |
| s10 Team Protocols | 统一请求-响应协议 | 代理间协商 |
| s12 Worktree Isolation | 任务与 git worktree 绑定 | 隔离执行环境 |

三条主干链路：

```text
① 控制链：启动 -> REPL -> Query Loop
② 执行链：Tool Runtime -> Permission -> Sandbox
③ 任务链：Task Runtime -> Sub-Agent / Agent Teams（不塞回主 Loop）
```

核心原则：**Multi-Agent 不塞回主 Query Loop，而是进入独立 Task Runtime。**

这和框架选型无关，而是 Harness 设计问题。详见 [[17-claude-code-best-practices|Claude Code 最佳实践]]。

---

## 8. 选型决策树

```text
任务能写成固定 workflow？
  ├── 是 → 用 Workflow，别上 Multi-Agent
  └── 否 → 单 Agent + LangGraph 多节点能搞定？
              ├── 是 → 单系统多角色（最稳）
              └── 否 → 子任务独立 + 上下文隔离有收益 + 能汇总？
                        ├── 是 → 选协作模式：
                        │         ├── 固定顺序 → CrewAI / LangGraph pipeline
                        │         ├── 群聊辩论 → AutoGen GroupChat
                        │         ├── handoff 分诊 → OpenAI Agents SDK
                        │         └── 复杂状态机 → LangGraph subgraph
                        └── 否 → 先优化单 Agent 的 context / tools / state
```

### 8.1 按场景推荐

| 场景 | 推荐方案 | 原因 |
|:---|:---|:---|
| 论文研读 / 投研报告 | LangGraph 多节点 或 CrewAI sequential | 步骤清晰，角色分工明确 |
| 软件开发团队模拟 | AutoGen GroupChat 或 MetaGPT | 需要多轮协商和代码执行 |
| 客服分诊 | OpenAI Agents SDK handoff | 轻量、路由清晰 |
| 复杂长任务 + 恢复 | LangGraph subgraph + checkpoint | 状态可恢复、可观测 |
| Coding Agent | 自研 Harness（学 Claude Code） | 框架覆盖不了 IDE 集成和权限 |
| 学习概念 | Swarm 或最小 handoff demo | 理解 handoff 即可 |

### 8.2 按团队阶段推荐

| 阶段 | 建议 |
|:---|:---|
| 第 1 周 | 手写单 Agent loop，别碰 Multi-Agent |
| 第 2-3 周 | LangGraph 多节点，理解多角色单系统 |
| 第 4-5 周 | 选一个框架（CrewAI 或 AutoGen）做 MVP |
| 第 6 周+ | 补 trace、eval、permission，再考虑真 Multi-Agent |

---

## 9. 生产工程检查清单

### 9.1 角色设计

- 每个角色职责是否**互斥**？
- 角色之间交接的是**结构化结果**还是 raw messages？
- 是否有 coordinator，还是靠 GroupChat 自由发言？
- 每个角色的工具白名单是否最小化？

### 9.2 协议设计

- 消息格式是否固定（task_id、status、artifacts）？
- handoff 时传递什么、丢弃什么？
- 冲突时谁有最终决定权？
- 超时和失败如何上报给 coordinator？

### 9.3 成本控制

- 是否有**全局步数上限**和**每角色步数上限**？
- GroupChat 是否限制 `max_round`？
- 是否支持模型路由（简单任务用便宜模型）？
- 是否有 [[27-agent-harness-engineering|cost guard]]？

### 9.4 可观测性

- 能否定位失败发生在哪个角色？
- 每个角色的 trajectory 是否独立可追溯？
- 是否有固定 eval case 覆盖多角色协作路径？
- 是否接入 [[26-agent-evaluation-harness-guide|Evaluation Harness]]？

### 9.5 与 Harness 的关系

Multi-Agent 框架只解决「角色怎么协作」。以下仍需自己掌控：

| 模块 | 框架通常不覆盖 |
|:---|:---|
| 权限 | 哪个角色能写文件、发邮件 |
| Sandbox | 代码执行隔离 |
| 上下文压缩 | 长对话的 snip / compact |
| Session 恢复 | 跨重启的任务恢复 |
| Eval | 多角色归因和回归测试 |

---

## 10. 常见坑

### 10.1 过早上 Multi-Agent

Demo 能跑 ≠ 需要 Multi-Agent。先用单 Agent 把主路径跑通，再拆角色。

### 10.2 角色职责重叠

```text
researcher：搜资料
searcher：查找信息   ← 和 researcher 重复，模型会混乱
```

角色名称和 description 必须**语义互斥**。这和 [[27-agent-harness-engineering|Harness 工具设计原则]] 一样。

### 10.3 GroupChat 空转

AutoGen GroupChat 容易陷入「我觉得你可以补充」「好的我来补充」式空转。

解法：

- 限制 `max_round`。
- 用 deterministic 发言策略，而非纯 LLM 选 speaker。
- 每轮要求**结构化输出**，不是自由闲聊。

### 10.4 共享上下文失控

真 Multi-Agent 的优势是隔离。如果所有角色共享完整 messages，就失去了拆分的意义。

### 10.5 没有 eval 就加角色

加一个 reviewer 角色很容易，证明它**真的提升了质量**很难。先用 [[26-agent-evaluation-harness-guide|Evaluation Harness]] 建立 baseline。

### 10.6 把框架当架构

CrewAI、AutoGen 是协作层，不是 Harness。生产级系统仍需自己掌控权限、trace、压缩和恢复。

---

## 11. 推荐实战

### 11.1 项目 1：投研报告 Multi-Agent（CrewAI）

对应 [[../06-路线图/learning-roadmap-development|开发岗学习路线]] 项目 2。

```text
用户输入公司名
  -> 信息搜集 Agent（搜索引擎、SEC API）
  -> 财报分析 Agent（PDF 解析、指标计算）
  -> 报告撰写 Agent（结构化输出）
  -> 保存中间产物和 trace
```

**框架承担**：角色定义、任务顺序、工具绑定。

**自研或重点控制**：

| 模块 | 原因 |
|:---|:---|
| 工具返回截断 | 防止上下文污染 |
| 重试和超时 | 外部 API 不稳定 |
| Eval Cases | 证明报告质量 |
| 引用溯源 | 结论必须可追溯 |

### 11.2 项目 2：Paper Agent 多角色（LangGraph）

对应 [[../07-项目与示例/projects/01-paper-agent/README|Paper Agent]] 和 [[05-langgraph-guide|LangGraph 指南]] 第 16 节。

```text
START
  -> query_planner
  -> paper_search
  -> dedupe_rank
  -> evidence_extract
  -> review_writer
  -> route
      ├── evidence_insufficient -> paper_search
      ├── citation_invalid -> evidence_extract
      └── done -> final_report
```

这是**伪 Multi-Agent**，但对论文场景通常够用，也更易 eval。

### 11.3 项目 3：软件开发团队（AutoGen）

```text
user_proxy
  -> GroupChatManager
      ├── researcher（调研方案）
      ├── coder（写代码）
      └── tester（写测试、跑测试）
```

适合学习 GroupChat 和代码执行，但要严格控制轮数和成本。

---

## 12. 学习路线

建议按下面顺序学习：

1. 先读 [[01-what-is-agent|什么是 Agent]]，理解 L5 Multi-Agent System 在能力分级中的位置。
2. 再读 [[04-react-framework|ReAct 框架]] 和 [[../07-项目与示例/examples/minimal-agent-loop|最小 Agent Loop]]，跑通单 Agent。
3. 读 [[05-langgraph-guide|LangGraph 框架指南]] 第 11 节，理解多角色单系统。
4. 回到本文，对比 AutoGen、CrewAI、Swarm 的设计哲学。
5. 选一个框架做 [[../06-路线图/learning-roadmap-development|第 6 周实战]]。
6. 补 [[27-agent-harness-engineering|Harness]] 和 [[26-agent-evaluation-harness-guide|Evaluation Harness]]。
7. 读 [[17-claude-code-best-practices|Claude Code 最佳实践]]，理解生产级 Multi-Agent 怎么做。

---

## 13. 面试表达

如果面试官问「什么是 Multi-Agent？和 LangGraph 多节点有什么区别？」：

```text
Multi-Agent 是多个相对独立的 Agent 通过角色分工和协作协议完成复杂任务。LangGraph 多节点是单系统内的多步骤，共享一份 State，我称之为多角色单系统。

真 Multi-Agent 适合子任务独立、上下文隔离有收益、且结果能汇总的场景。否则我会优先用单 Agent 或 LangGraph 多节点，因为更稳、更便宜、更易 eval。

框架选择上，固定顺序分工用 CrewAI 或 LangGraph pipeline；需要多轮协商用 AutoGen GroupChat；handoff 分诊用 OpenAI Agents SDK；复杂状态恢复用 LangGraph subgraph。但无论用什么框架，权限、trace、cost guard 和 eval 都要自己掌控。
```

如果面试官问「什么时候不该用 Multi-Agent？」：

```text
三种情况不上：第一，任务能写成固定 workflow；第二，单 Agent 加好 state 和 context builder 就能搞定；第三，角色职责拆不清。Multi-Agent 是分工手段，不是智能增强。拆不清职责，只会增加成本、空转和归因难度。
```

如果面试官问「CrewAI 和 AutoGen 怎么选？」：

```text
CrewAI 以角色和任务为中心，适合步骤清晰、顺序或层级明确的协作，比如投研报告、内容生产。AutoGen 以对话为中心，适合需要多轮协商、代码执行、探索性路径的场景，比如研发协作。两者都可以做 Multi-Agent，但 CrewAI 更像流水线，AutoGen 更像会议室。
```

---

## 14. 总结

Multi-Agent 的正确打开方式：

- 先分清**多角色单系统**和**真 Multi-Agent**。
- 用决策树判断**该不该上**，而不是为了简历硬上。
- 选对**协作模式**：流水线、协调者-工人、层级、群聊。
- 用框架解决**协作层**，用 Harness 解决**运行层**。
- 用 Eval 证明**加角色真的有效**。

最终目标不是「搭一个 Multi-Agent Demo」，而是构建一个**分工清晰、可观测、可归因、可评估**的协作系统。

---

## 15. 延伸阅读

- [[05-langgraph-guide|LangGraph 框架指南]]
- [[27-agent-harness-engineering|Agent Harness Engineering]]
- [[12-factor-agent-architecture|12-Factor Agent 架构]]
- [[17-claude-code-best-practices|Claude Code 最佳实践]]
- [[01-agent-map|Agent 学习地图]]
- [AutoGen 官方文档](https://microsoft.github.io/autogen/)
- [CrewAI 官方文档](https://docs.crewai.com/)
- [OpenAI Agents SDK](https://platform.openai.com/docs/guides/agents-sdk/)
- [MetaGPT](https://github.com/geekan/MetaGPT)
- [AgentScope](https://github.com/modelscope/agentscope)
