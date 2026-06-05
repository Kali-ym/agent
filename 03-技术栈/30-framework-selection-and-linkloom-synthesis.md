# 框架选型与 LinkLoom AI Builder 对话综述

> 本文汇总一次关于 Agent 框架分层、AgentScope/LangGraph 选型、以及 LinkLoom AI Builder 架构诊断的对话结论。  
> 目的：在项目环境里继续展开时，不必重读整段 chat，直接从这里接续。

**关联文档（本次已补充或引用）**  
- [[07-agentscope]] — AgentScope 2.0 框架指南（由占位符补全）  
- [[08-vector-db-basics]] — 向量数据库基础（由占位符补全）  
- [[04-langchain-guide]] / [[05-langgraph-guide]] / [[06-multi-agent-frameworks]]  
- [[01-what-is-agent]] / [[27-agent-harness-engineering]]  
- LinkLoom 源码：`\\wsl.localhost\Ubuntu\home\openclaw\NewsDaily\RSSPLUS\LinkLoom`

---

## 1. 对话主线（五句话）

1. **补了两篇技术栈文档**：`07-agentscope.md`、`08-vector-db-basics.md`，风格对齐 LangChain/LangGraph 指南。  
2. **框架分层**：AgentScope、LangGraph、AutoGen 等都在 L2「编排/运行时」层，但重心不同；Claude Code 在 L3「成品 Harness」，不是同一层。  
3. **手搓系统选型**：Coding Agent / Agent 生成器 → 核心 Harness 建议自研；LangGraph 管状态流；AgentScope 仅 Python 栈且与 LinkLoom 不匹配。  
4. **LinkLoom 诊断**：AI Builder 是「Plan 编译器 + 单次 LLM」；真正 Agent 行为在 `ReActRuntime`；两者未接通。  
5. **自建 Agent 算不算 Agent**：配置页编辑的是 Harness；`runAgent` + 工具 + ReAct 循环时算 L2–L3 Agent。

---

## 2. 框架分层地图

```text
L0  理论基础        ReAct、CoT、上下文工程
L1  组件层          LangChain Core、LlamaIndex 数据模块
L2  编排/运行时层   ← AgentScope、LangGraph、AutoGen、CrewAI、OpenAI Agents SDK
L3  成品 Harness    Claude Code、Cursor、Dify/Coze
```

### 2.1 一句话定位

| 框架/产品 | 核心问题 |
|:---|:---|
| **LangChain** | 组件怎么组合（L1，常被 L2 借用） |
| **LangGraph** | 任务状态怎么流转（状态图 / checkpoint / interrupt） |
| **AgentScope** | Agent 怎么跑、多角色怎么协作、怎么部署（ReAct 运行时 + Agent Service） |
| **AutoGen / CrewAI** | Multi-Agent 对话/角色流水线 |
| **Claude Code** | 已造好的 Coding Harness（学架构，不是库） |

### 2.2 AgentScope vs LangGraph

- **同一层**，不可完全互换。  
- LangGraph：**多角色单系统**（共享 State、Node/Edge）更强。  
- AgentScope：**独立 Agent + observe**、权限、沙箱、流式 Event、Agent Service 更强。  
- AgentScope **不能原生**做 LangGraph 式「共享 state 多节点」；硬做等于自己写编排。

### 2.3 AgentScope vs Claude Code

- **不是竞品**。Claude Code = 产品级 Coding Harness；AgentScope = Python 开发框架。  
- 都应学：**Sub-Agent 不进主 Loop**、上下文隔离、权限分级。  
- Claude Code 的 Task Runtime ≈ 真 Multi-Agent；AgentScope 2.0 的 `observe` ≈ 同类思路。

### 2.4 与 AgentScope 同层的框架

