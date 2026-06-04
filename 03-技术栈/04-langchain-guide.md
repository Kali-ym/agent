# LangChain 框架指南

> 本文面向已经理解 Agent、RAG、上下文工程基本概念的读者。目标不是罗列 LangChain API，而是说明：什么时候该用 LangChain，怎么把它放进一个可维护的 Agent 系统里，以及如何避免“框架用得很多，系统却不可控”的问题。

---

## 1. 先给结论

LangChain 适合做三类事情：

1. **快速搭建 LLM 应用管线**：提示词、模型、解析器、检索器、工具、记忆、回调等组件已有大量封装。
2. **把 RAG 和工具调用串起来**：适合做知识库问答、文档助手、研究助手、轻量工作流 Agent。
3. **向 LangGraph 过渡**：当普通 Chain 不够表达状态机、分支、循环、恢复和多 Agent 编排时，使用 LangGraph 承接更复杂的 Agent 运行时。

但它不适合替代工程设计。LangChain 能降低集成成本，不能自动解决上下文污染、工具越权、状态混乱、评估缺失和生产可观测性问题。

在本项目的知识体系里，LangChain 应该被放在下面这个位置：

```text
Agent 系统
├── 上下文工程：决定什么信息进入模型
├── Agent Loop：决定任务如何推进
├── 工具系统：决定模型能调用什么能力
├── 记忆系统：决定历史和知识如何沉淀
├── RAG 系统：决定外部知识如何检索和引用
├── 评估系统：决定系统是否真的变好了
└── LangChain / LangGraph：提供组件封装和编排框架
```

如果你只记一句话：**LangChain 是组件库和编排层，不是 Agent 架构本身。**

---

## 2. LangChain 解决什么问题

### 2.1 没有框架时的典型状态

手写一个 LLM 应用通常会快速遇到这些重复问题：

- 模型供应商不同，调用方式不同。
- Prompt 模板越来越多，缺少统一管理方式。
- 输出格式不稳定，需要解析和校验。
- RAG 要处理加载、切分、向量化、检索、重排和引用。
- 工具调用需要 schema、权限、错误处理和 trace。
- 多轮对话需要短期记忆、摘要和长期记忆。
- 线上问题很难复盘，因为没有完整运行轨迹。

LangChain 的价值，就是把这些重复模块抽象成可复用组件。

### 2.2 LangChain 的核心边界

| 它能帮你做                                 | 它不能替你做            |
| :------------------------------------ | :---------------- |
| 快速接入模型、Embedding、向量库、工具和文档加载器         | 判断业务上该给模型哪些上下文    |
| 用统一接口组合 Prompt、Model、Parser、Retriever | 设计稳定的状态机和失败恢复策略   |
| 快速验证 RAG、工具调用和 Agent 原型               | 保证答案可靠、引用真实、成本可控  |
| 接入 LangSmith 做 trace 和调试              | 自动建立完整 eval 体系    |
| 使用 LangGraph 表达循环和分支                  | 替代你对权限、安全、观测的工程治理 |

更务实的判断标准：

- **学习和原型阶段**：LangChain 很适合。
- **知识库问答和轻量工具 Agent**：LangChain + LangGraph 很适合。
- **强状态、强合规、强可控的生产 Agent**：可以借用 LangChain 组件，但核心状态、权限、上下文构建和评估最好掌握在自己手里。

---

## 3. LangChain 生态地图

LangChain 现在不只是一个包，而是一组分层生态。

```text
LangChain 生态
├── LangChain Core
│   ├── PromptTemplate
│   ├── ChatModel 抽象
│   ├── OutputParser
│   ├── Runnable / LCEL
│   └── Message / Document 基础结构
│
├── LangChain Integrations
│   ├── OpenAI / Anthropic / Google / Ollama 等模型
│   ├── Chroma / FAISS / Qdrant / Milvus 等向量库
│   ├── Web / PDF / Markdown / HTML 等文档加载器
│   └── 搜索、数据库、浏览器、API 等工具集成
│
├── LangGraph
│   ├── 状态图
│   ├── 分支与循环
│   ├── checkpoint
│   ├── human-in-the-loop
│   └── 多 Agent 编排
│
└── LangSmith
    ├── trace
    ├── dataset
    ├── prompt / run 对比
    ├── eval
    └── 线上调试与观测
```

简单理解：

