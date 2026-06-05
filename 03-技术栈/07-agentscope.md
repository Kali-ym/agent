# AgentScope 框架指南

> 本文是 [[06-multi-agent-frameworks|Multi-Agent 框架详解]] 的配套深度文档。Multi-Agent 文档讲「什么时候该多角色协作」，本文讲「AgentScope 如何把协作、工具、上下文和生产部署落到代码里」。

---

## 1. 先给结论

AgentScope 是阿里达摩院开源的 **Multi-Agent 应用框架**，2026 年 5 月发布 **2.0 大版本**，核心定位是：**用 ReAct 范式把 Agent 跑起来，同时把生产环境需要的权限、沙箱、流式事件、会话持久化和部署能力内置进去。**

如果说 LangChain 更像「LLM 应用组件库」，LangGraph 更像「有状态工作流状态机」，那么 AgentScope 更像：

```text
Agent 运行时 + 多角色消息协作 + 生产部署套件
```

AgentScope 最适合处理这类问题：

- 需要 **多个 Agent 分工协作**（研究员、写作者、审稿人等）。
- 需要 **国产模型生态**（通义千问 / DashScope、DeepSeek、Moonshot 等）开箱即用。
- 需要 **流式 UI**（文本、思考、工具调用全过程可观测）。
- 需要 **Human-in-the-loop**（工具执行前人工确认、敏感操作外置执行）。
- 需要 **从笔记本原型快速迁到服务化部署**（REST + SSE、多租户、多会话）。
- 需要 **MCP / Skills / 沙箱** 等现代 Agent Harness 能力。

但它不适合替代工程设计。AgentScope 能降低 Multi-Agent 集成和部署成本，不能自动解决上下文污染、评估缺失、职责划分不清和成本失控。

在本项目知识体系里，AgentScope 应该被放在下面这个位置：

```text
Agent 系统
├── 上下文工程：决定什么信息进入模型
├── Agent Loop：决定任务如何推进（ReAct）
├── 工具系统：决定模型能调用什么能力
├── Multi-Agent 协作：决定角色如何分工
├── Harness Engineering：权限、沙箱、trace、eval
└── AgentScope：提供 Agent 运行时 + 消息协作 + 生产部署
```

如果你只记一句话：**AgentScope 是面向生产的 Multi-Agent 运行时，不是 Agent 架构本身。**

---

## 2. AgentScope 解决什么问题

### 2.1 没有框架时的典型状态

手写一个 Multi-Agent 系统通常会快速遇到这些重复问题：

- 多个 Agent 之间消息怎么广播、谁该看到什么。
- ReAct 循环里工具并发、失败重试、权限校验怎么统一处理。
- 长对话上下文怎么压缩，超大工具输出怎么截断。
- 流式 UI 需要把 token、tool call、tool result 拆成事件流。
- 人工确认、外部执行、会话恢复没有统一协议。
- 从本地脚本迁到 Docker / K8s / 多租户服务要重写大量胶水代码。

AgentScope 的价值，就是把这些 Multi-Agent 运行时问题做成一等公民抽象。

### 2.2 AgentScope 的核心边界

| 它能帮你做 | 它不能替你做 |
|:---|:---|
| 快速搭建 ReAct Agent 和工具调用 | 判断业务上该拆成几个角色、各自职责是什么 |
| 用 `observe` / 消息机制组织多 Agent 协作 | 设计稳定的协作协议和冲突解决策略 |
| 内置上下文压缩、工具结果截断、模型降级 | 保证答案可靠、引用真实、成本可控 |
| 提供权限系统、沙箱、Human-in-the-loop | 自动建立完整 eval 体系 |
| 提供 Agent Service 做 REST + SSE 部署 | 替代你对业务权限、合规、观测的工程治理 |

更务实的判断标准：

- **学习和原型阶段**：AgentScope 很适合，5 分钟能跑通第一个 Agent。
- **中文生态、国产模型、多角色对话 / 模拟类应用**：AgentScope 有明显优势。
- **需要生产级权限、沙箱、流式 UI、服务化部署**：AgentScope 2.0 是强项。
- **强状态机、复杂分支恢复**：可以借用 AgentScope 做局部运行时，复杂编排仍建议结合 [[05-langgraph-guide|LangGraph]] 或自研状态机。

---

## 3. AgentScope 在项目知识体系中的位置