**最直接同类**：AutoGen、CrewAI、OpenAI Agents SDK  
**同层不同路**：LangGraph（图编排）、MetaGPT（SOP）、Parlant（合规）  
**国产同类**：Qwen-Agent、Lagent、agentUniverse  
**不是同层**：Claude Code、Dify、LangChain Core、Mem0、LangSmith

---

## 3. 三类「手搓」场景的选型结论

### 3.1 手搓 Coding Agent

| 建议 | 说明 |
|:---|:---|
| **主路径** | 自研 Harness（学 Claude Code），[[06-multi-agent-frameworks]] 明确推荐 |
| **编排** | 复杂分支/checkpoint → LangGraph（JS 版，若用 TS） |
| **工具/权限** | 可借鉴 AgentScope 设计，但 LinkLoom 是 Node/TS，不引入 Python AgentScope |
| **不要** | 整站押 AgentScope 或 LangGraph 替代自研 Harness |

分层草图：

```text
L4  CLI/IDE 通道（自研）
L3  任务编排（可选 LangGraph.js）
L2  Agent Loop（自研或增强 ReActRuntime）
L1  工具层（ToolRegistry + MCP）
L0  Sub-Agent Task Runtime（独立 messages[]）
```

### 3.2 手搓「Agent 生成的 Agent」（Meta-Agent）

```text
用户需求 → AgentSpec（结构化 JSON/Pydantic）
  → 校验 → 沙箱试跑 → HITL → 部署实例
```

| 层级 | 推荐 |
|:---|:---|
| **生成流水线** | LangGraph（状态机：clarify→draft→validate→test→deploy） |
| **Spec 编译器** | 自研 |
| **被生成的运行时** | 自研 minimal loop 或（Python 栈）AgentScope Agent Service |
| **关键** | AgentSpec Schema + Eval，不是换框架 |

三种生成模式：

- **A 配置生成**：自然语言 → agent/workflow YAML/JSON（最常见）  
- **B 运行时孵化**：主 Agent `Task(...)` 动态拉子 Agent（像 Claude Code）  
- **C 代码生成**：输出完整项目仓库  

### 3.3 LinkLoom 的 AI Builder 升级（结合 AgentScope 架构图）

用户目标：实现类似 AgentScope 2.0 图中的 Engine + Event + Permission + Workspace + Agent Service。

**结论：不要迁 Python AgentScope；在 LinkLoom 内抽共享 `AgentEngine`。**

| 图中模块 | LinkLoom 现状 | 升级优先级 |
|:---|:---|:---|
| Agent Engine（ReAct+Permission+Toolkit） | `ReActRuntime` 有 ReAct+工具，无 Permission | P1 |
| Event System + HITL | Builder 有 SSE；Runtime 有 trace，无统一 Event | P0 |
| Workspace（Docker/Sandbox） | 工具直跑宿主机 | P2 |
| Context 压缩/Offload | Builder 有 `compressRequested`；Runtime 无 | P2 |
| Middleware | 无 | P4 |
| Agent Service（Session/Cron/Pool） | 有 Scheduler；Builder 会话在浏览器 | P5 |

推荐路线：

```text
Phase 0  统一 AgentEvent + Builder UI 展示 tool/reasoning
Phase 1  Permission Gate 沉入 ReActRuntime
Phase 2  Context 压缩 + tool result offload
Phase 3  Workspace（Docker 试跑）
Phase 4  Middleware 链
Phase 5  Builder 服务端 Session + Background Task
Phase 6  AI Builder 用 Engine 做 sandbox 试跑（接 Runtime）
```

---

## 4. LinkLoom 架构事实（对话中读码结论）

### 4.1 系统总览

- **栈**：Node 24 + TypeScript + Fastify + PostgreSQL + LangChain（仅 `AIProvider` 模型适配）  
- **执行层**：`WorkflowEngine` + `AgentService` + `ReActRuntime`  
- **Meta 层**：`backend/src/services/aiBuilder/*`（AI Builder）