- **LangChain**：负责组件和链式组合。
- **LangGraph**：负责有状态 Agent 工作流。
- **LangSmith**：负责调试、评估和观测。

---

## 4. 核心概念

### 4.1 Model：模型不是系统，只是一个无状态转换器

LLM 本质上接收上下文，输出文本或结构化结果。Agent 系统做得好不好，关键不是“调了哪个模型”，而是：

- 给它什么任务说明。
- 给它什么历史状态。
- 给它什么工具定义。
- 给它什么检索证据。
- 要求它输出什么结构。
- 失败时如何把错误反馈回去。

这与本项目反复强调的 [[11-context-engineering-practices|上下文工程]] 是同一个核心思想。

### 4.2 Prompt：提示词是可维护资产

Prompt 不应该散落在业务代码里。推荐按用途分层管理：

```text
prompts/
├── system/
│   ├── assistant.md
│   └── reviewer.md
├── rag/
│   ├── answer-with-citations.md
│   └── query-rewrite.md
└── agent/
    ├── planner.md
    ├── tool-router.md
    └── final-answer.md
```

一个可维护的 Prompt 至少包含：

- 角色和边界。
- 输入字段说明。
- 可用证据说明。
- 输出格式。
- 禁止行为。
- 失败时的处理方式。

### 4.3 Runnable / LCEL：把组件组合成数据流

LangChain 的现代组合方式可以理解成一条数据流：

```text
输入
  -> Prompt
  -> Model
  -> Output Parser
  -> 结构化结果
```

它的价值不在于“语法更短”，而在于让每一段职责清晰：

- Prompt 负责组织上下文。
- Model 负责生成。
- Parser 负责把输出变成稳定结构。
- Retriever / Tool 可以插入到数据流中。

### 4.4 Output Parser：把自由文本变成可控结构

自由文本适合聊天，不适合系统协作。Agent 工程里更推荐让模型输出结构化对象，例如：

```json
{
  "intent": "search_documents",
  "query": "Agent Memory 三层架构",
  "reason": "需要先检索项目内已有说明"
}
```

这和 [[12-factor-agent-architecture|12-Factor Agent 架构]] 中“工具即结构化输出”的观点一致：模型决定要做什么，确定性代码决定怎么执行。

### 4.5 Retriever：RAG 不是塞资料，而是选择上下文

Retriever 的职责不是“多找点资料”，而是从外部知识中选择最相关、最可信、最适合当前任务的片段。

常见链路：

```text
用户问题
  -> Query Rewrite
  -> 多路召回
  -> 去重
  -> Rerank
  -> 上下文压缩
  -> 带引用回答
```

这部分建议配合 [[20-rag-full-pipeline|RAG 全链路实战]] 和 [[08-vector-db-basics|向量数据库基础]] 学习。

### 4.6 Tools：工具调用要有白名单、schema 和错误结构

工具不是“让模型随便执行代码”。一个合格工具至少有：

| 项目 | 说明 |
|:---|:---|
| 名称 | 模型看到的能力入口 |
| 描述 | 什么时候应该使用，什么时候不该使用 |
| 输入 schema | 参数类型、必填项、约束 |
| 输出 schema | 成功、失败、部分结果的统一结构 |
| 权限 | 是否需要用户确认，是否有读写边界 |
| 观测 | 每次调用记录参数、结果、耗时和错误 |

推荐工具返回结构：

```json
{
  "ok": false,
  "error": "not_found",
  "retryable": false,
  "message": "没有找到匹配文档",
  "partial_result": []
}
```

### 4.7 Memory：不要把所有历史都塞进上下文

LangChain 早期的 memory 很容易让人误解为“保存完整聊天历史”。实际生产里更合理的是分层记忆：

```text
Working Memory：当前任务状态和最近交互
Episodic Memory：本次会话关键事件
Semantic Memory：长期偏好、事实和知识
```

这部分建议直接阅读 [[15-agent-memory|Agent Memory - 从原理到实战]]。

---

## 5. 最小开发环境

Python 项目常见依赖：

```bash
pip install langchain langgraph langsmith langchain-openai langchain-community
```

如果要做本地向量库原型，可以加：

```bash
pip install langchain-chroma chromadb
```

如果使用 `.env` 管理密钥：

```bash
pip install python-dotenv
```

典型环境变量：

```bash
OPENAI_API_KEY=your_api_key
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=agent-guide-demo
```

注意：不要把真实密钥写进笔记、仓库或示例代码。

---