结合本项目的 Agent 学习路线，可以把 AgentScope 放在这里：

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
├── 框架层
│   ├── [[04-langchain-guide|LangChain 组件组合]]
│   ├── [[05-langgraph-guide|LangGraph 状态编排]]
│   ├── [[06-multi-agent-frameworks|Multi-Agent 框架详解]]
│   └── 本文：AgentScope 运行时与部署
│
├── 工程架构
│   ├── [[12-factor-agent-architecture|12-Factor Agent 架构]]
│   ├── [[27-agent-harness-engineering|Agent Harness Engineering]]
│   └── [[28-mcp-protocol|MCP 协议]]
│
└── 质量保障
    ├── [[26-agent-evaluation-harness-guide|Evaluation Harness]]
    └── [[agent-evaluation-complete-guide|Agent 评估完全指南]]
```

它承接的是：

```text
ReAct 理论
  -> 最小 Agent Loop
  -> Multi-Agent 分工协议
  -> AgentScope 运行时（Agent + Msg + Event + Toolkit）
  -> Harness（权限 / 沙箱 / MCP / Skills）
  -> Agent Service 部署
  -> Eval / Trace 工程化
```

---

## 4. 版本与生态地图

### 4.1 仓库与文档

| 资源 | 地址 |
|:---|:---|
| GitHub（当前主仓库） | https://github.com/agentscope-ai/agentscope |
| 官方文档（2.0） | https://docs.agentscope.io/ |
| 旧仓库（1.x，已迁移） | https://github.com/modelscope/agentscope |

> 注意：本项目 [[06-multi-agent-frameworks|Multi-Agent 框架详解]] 中引用的 `modelscope/agentscope` 是 1.x 时代的地址。新用户应直接使用 `agentscope-ai/agentscope` 和 2.0 文档。

### 4.2 AgentScope 2.0 生态分层

```text
AgentScope 2.0 生态
├── Building Blocks（构建块）
│   ├── Agent          — ReAct 推理-行动循环引擎
│   ├── Message & Event — 消息持久化 + 流式事件
│   ├── Model          — 多供应商模型抽象（DashScope / OpenAI / Anthropic / DeepSeek 等）
│   ├── Tool           — 工具、MCP、Skills 管理
│   ├── Workspace      — 执行环境（Local / Docker / E2B）
│   ├── Context        — 上下文压缩与卸载
│   ├── Middleware     — 生命周期钩子（含 OpenTelemetry）
│   └── Permission     — 工具调用权限引擎
│
├── Deploy（部署）
│   └── Agent Service  — FastAPI + REST + SSE，多租户 / 多会话 / 定时任务
│
└── Frontend SDK
    └── @agentscope-ai/agentscope — TypeScript 消息/事件重建
```

### 4.3 1.0 → 2.0 关键变化

如果你在其他资料里看到 `MsgHub`、`SequentialPipeline`、`ReActAgent`，那是 **1.0 时代的 API**。2.0 是一次破坏性升级，核心变化如下：

| 维度 | 1.0 | 2.0 |
|:---|:---|:---|
| 核心 Agent 类 | `ReActAgent` | 统一 `Agent` 类 |
| 多 Agent 编排 | `MsgHub` + `Pipeline` | `observe()` + 事件流 + Middleware |
| 流式输出 | 有限支持 | 完整 `Event` 体系（`reply_stream`） |
| 工具权限 | 较弱 | 内置 `Permission System`（ALLOW / ASK / DENY） |
| 人工介入 | 有限 | `RequireUserConfirmEvent` / `RequireExternalExecutionEvent` |
| 部署 | 需自建 | 内置 `Agent Service`（REST + SSE + Redis 会话） |
| 执行环境 | 本地为主 | `Workspace`（Local / Docker / E2B 一行切换） |
| MCP / Skills | 后期加入 | 一等公民，通过 `Toolkit` 统一管理 |

**学习建议**：新项目直接从 2.0 开始；只有在维护旧代码时才需要了解 1.0 的 `MsgHub` / `Pipeline`。

---

## 5. 核心概念

### 5.1 Agent：ReAct 循环引擎

`Agent` 是 AgentScope 2.0 的核心抽象，把模型、工具、权限、上下文管理、中间件和事件系统整合进一个统一接口。

主循环：

```text
输入 Msg / Event
  -> 是否需要处理外部事件（人工确认 / 外部执行结果）？
  -> 加入上下文
  -> 检查下一步动作
      -> 需要推理：压缩上下文 -> LLM 调用
          -> 无 tool call：返回最终消息
          -> 有 tool call：进入 Acting
              -> 权限检查（ALLOW / ASK / DENY）
              -> 执行工具（支持并发 / 串行）
              -> 回到推理
  -> 返回 Msg 或暂停等待外部输入