### 4.2 AI Builder 对话/操作时用什么（非验证阶段）

**不用** `ReActRuntime`、`AgentService`、`WorkflowEngine`。

```text
Admin → SSE /api/ai-builder/chat-stream
  → AiBuilderChatService.streamChat()
  → AIProvider.generateContent() / streamContent()
       tools: []   ← 恒为空，无工具循环
  → extractJsonObject → normalizePlan → SSE 事件
```

| 模式 | 行为 |
|:---|:---|
| **chat** | 纯文本流式补全 |
| **plan** | 单次 LLM → PlanDraft JSON |
| **build**（chat-stream 内） | 单次 LLM → AiBuildPlan JSON |
| **build-stream**（写库） | `AiBuildApplyService.applyPlan()`，**不调 LLM** |

因此 AI Builder 体感「单薄」的原因：**它是带 catalog 的 JSON 生成器，不是 Agent 循环。**

### 4.3 Dry-run / validate

- `buildDryRun()` = **静态字段 diff + 风险评级**，不执行 `WorkflowEngine` / `ReActRuntime`。  
- 与「真试跑」是两层能力，目前缺失。

### 4.4 正式 Agent 运行时

```text
AgentService.runAgent()
  → ReActRuntime.run()
  → while (rounds < maxRounds): LLM → tool_call → ToolRegistry/MCP → 观察 → 继续
```

这才是 [[04-react-framework]] 闭环；用户可在 Admin 配 prompt/temperature/tools，跑起来即为 Agent。

### 4.5 自建 Agent 算不算 Agent？

| 状态 | 判定 |
|:---|:---|
| 仅编辑 `AgentDefinition` | Harness 配置，不算「在运行」 |
| `runAgent` 无工具 | L0 Prompt App |
| `runAgent` + 工具 + ReActRuntime | **L3 Agent** |
| 作为 Workflow 固定步骤 | **L2 Workflow Agent** |
| AI Builder 对话生成 | L0，不是 Agent |

编辑 prompt/tools **正是**正常生产形态（Policy + Tool Registry），不等于假 Agent。

对照 [[01-what-is-agent]] 八模块：LinkLoom 已有 Goal、Tool Registry、Loop Controller（部分 Memory/Trace）；弱项是 Permission、强 State、系统 Eval。

---

## 5. 向量数据库文档要点（08-vector-db-basics）

- 向量库 = RAG **召回层**，不是 RAG 全部。  
- 选型：原型 Chroma → 实验 FAISS → 生产 Milvus/Qdrant。  
- 与 LinkLoom：若做资讯/RAG，PostgreSQL tsvector 已有；大规模语义检索可再加专用向量库。  
- 详见 [[08-vector-db-basics]]、[[20-rag-full-pipeline]]（后者仍为占位）。

---

## 6. AgentScope 文档要点（07-agentscope）

- 以 **2.0** 为主：`Agent`、`Msg`、`Event`、`Toolkit`、`Permission`、`Workspace`、`Agent Service`。  
- 1.0 的 `MsgHub`/`Pipeline` 仅作对照。  
- 与 LangGraph：**编排 vs 运行时**，可组合，不互换。  
- 详见 [[07-agentscope]]。

---

## 7. 待展开话题（在项目里继续聊）

按优先级列成 checklist，方便开新对话时 `@` 本文件并说「从第 N 节继续」。

### 7.1 LinkLoom 工程（高优）

- [ ] **M1**：`AiBuildPlan` / `PlanDraft` 改 Zod + LangChain structured output（替换 `extractJsonObject`）  
- [ ] **Phase 0**：定义 `AgentEvent` 类型，`ReActRuntime` 与 `AiBuilderChatService` 共用  
- [ ] **Phase 1**：`PermissionEngine` 接入 `ReActRuntime.callTool()` 前  
- [ ] **Builder 接 Runtime**：dry-run 阶段 sandbox 执行 `runAgent` / 迷你 workflow  
- [ ] **Builder 工具化**：`streamChat` 中 `tools: []` → Builder 专用工具（`search_catalog`、`preview_plan`）  
- [ ] **AgentEngine 目录结构**：`backend/src/services/agents/engine/` 接口草案  