## 6. 最小 Chain：从问题到结构化回答

最小 Chain 的目标不是“能聊天”，而是建立一个可组合的数据流。

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个技术文档助手。回答要简洁、准确，并明确不确定性。"),
    ("user", "问题：{question}"),
])

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
parser = StrOutputParser()

chain = prompt | model | parser

answer = chain.invoke({
    "question": "LangChain 和 LangGraph 的区别是什么？"
})

print(answer)
```

这条链路的模块关系：

```text
question
  -> prompt：组织任务说明
  -> model：生成回答
  -> parser：转成普通字符串
  -> answer
```

实际项目里可以继续把 Parser 换成 JSON / Pydantic 结构，把输入换成包含任务状态、证据片段、工具结果的上下文对象。

---

## 7. RAG：用 LangChain 搭知识库问答

### 7.1 RAG 的目标

一个好的 RAG 系统不是“回答得像”，而是满足：

- 能找到相关资料。
- 能过滤无关资料。
- 能引用证据。
- 不知道时能说不知道。
- 能复盘每次用了哪些片段。

### 7.2 基础链路

```text
文档
  -> 加载
  -> 切分
  -> 向量化
  -> 入库
  -> 检索
  -> 生成带证据回答
```

### 7.3 示例骨架

```python
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

vectorstore = Chroma(
    collection_name="agent_notes",
    embedding_function=OpenAIEmbeddings(),
    persist_directory="./chroma_db",
)

retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

prompt = ChatPromptTemplate.from_template("""
你是一个严谨的知识库助手。
只能基于给定资料回答；如果资料不足，直接说明不足。

资料：
{context}

问题：
{question}
""")

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

rag_chain = prompt | model | StrOutputParser()

docs = retriever.invoke("Agent Memory 的三层架构是什么？")
context = "\n\n".join(doc.page_content for doc in docs)

answer = rag_chain.invoke({
    "context": context,
    "question": "Agent Memory 的三层架构是什么？"
})

print(answer)
```

### 7.4 RAG 工程检查清单

| 检查项 | 判断标准 |
|:---|:---|
| 文档切分 | 片段能独立表达完整语义，不被切断关键上下文 |
| 元数据 | 至少保留来源、标题、页码或章节 |
| 检索质量 | 有固定 query 集合验证召回率和相关性 |
| 引用格式 | 每条关键结论能回到原文证据 |
| 不足处理 | 没有证据时不编造 |
| Trace | 保存 query、召回片段、最终回答和成本 |

---

## 8. Agent：从 Chain 升级到可控循环

### 8.1 不要一上来就做“全自动 Agent”

很多 LangChain 初学者会直接把一堆工具交给模型，让它自由规划。这种方式很快能做 demo，但也很容易失控：

- 模型不知道什么时候停。
- 工具参数经常不稳定。
- 错误会污染后续上下文。
- 状态和业务数据混在一起。
- 失败后不知道问题出在哪一步。

更稳的做法是先实现最小 Agent Loop，再把 LangChain 组件嵌进去。

### 8.2 推荐状态结构

```text
Agent State
├── task：用户目标
├── success_criteria：成功标准
├── steps：已执行步骤
├── evidence：已确认事实和证据
├── artifacts：中间产物
├── errors：失败记录
├── budget：步数、时间和成本预算
└── final：最终结果
```

### 8.3 LangChain 在 Agent Loop 中的位置

```text
用户任务
  -> Context Builder
  -> LangChain Prompt / Model / Parser
  -> 结构化 action
  -> 工具白名单执行
  -> observation
  -> 更新 state
  -> 下一轮