```

关键接口：

| 方法 | 作用 |
|:---|:---|
| `reply(inputs)` | 跑完整个 ReAct 循环，返回最终 `Msg` |
| `reply_stream(inputs)` | 同上，但逐步 yield `AgentEvent`，适合流式 UI |
| `observe(msgs)` | 把消息注入上下文，**不触发推理**（多 Agent 场景核心） |
| `compress_context()` | 手动触发上下文压缩 |

最小示例：

```python
import asyncio
from agentscope.agent import Agent
from agentscope.model import DashScopeChatModel
from agentscope.credential import DashScopeCredential
from agentscope.message import UserMsg

agent = Agent(
    name="assistant",
    system_prompt="你是一个有帮助的助手。",
    model=DashScopeChatModel(
        credential=DashScopeCredential(api_key="YOUR_API_KEY"),
        model="qwen-max",
    ),
)

async def main():
    result = await agent.reply(UserMsg(name="user", content="你好"))
    print(result.get_text_content())

asyncio.run(main())
```

这与本项目 [[04-react-framework|ReAct 框架]] 的理论完全对应：AgentScope 把「推理 → 行动 → 观察结果 → 再推理」的循环做成了框架内置能力。

---

### 5.2 Message：Agent 间通信单元

`Msg` 是对话中的一个完整轮次，由类型化的 `ContentBlock` 组成：

| Block 类型 | 含义 | 出现在 |
|:---|:---|:---|
| `TextBlock` | 纯文本 | user / assistant / system |
| `ThinkingBlock` | 模型思考过程 | assistant |
| `ToolCallBlock` | 工具调用请求 | assistant |
| `ToolResultBlock` | 工具执行结果 | assistant |
| `DataBlock` | 图片、音频等多模态 | user / assistant |
| `HintBlock` | 注入给模型的提示 | assistant |

快捷工厂函数：

```python
from agentscope.message import UserMsg, AssistantMsg, SystemMsg

user_msg = UserMsg(name="user", content="分析这份报告")
system_msg = SystemMsg(name="system", content="你是资深分析师。")
```

**项目视角**：不要把所有原始聊天历史直接塞进上下文。结合 [[14-context-engineering|长上下文问题与修复]]，AgentScope 的 `ContextConfig` 提供了框架级压缩能力，但「什么该保留、什么该卸载」仍是你的工程设计责任。

---

### 5.3 Event：流式 UI 与 Human-in-the-loop 的基础

`Event` 是 `Msg` 的流式对应物。一次 `reply` 产生的事件序列，可以通过 `append_event()` 完整重建出一条 assistant `Msg`。

典型事件生命周期：

```text
ReplyStartEvent
  -> ModelCallStartEvent
      -> TextBlockStartEvent -> TextBlockDeltaEvent (×N) -> TextBlockEndEvent
      -> ToolCallStartEvent -> ToolCallDeltaEvent (×N) -> ToolCallEndEvent
  -> ModelCallEndEvent
  -> ToolResultStartEvent -> ToolResultTextDeltaEvent (×N) -> ToolResultEndEvent
  -> ReplyEndEvent
```

流式 UI 模式：

```python
from agentscope.event import TextBlockDeltaEvent, ToolCallStartEvent

async for event in agent.reply_stream(user_msg):
    if isinstance(event, TextBlockDeltaEvent):
        print(event.delta, end="", flush=True)
    elif isinstance(event, ToolCallStartEvent):
        print(f"\n[调用工具: {event.tool_call_name}]")
```

这与 [[27-agent-harness-engineering|Agent Harness Engineering]] 中「通道层需要把 Agent 运行过程可观测」的要求直接对齐。AgentScope 2.0 的事件体系让你不必手写 adapter 就能对接 AG-UI、A2A 或自研前端。

---

### 5.4 Toolkit：工具、MCP 与 Skills

`Toolkit` 统一管理 Agent 可调用的能力：

```python
from agentscope.tool import Toolkit, Bash, Read, Write, Grep, Edit
from agentscope.mcp import MCPClient, HttpMCPConfig