### 7.2 知识库文档（中优）

- [ ] 把本文「LinkLoom 八模块对照」扩成独立小节或 LinkLoom 仓库 `docs/`  
- [ ] 补 [[20-rag-full-pipeline]]  
- [ ] 在 [[06-multi-agent-frameworks]] 7.7 加指向 [[07-agentscope]] 的深度链接  
- [ ] 四层对照图（LangChain / LangGraph / AgentScope / Claude Code）写入 [[07-agentscope]] 或 [[06-multi-agent-frameworks]]

### 7.3 概念深化（低优）

- [ ] `classic` vs `react` runtime mode 在 `ReActRuntime` 中的实际差异（读码显示 loop 相同，mode 主要进 trace）  
- [ ] LinkLoom Workflow DSL 与 LangGraph StateGraph 的概念映射  
- [ ] Paper Agent 双角色：LangGraph 编排 vs AgentScope observe 在 LinkLoom 里的等价实现  

---

## 8. 面试/对外表述模板

**框架理解**

```text
我把 Agent 拆成 Model + Harness。LangChain 是组件库，LangGraph 管状态流转，
AgentScope 管 Multi-Agent 运行时与部署。Coding Agent 和 AI Builder 的核心是
Harness 设计，框架只借局部能力。
```

**LinkLoom Agent**

```text
用户配置的是 Harness（prompt、工具、技能）；运行时由 ReActRuntime 提供
Observe-Act 循环。WorkflowEngine 负责业务编排。AI Builder 是 Meta 层配置
生成器，目前用单次 LLM 出 Plan，下一步是接 Engine 做 sandbox 试跑。
```

---

## 9. 关键代码锚点（LinkLoom）

| 路径 | 作用 |
|:---|:---|
| `backend/src/services/aiBuilder/AiBuilderChatService.ts` | Builder 对话主入口，`tools: []` |
| `backend/src/services/aiBuilder/AiBuilderPlanService.ts` | Plan 生成 |
| `backend/src/services/aiBuilder/AiBuilderDryRunService.ts` | 静态 dry-run + `executeBuild` |
| `backend/src/services/aiBuilder/AiBuildApplyService.ts` | 写库 |
| `backend/src/services/agents/AgentService.ts` | 正式 `runAgent` |
| `backend/src/services/agents/runtime/ReActRuntime.ts` | ReAct 循环 |
| `backend/src/services/agents/WorkflowEngine.ts` | 工作流调度 |
| `backend/src/services/AIProvider.ts` | LangChain 模型适配 |
| `backend/scripts/test-ai-builder.mjs` | Builder 回归测试（2000+ 行） |

---

## 10. 总结一张图

```text
                    Codian 知识库（本次对话）
                    ├── 07-agentscope（已写）
                    ├── 08-vector-db-basics（已写）
                    └── 30-本文（综述）

                    LinkLoom 运行时
                    ┌─────────────────────────────────┐
                    │ AI Builder（Meta）               │
                    │  AIProvider 单次 JSON  LLM tools=[]│
                    │  ──── 未接 ────►                 │
                    │ AgentEngine（待建）              │
                    │  ReActRuntime + Permission + Event│
                    │  ▲                               │
                    │ WorkflowEngine 调度 agent 步骤   │
                    └─────────────────────────────────┘

                    升级方向：Builder ──试跑──► Engine，不要换 Python 框架
```

---

*生成说明：基于 2026-06 对话整理；LinkLoom 版本以仓库 `README` v1.1.0 为准。继续讨论时建议附带具体里程碑（如「先做 Phase 0 AgentEvent」）以便落地。*