```

这个结构和 [[../07-项目与示例/examples/minimal-agent-loop|最小 Agent Loop 模板]] 是一致的。

### 8.4 什么时候用 LangGraph

当你的 Agent 出现下面任意情况，就应该考虑 LangGraph：

| 触发条件 | 为什么 Chain 不够 |
|:---|:---|
| 需要循环执行 | Chain 更像单向数据流，不擅长表达循环状态 |
| 需要多分支 | 不同任务路径需要显式路由 |
| 需要人工确认 | 中间节点要暂停、等待、恢复 |
| 需要失败重试 | 错误分支需要可控处理 |
| 需要长期任务 | 需要 checkpoint 和恢复 |
| 需要多 Agent | 多角色之间要有明确交接关系 |

LangGraph 更像“Agent 状态机”，LangChain 更像“组件工具箱”。

---

## 9. LangSmith：没有 Trace 就没有工程化

Agent 失败时，单看最终答案几乎没用。你需要知道：

- 输入是什么。
- Prompt 实际长什么样。
- 检索到了哪些文档。
- 模型输出了什么 action。
- 调用了什么工具。
- 工具返回了什么。
- 哪一步开始偏离。
- 总成本和延迟是多少。

LangSmith 主要解决三件事：

```text
Trace：记录一次运行的完整轨迹
Dataset：沉淀可复现测试集
Eval：对不同版本 Prompt、模型、检索策略做对比
```

它和 [[26-agent-evaluation-harness-guide|Agent Evaluation Harness]] 的关系是：

- LangSmith 更偏 LLM 应用的调试、数据集和在线观测。
- Evaluation Harness 更偏系统化评估框架和任务套件。
- 生产系统通常两者都需要，或者至少需要自建等价能力。

---

## 10. 推荐项目结构

轻量 RAG / Agent 项目可以按下面组织：

```text
app/
├── chains/
│   ├── answer_chain.py
│   ├── rewrite_chain.py
│   └── judge_chain.py
├── graphs/
│   └── research_graph.py
├── prompts/
│   ├── rag_answer.md
│   ├── planner.md
│   └── reviewer.md
├── tools/
│   ├── search.py
│   ├── document.py
│   └── sandbox.py
├── memory/
│   ├── short_term.py
│   └── long_term.py
├── retrieval/
│   ├── ingest.py
│   ├── retriever.py
│   └── reranker.py
├── evals/
│   ├── cases.jsonl
│   ├── graders.py
│   └── run_eval.py
└── observability/
    └── tracing.py
```

核心原则：

- Prompt 单独管理。
- 工具单独管理。
- 检索链路单独管理。
- Agent 状态单独管理。
- Eval 和 trace 从第一天就保留。

---

## 11. 常见模式

### 11.1 文档问答

```text
用户问题
  -> query rewrite
  -> retriever
  -> rerank / compress
  -> answer with citations
  -> confidence check
```

适合：知识库、政策问答、企业文档助手。

关键风险：检索不到、引用不支持结论、文档版本过期。

### 11.2 研究助手

```text
用户主题
  -> 拆解研究问题
  -> 多源搜索
  -> 资料去重和排序
  -> 证据抽取
  -> 综述生成
  -> 审稿式复核
```

适合：论文综述、行业调研、竞品分析。

可参考 [[../07-项目与示例/projects/01-paper-agent/README|Paper Agent：论文研读与综述助手]]。

### 11.3 工具型 Agent

```text
用户请求
  -> intent 识别
  -> 工具选择
  -> 参数生成
  -> 权限确认
  -> 工具执行
  -> 结果解释
```

适合：工单助手、数据查询助手、自动化办公助手。

关键风险：权限、误操作、工具错误反馈不清晰。

### 11.4 多步骤工作流

```text
目标
  -> planner
  -> executor
  -> verifier
  -> revise or finish