toolkit = Toolkit(
    tools=[Bash(), Read(), Write(), Grep(), Edit()],
    mcps=[
        MCPClient(
            name="amap",
            is_stateful=False,
            mcp_config=HttpMCPConfig(url="https://mcp.amap.com/mcp?key=..."),
        ),
    ],
    skills_or_loaders=["./skills"],
)

agent = Agent(
    name="coder",
    system_prompt="你是编程助手。",
    model=model,
    toolkit=toolkit,
)
```

| 能力层 | AgentScope 对应 | 本项目对应 |
|:---|:---|:---|
| 内置工具 | `Bash`, `Read`, `Write`, `Grep`, `Edit` | Harness L3 工具层 |
| MCP 集成 | `MCPClient` | [[28-mcp-protocol|MCP 协议]] |
| Skills | `skills_or_loaders` | Harness L3 Skills |
| 工具分组 | `Toolkit` 工具组 | 按角色分配工具白名单 |

---

### 5.5 Context：长对话的自动治理

AgentScope 内置上下文压缩，通过 `ContextConfig` 控制：

```python
from agentscope.agent import ContextConfig

agent = Agent(
    name="assistant",
    system_prompt="...",
    model=model,
    context_config=ContextConfig(
        trigger_ratio=0.7,       # 用到 70% 上下文窗口时触发压缩
        reserve_ratio=0.2,       # 压缩后保留最近 20%
        tool_result_limit=1000,  # 工具结果超过 1000 token 自动截断
    ),
)
```

对应本项目上下文工程的四个策略（Offload / Retrieve / Reduce / Isolate）：

| 策略 | AgentScope 实现 |
|:---|:---|
| Reduce | 自动上下文压缩（摘要旧消息） |
| Offload | `Offloader` 把压缩内容和超大工具结果卸载到磁盘 |
| Isolate | 多 Agent 各自独立 `Agent` 实例和上下文 |
| Retrieve | 需结合 RAG 或 Skills 自行实现 |

---

### 5.6 Permission System：工具调用的安全闸门

2.0 内置权限引擎，每个工具调用会经过 **ALLOW / ASK / DENY** 判断：

```text
工具调用请求
  -> ALLOW：直接执行
  -> ASK：暂停，发出 RequireUserConfirmEvent，等待用户确认
  -> DENY：返回错误给 LLM，模型可能换方案重试
```

用户确认后，可接受 `suggested_rules` 实现「同类操作以后自动放行」——这是把人工审核沉淀为策略的机制。

这与 [[12-factor-agent-architecture|12-Factor Agent 架构]] 中「工具必须有权限边界」的要求一致，也是 AgentScope 相比 LangChain / CrewAI 的差异化能力之一。

---

### 5.7 Workspace：执行环境隔离

`Workspace` 让你用一行配置切换执行环境：

```text
Local    — 本机直接执行
Docker   — 容器隔离
E2B      — 云端沙箱
```

每个 user / agent / session 可以有独立的工作目录、MCP 客户端和 Skills。对应 Harness 工程里「Agent 不应静默触碰宿主机」的安全要求。

---

### 5.8 Middleware：生命周期扩展点

1.0 的 Hook 机制在 2.0 升级为 Middleware，可在以下阶段插入自定义逻辑：

- `reply` 前后
- `reasoning`（LLM 调用）前后
- `acting`（工具执行）前后
- `model call` 前后
- `system prompt` 构建时

内置 `TracingMiddleware` 对接 OpenTelemetry，满足生产可观测性需求。

---

### 5.9 Agent Service：从脚本到服务

AgentScope 2.0 提供 FastAPI 工厂 `create_app()`，开箱支持：

| 能力 | 说明 |
|:---|:---|
| REST + SSE | 流式对话接口 |
| 多租户 / 多会话 | `SessionManager` + Redis 持久化 |
| 凭证管理 | 统一的 `Credential` 模块 |
| 定时任务 | `SchedulerManager` |
| 后台任务 | `BackgroundTaskManager` |
| Workspace 管理 | 按会话分配执行环境 |

如果你要做「从 Demo 到线上服务」的快速迁移，AgentScope 在这层的完整度明显高于大多数 Agent 框架。

---

## 6. Multi-Agent 协作模式

### 6.1 2.0 推荐模式：`observe` + 独立 Agent

2.0 不再以 `MsgHub` 为核心，而是通过 `observe()` 让 Agent 看到其他 Agent 的输出，同时保持各自独立的上下文和工具集：

```python
import asyncio
from agentscope.agent import Agent
from agentscope.message import UserMsg

# 两个角色，各自独立 system prompt 和 toolkit
researcher = Agent(name="researcher", system_prompt="你是研究员，负责检索和摘要。", model=model)
writer = Agent(name="writer", system_prompt="你是写作者，负责成文。", model=model)

async def main():
    # 研究员先工作
    research_result = await researcher.reply(
        UserMsg(name="user", content="调研 AgentScope 的核心特性")
    )

    # 写作者 observe 研究员的输出，但不触发自己的推理
    await writer.observe(research_result)

    # 写作者基于观察到的内容继续工作
    article = await writer.reply(
        UserMsg(name="user", content="请写成一篇技术博客")
    )
    print(article.get_text_content())

asyncio.run(main())
```

这种模式对应 [[06-multi-agent-frameworks|Multi-Agent 框架详解]] 中的核心原则：

```text
每个角色 = 独立 (Model + Harness) + 只看必要上下文
```

### 6.2 1.0 模式：`MsgHub` + `Pipeline`（了解即可）

在 1.0 中，多 Agent 协作用 `MsgHub` 做消息广播中心：

```python
# 1.0 API，仅供参考，新项目请用 2.0
from agentscope.pipeline import MsgHub, sequential_pipeline

async with MsgHub(participants=[agent1, agent2, agent3]) as hub:
    await agent1(Msg("user", "开始讨论", "user"))
    # agent2、agent3 自动通过 hub 观察到 agent1 的消息
    await sequential_pipeline([agent1, agent2, agent3])
```

| 1.0 概念 | 作用 |
|:---|:---|
| `MsgHub` | Agent 间消息广播中心，参与者自动互观察 |
| `sequential_pipeline` | 按顺序让多个 Agent 依次执行 |
| `fanout_pipeline` | 把同一输入分发给多个 Agent 并行处理 |

### 6.3 三种协作拓扑

结合本项目的 Multi-Agent 分类，AgentScope 常见的三种拓扑：

```text
拓扑 1：顺序流水线（Pipeline 思维）
  用户 -> 研究员 -> 分析师 -> 写作者 -> 审稿人
  实现：前一个 Agent 的 reply 结果 -> 下一个 Agent 的 observe + reply

拓扑 2：并行 Fan-out
  用户 -> [研究员A, 研究员B, 研究员C] 并行 -> 汇总者
  实现：asyncio.gather 多个 Agent.reply，汇总者 observe 全部结果

拓扑 3：共享讨论（MsgHub 思维 / 2.0 用 observe 模拟）
  多个 Agent 在同一讨论区互相 observe
  实现：每轮让一个 Agent reply，其他 Agent observe，轮流发言
```

**选型原则**（与 [[06-multi-agent-frameworks|Multi-Agent 框架详解]] 一致）：

- 子任务**独立可并行** → 拓扑 2。
- 步骤有**严格先后依赖** → 拓扑 1。
- 需要**协商讨论** → 拓扑 3，但要控制轮次和成本。

---

## 7. 与其他框架的对比

| 维度 | AgentScope 2.0 | LangChain + LangGraph | AutoGen | CrewAI |
|:---|:---|:---|:---|:---|
| 核心范式 | ReAct Agent 运行时 | 组件组合 + 状态图 | 对话式 Multi-Agent | 角色 + 任务编排 |
| Multi-Agent | `observe` + 独立 Agent | 子图 / handoff | GroupChat 原生 | Crew / Process 原生 |
| 流式事件 | 完整 Event 体系 | 需额外封装 | 有限 | 有限 |
| 工具权限 | 内置 Permission System | 需自研 | 需自研 | 需自研 |
| Human-in-the-loop | 事件级暂停 / 恢复 | interrupt 机制 | 有限 | 有限 |
| 国产模型 | DashScope 一等公民 | 需适配 | 需适配 | 需适配 |
| 生产部署 | Agent Service 内置 | 需自建 | 需自建 | 需自建 |
| 状态机编排 | 较弱（靠 Middleware 扩展） | 强（LangGraph 核心） | 中等 | 弱 |
| 学习曲线 | ⭐⭐⭐（2-3 天基础） | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |

### 7.1 什么时候选 AgentScope

- 国内团队，主要用通义千问 / DeepSeek 等国产模型。
- Multi-Agent 角色分工明确，不需要复杂状态机。
- 需要快速做出带流式 UI 和工具权限的生产原型。
- 需要 MCP、Skills、沙箱、Agent Service 一站式方案。

### 7.2 什么时候不选 AgentScope

- 任务核心是复杂分支、循环、checkpoint 恢复 → 优先 [[05-langgraph-guide|LangGraph]]。
- 只需要单 Agent RAG 问答 → [[04-langchain-guide|LangChain]] 生态更成熟。
- 需要严谨的 Agent 评估闭环 → 无论选哪个框架，都要自建 [[26-agent-evaluation-harness-guide|Evaluation Harness]]。

### 7.3 组合使用

实践中常见的组合：

```text
AgentScope 做 Agent 运行时 + 多角色协作 + 服务部署
  +