```

适合：代码修改、报告生成、数据分析、运维排查。

当状态分支明显变多时，建议从 Chain 迁移到 LangGraph。

---

## 12. 常见坑

### 12.1 把 LangChain 当“魔法 Agent”

错误心态：接好工具，模型自己会规划。

正确心态：模型只负责不确定决策，流程、状态、权限和失败处理由系统控制。

### 12.2 把完整历史都塞进上下文

问题：成本高、噪声多、旧错误会污染新判断。

更好的方式：

```text
完整历史 -> 摘要 / 重要事实 / 可检索记忆 -> 当前任务上下文
```

### 12.3 RAG 只看“回答像不像”

RAG 的关键指标不是流畅度，而是：

- 召回是否相关。
- 结论是否被证据支持。
- 没有证据时是否拒答。
- 引用是否能追溯。

### 12.4 工具过多且描述模糊

工具越多，模型越容易选错。工具描述越模糊，参数越容易错。

推荐做法：

- 工具按场景分组召回。
- 当前任务只暴露必要工具。
- 每个工具写清楚适用场景和禁止场景。
- 工具错误返回结构化信息。

### 12.5 没有 Eval 就反复调 Prompt

没有固定测试集时，Prompt 优化很容易变成玄学。

最小可用 eval：

```text
20 条真实任务
├── 10 条正常任务
├── 5 条边界任务
├── 3 条错误输入
└── 2 条安全/拒答任务
```

每次改 Prompt、模型、切分策略、检索参数，都跑同一批用例对比。

---

## 13. 选型建议

### 13.1 什么时候直接用 LangChain

适合：

- 快速验证想法。
- 做知识库问答 MVP。
- 接入多个模型或向量库。
- 需要大量现成 loader / retriever / tool。
- 团队还在探索阶段。

### 13.2 什么时候用 LangGraph

适合：

- 任务有明确状态流转。
- 需要循环、分支、暂停和恢复。
- 需要多 Agent 协作。
- 需要 human-in-the-loop。
- 需要长期运行和 checkpoint。

### 13.3 什么时候减少框架依赖

适合：

- 核心业务强依赖稳定性和可审计性。
- 工具调用有强权限边界。
- 状态机已经非常明确。
- 需要细粒度成本、延迟和错误控制。
- 团队已经有成熟工程基础设施。

这时可以只保留 LangChain 的局部组件，例如模型适配、Embedding、文档加载器，而把 Agent Loop、Context Builder、权限系统和评估系统自研。

---

## 14. 学习路线

建议按下面顺序学习：

1. 先读 [[01-what-is-agent|什么是 Agent]]，理解 Agent 不是聊天机器人。
2. 再读 [[04-react-framework|ReAct 框架]]，理解推理和行动循环。
3. 再读 [[05-cot-and-planning|CoT 与规划]]，理解复杂任务拆解。
4. 再读 [[11-context-engineering-practices|上下文工程实践]]，理解信息流控制。
5. 回到本文，学习 LangChain 如何承接组件组合。
6. 继续读 [[12-factor-agent-architecture|12-Factor Agent 架构]]，理解生产级 Agent 的控制边界。
7. 结合 [[15-agent-memory|Agent Memory]]、[[20-rag-full-pipeline|RAG 全链路实战]] 和 [[26-agent-evaluation-harness-guide|Evaluation Harness]] 做完整项目。

---

## 15. 推荐实战：用 LangChain 做一个 Paper Agent MVP

目标：构建一个论文研读助手。

MVP 范围：

```text
用户输入研究主题
  -> arXiv / Semantic Scholar 检索
  -> PDF 或摘要解析
  -> 文献去重和排序
  -> 证据片段抽取
  -> 生成带引用综述
  -> 保存 trace 和 eval 结果
```

LangChain 可承担：

| 模块 | LangChain 角色 |
|:---|:---|
| Query Rewrite | Prompt + Model + Parser |
| 文档解析 | Document Loader |
| 向量检索 | Embedding + VectorStore + Retriever |
| 证据回答 | RAG Chain |
| 工具调用 | Tool schema 和执行封装 |
| 运行观测 | LangSmith trace |

自研或重点控制：

| 模块 | 原因 |
|:---|:---|
| Agent State | 任务状态要可恢复、可复盘 |
| Evidence Store | 结论必须能追溯到来源 |
| Eval Cases | 判断系统是否真的变好 |
| 权限和下载边界 | 避免越权、误下载和不可控访问 |

项目说明可参考 [[../07-项目与示例/projects/01-paper-agent/README|Paper Agent：论文研读与综述助手]]。

---

## 16. 面试表达

如果面试官问“你了解 LangChain 吗”，不要只说“会用 Chain、Agent、Memory”。更好的回答结构是：

```text
我把 LangChain 理解为 LLM 应用组件库，主要价值是统一模型、Prompt、Parser、Retriever、Tool 等组件的组合方式。

但在生产级 Agent 里，我不会把控制权完全交给框架。我的设计会把 Agent 拆成 Context Builder、状态机、工具白名单、RAG、Memory、Trace 和 Eval 几层。

LangChain 可以负责局部组件集成；如果任务有循环、分支、恢复和人工确认，我会用 LangGraph 表达状态流转；如果要调试和评估，我会接 LangSmith 或自建等价 trace/eval 能力。
```

这类回答能体现你知道框架，也知道框架边界。

---

## 17. 总结

LangChain 的正确打开方式：

- 用它快速组合 LLM 应用组件。
- 用 LangGraph 管理复杂 Agent 状态流。
- 用 LangSmith 或等价系统保留 trace 和 eval。
- 把上下文、状态、工具、权限和评估握在自己手里。

最终目标不是“写一个 LangChain Demo”，而是构建一个可解释、可复盘、可评估、可迭代的 Agent 系统。