自研 Eval Harness 做质量保障
  +
LangGraph 做复杂审批流 / 状态机（如有需要）
```

---

## 8. 生产实践要点

### 8.1 对齐 12-Factor 架构

把 AgentScope 映射到本项目的 [[12-factor-agent-architecture|12-Factor Agent 架构]]：

| Factor | AgentScope 支撑 | 你仍需自研 |
|:---|:---|:---|
| 可控的上下文 | `ContextConfig` + `Offloader` | 业务级信息筛选策略 |
| 工具白名单 | `Toolkit` + `Permission System` | 角色级工具分配 |
| 状态可恢复 | `AgentState` + `RedisStorage` | 业务状态字段设计 |
| 可观测 | `TracingMiddleware` + Event 流 | 业务指标和 eval |
| 安全边界 | `Workspace` 沙箱 + Permission | 合规策略和审计 |

### 8.2 成本控制

| 策略 | 做法 |
|:---|:---|
| 限制 ReAct 轮次 | `ReActConfig.max_iters` |
| 压缩长对话 | `ContextConfig.trigger_ratio` |
| 截断工具输出 | `ContextConfig.tool_result_limit` |
| 模型降级 | `ModelConfig` 配置 fallback 模型 |
| 角色隔离 | 每个 Agent 只看必要上下文，避免全员围观 |

### 8.3 会话持久化

```python
from agentscope.state import AgentState
from agentscope.app.storage import RedisStorage

async with RedisStorage(host="localhost", port=6379) as storage:
    record = await storage.get_session(user_id, agent_id, session_id)
    state = record.state if record else AgentState()

    agent = Agent(..., state=state)
    result = await agent.reply(user_msg)

    await storage.update_session_state(user_id, agent_id, session_id, agent.state)
```

### 8.4 评估与 Trace

AgentScope 提供 OpenTelemetry 集成和完整事件流，但**不会自动告诉你 Agent 好不好**。上线前至少准备：

1. 一组固定 eval cases（输入 + 期望行为）。
2. 对工具调用轨迹的结构化记录。
3. 对最终输出的质量评分（规则 + LLM-as-Judge）。

参考 [[agent-evaluation-complete-guide|Agent 评估完全指南]] 建立评估思维。

---

## 9. 常见坑

| 坑 | 原因 | 修复 |
|:---|:---|:---|
| 多 Agent 上下文爆炸 | 所有角色共享完整历史 | 用 `observe` 只传递必要结果，每个角色独立 Agent |
| 工具越权 | Permission 未配置 | 为高风险工具设置 ASK，接受规则前先审查 |
| 系统 prompt 过长 | 压缩阈值触发失败 | 精简 system prompt 或换更大上下文模型 |
| 1.0 教程跑不通 | API 已破坏性升级 | 切换到 2.0 文档和 `agentscope-ai/agentscope` 仓库 |
| 没有 eval 就上线 | 框架不提供质量保障 | 自建 eval harness，至少覆盖核心场景 |
| 角色职责重叠 | Multi-Agent 分工不清 | 回到 [[06-multi-agent-frameworks|Multi-Agent 框架详解]] 重新审视分工 |

---

## 10. 学习路线

建议按下面顺序学习：

1. 先读 [[01-what-is-agent|什么是 Agent]]，理解 Agent 不是聊天机器人。
2. 再读 [[04-react-framework|ReAct 框架]]，理解推理和行动循环。
3. 再读 [[06-multi-agent-frameworks|Multi-Agent 框架详解]]，理解什么时候该多角色协作。
4. 回到本文，用 AgentScope 2.0 跑通单 Agent 和双 Agent 协作。
5. 继续读 [[27-agent-harness-engineering|Agent Harness Engineering]]，理解权限、沙箱、通道和观测。
6. 结合 [[28-mcp-protocol|MCP 协议]] 给 Agent 接入外部工具。
7. 用 [[26-agent-evaluation-harness-guide|Evaluation Harness]] 给 Agent 加上质量保障。

官方资源：

| 步骤 | 资源 |
|:---|:---|
| 快速上手 | [Quickstart](https://docs.agentscope.io/v2/quickstart) |
| 核心概念 | [Building Blocks](https://docs.agentscope.io/v2/building-blocks/agent) |
| 生产部署 | [Agent Service](https://docs.agentscope.io/v2/deploy/agent-service) |
| 版本迁移 | [Changelog](https://docs.agentscope.io/v2/change-log) |

---

## 11. 推荐实战：用 AgentScope 做一个 Paper Agent 双角色版

目标：构建一个简化版论文研读助手（与 [[04-langchain-guide|LangChain 框架指南]] 第 15 节的 Paper Agent MVP 对应）。

MVP 范围：

```text
用户输入研究主题
  -> Researcher Agent：检索 + 摘要（工具：搜索 / 阅读）
  -> Writer Agent：基于摘要生成带结构综述
  -> 保存事件流和 eval 结果
```

AgentScope 可承担：

| 模块 | AgentScope 角色 |
|:---|:---|
| 研究员 Agent | 独立 `Agent` + 检索工具 `Toolkit` |
| 写作者 Agent | `observe` 研究员结果 + 写作 `reply` |
| 流式 UI | `reply_stream` + Event 渲染 |
| 工具权限 | 限制下载 / 执行类工具需 ASK |
| 服务部署 | `Agent Service` 暴露 REST + SSE |

自研或重点控制：

| 模块 | 原因 |
|:---|:---|
| 证据溯源 | 结论必须能追溯到论文来源 |
| Eval Cases | 判断综述质量是否达标 |
| 角色 Prompt | 分工清晰比框架选择更重要 |
| 检索策略 | 框架不管你的 RAG 质量 |

---

## 12. 面试表达

如果面试官问「你了解 AgentScope 吗」，不要只说「阿里开源的 Multi-Agent 框架」。更好的回答结构是：

```text
我把 AgentScope 理解为面向生产的 Multi-Agent 运行时，核心价值是把 ReAct 循环、
工具权限、流式事件、上下文压缩和 Agent Service 部署集成在一起。

在 Multi-Agent 场景里，我用独立 Agent + observe 模式做角色分工，
而不是让所有角色共享一坨 messages。这样每个角色有自己的工具白名单和上下文窗口。

选型上，如果需要复杂状态机和 checkpoint 恢复，我会用 LangGraph；
如果需要快速做出带权限控制和流式 UI 的国产模型 Multi-Agent 服务，AgentScope 2.0 很合适。
但无论选哪个框架，评估、trace 和上下文治理都要自己掌控。
```

这类回答能体现你知道框架，也知道框架边界。

---

## 13. 总结

AgentScope 的正确打开方式：

- 用它快速搭建 **ReAct Agent + 多角色协作 + 流式 UI**。
- 用 **Permission System + Workspace** 管住工具安全边界。
- 用 **Agent Service** 把原型迁到可部署的服务。
- 用 **Event 流 + OpenTelemetry** 保留可观测性。
- 把 **角色分工、上下文策略、评估和成本** 握在自己手里。

最终目标不是「写一个 AgentScope Demo」，而是构建一个**角色清晰、权限可控、可观测、可评估、可部署**的 Multi-Agent 系统。

---

## 参考资源

- [AgentScope GitHub](https://github.com/agentscope-ai/agentscope)
- [AgentScope 2.0 文档](https://docs.agentscope.io/)
- [AgentScope 1.0 论文](https://arxiv.org/abs/2508.16279)
- [Multi-Agent 框架详解](06-multi-agent-frameworks.md)
- [Agent Harness Engineering](27-agent-harness-engineering.md)
