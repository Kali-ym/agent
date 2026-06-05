# 向量数据库基础

> 本文是 [[04-langchain-guide|LangChain 框架指南]] 第 7 节 RAG 的配套深度文档。LangChain 文档讲「怎么把检索串进 Chain」，本文讲「向量数据库本身是什么、怎么选、怎么用、怎么避坑」。

---

## 1. 先给结论

向量数据库（Vector Database）是专门存储和检索 **Embedding 向量** 的数据系统。在 Agent / RAG 体系里，它的职责很单一：

```text
把文本（或图片、音频）变成向量
  -> 按语义相似度快速找回最相关的片段
  -> 作为 LLM 的「外部记忆」注入上下文
```

如果说 Embedding 模型负责「把语言变成坐标」，向量数据库负责「在这个坐标空间里快速找邻居」。

向量数据库最适合处理这类问题：

- RAG 知识库：文档问答、企业知识库、论文助手。
- Agent Memory：情节记忆、语义记忆的长期存储与检索。
- 相似内容推荐：找相似案例、相似代码、相似工单。
- 多模态检索：图文混合搜索。

但它**不能**单独解决 RAG 质量问题。向量库只负责「召回候选」，不负责：

- 文档切分是否合理。
- Embedding 模型是否匹配业务域。
- 检索结果是否经过重排和过滤。
- 最终回答是否有证据支撑。

在本项目知识体系里，向量数据库应该被放在这里：

```text
RAG / Memory 系统
├── 文档加载与切分     ← 决定片段质量
├── Embedding 模型    ← 决定语义表示质量
├── 向量数据库        ← 本文：存储与相似度检索
├── 检索策略          ← 混合检索、重排、查询改写
├── 上下文注入        ← 决定什么进入 LLM
└── 评估体系          ← 判断检索是否真的变好了
```

如果你只记一句话：**向量数据库是 RAG 的「召回层」，不是 RAG 的全部。**

---

## 2. 向量数据库解决什么问题

### 2.1 没有向量库时的典型状态

传统关键词搜索（BM25 / Elasticsearch）擅长精确匹配，但在 Agent 场景很快遇到瓶颈：

- 用户问「怎么提升 Agent 的记忆力」，文档里写的是「Memory 系统设计」——关键词对不上。
- 同义词、改写、跨语言查询无法语义对齐。
- 百万级文档暴力算余弦相似度，延迟不可接受。
- 检索结果缺少结构化元数据过滤（按部门、时间、权限）。

向量数据库的价值，就是把「语义相似度搜索」做成可扩展的基础设施。

### 2.2 向量库的核心边界

| 它能帮你做 | 它不能替你做 |
|:---|:---|
| 高效存储和检索高维向量 | 判断文档该怎么切分 |
| 按相似度返回 Top-K 候选 | 保证 Top-K 一定相关 |
| 元数据过滤（部分产品） | 自动做权限控制和合规审计 |
| 支持增量写入和索引更新 | 自动选择最佳 Embedding 模型 |
| 水平扩展（生产级产品） | 替代 Reranker 和 Eval 体系 |

更务实的判断标准：

- **学习和原型阶段**：Chroma 或 FAISS 足够，30 分钟能跑通。
- **本地实验 / 算法研究**：FAISS 性能最强、算法最全。
- **中小规模生产（< 500 万向量）**：Qdrant 或 Milvus Standalone。
- **大规模分布式生产**：Milvus 集群或 Zilliz Cloud。
- **不想管基础设施**：Pinecone 等托管服务。

---

## 3. 向量数据库在项目知识体系中的位置

```text
Agent 工程体系
├── 理论基础
│   ├── [[03-transformer|Transformer 基础]]（Embedding 来源）
│   └── [[05-cot-and-planning|CoT 与规划]]
│
├── 上下文工程
│   ├── [[11-context-engineering-practices|上下文工程实践]]（Retrieve 策略）
│   ├── [[14-context-engineering|长上下文问题与修复]]
│   └── [[18-context-engineering-guide|上下文工程完全指南]]
│
├── RAG 管线
│   ├── [[04-langchain-guide|LangChain 框架指南]]（RAG Chain 组装）
│   ├── 本文：向量数据库存储与检索
│   └── [[20-rag-full-pipeline|RAG 全链路实战]]（完整管线）
│
├── Memory
│   └── [[15-agent-memory|Agent Memory]]（向量库作为 L2/L3 存储）
│
└── 质量保障
    └── [[26-agent-evaluation-harness-guide|Evaluation Harness]]（检索质量评估）
```

它承接的是：

```text
文档切分 + Embedding
  -> 向量入库（本文）
  -> 相似度检索
  -> 混合检索 / Rerank
  -> 上下文注入 LLM
  -> Eval 验证召回质量
```

---

## 4. 核心原理

### 4.1 从文本到向量

```text
原始文本："Agent Memory 的三层架构"
  -> Tokenize
  -> Embedding 模型（如 text-embedding-3-small、bge-m3）
  -> 向量：[0.12, -0.34, 0.56, ...]（通常 384 ~ 3072 维）
```

关键认知：

| 概念 | 说明 |
|:---|:---|
| Embedding | 把变长文本映射到固定维度浮点向量 |
| 语义相似 | 向量空间中距离近 ≈ 语义相近 |
| 维度 | 越高通常表达能力越强，但存储和计算成本也更高 |
| 模型选择 | 通用模型 vs 领域微调模型，对召回质量影响极大 |

**项目视角**：Embedding 模型和向量库是绑定的——换模型通常需要**重建全部索引**。

### 4.2 相似度度量

最常见的三种距离/相似度：

| 度量 | 公式直觉 | 适用场景 |
|:---|:---|:---|
| 余弦相似度（Cosine） | 向量夹角，忽略长度 | **最常用**，文本 Embedding 默认 |
| 欧氏距离（L2） | 空间直线距离 | FAISS 默认，部分图像场景 |
| 内积（IP / Dot Product） | 向量点乘 | 归一化向量上等价于余弦 |

大多数现代向量库默认用余弦相似度或归一化后的内积。

### 4.3 近似最近邻（ANN）

精确搜索（暴力遍历）在百万级以上不可行。向量库用 **ANN 索引** 做近似搜索，用少量精度换取数量级的速度提升。

```text
精确搜索：遍历全部向量，O(N)，慢但准
ANN 搜索：通过索引结构快速定位候选区域，O(log N)，快但有召回损失
```

工程上要在「检索速度」和「召回率」之间做权衡，通过索引参数调节。

### 4.4 三种核心索引算法

| 算法 | 原理 | 速度 | 召回精度 | 内存 | 适合场景 |
|:---|:---|:---|:---|:---|:---|
| **FLAT** | 暴力遍历，精确搜索 | 慢 | 最高（100%） | 高 | 小数据集（< 10 万）、基准测试 |
| **IVF** | 先聚类分区，只搜相关分区 | 快 | 中高 | 中 | 百万级，可接受少量损失 |
| **HNSW** | 多层图结构，贪心导航 | 很快 | 高 | 较高 | **生产默认首选**，百万~亿级 |

选型建议：

```text
原型 / 小数据（< 10 万）  -> FLAT 或 HNSW
生产中等规模（10 万 ~ 1000 万） -> HNSW
超大规模（> 1000 万）     -> IVF + PQ 量化，或 Milvus 分布式
```

**IVF-PQ** 是 IVF 的进阶：在分区基础上对向量做乘积量化压缩，大幅降内存，适合算法岗做索引优化实验（见 [[06-路线图/learning-roadmap-algorithm|算法岗学习路线]]）。

---

## 5. 数据模型

无论选哪个向量库，概念模型基本一致：

```text
Collection（集合）
  └── Record / Point（记录）
        ├── id          — 唯一标识
        ├── vector      — Embedding 向量（float[]）
        ├── payload     — 原始文本或摘要
        └── metadata    — 结构化附加信息
```

### 5.1 元数据（Metadata）设计

元数据决定了你能否做**过滤检索**，是生产系统的关键：

```python
# 推荐的 metadata 字段
metadata = {
    "source": "agent/03-技术栈/15-agent-memory.md",  # 来源路径
    "title": "Agent Memory 从原理到实战",
    "section": "三层记忆架构",
    "doc_type": "tutorial",
    "created_at": "2025-11-01",
    "access_level": "public",       # 权限过滤
    "chunk_index": 3,               # 片段序号
    "parent_id": "doc_001",         # 父文档 ID
}
```

| 原则 | 说明 |
|:---|:---|
| 每条向量都带 source | 回答必须能追溯到原文 |
| 保留 chunk_index | 支持上下文扩展（取相邻片段） |
| 设计权限字段 | 多租户 / 部门隔离靠 metadata filter |
| 避免过大 payload | 向量库不是文档存储，原文放对象存储 |

### 5.2 Collection 版本管理

换 Embedding 模型或切分策略时，不要原地覆盖：

```text
collections/
├── agent_notes_v1_bge-m3_512tok   ← 旧版，保留用于对比
├── agent_notes_v2_bge-m3_256tok   ← 当前生产
└── agent_notes_v3_experiment      ← 实验中
```

这样你可以用同一套 eval query 对比不同索引配置的召回质量。

---

## 6. 主流产品对比

### 6.1 快速选型表

| 向量库 | 类型 | 规模上限 | 部署 | 过滤能力 | 适合场景 | 推荐度 |
|:---|:---|:---|:---|:---|:---|:---:|
| **Chroma** | 嵌入式库 | < 10 万 | 本地文件 | 基础 | 原型、学习 | ⭐⭐⭐⭐ |
| **FAISS** | 算法库 | 取决于内存 | 本地 | 无（需自研） | 实验、算法研究 | ⭐⭐⭐⭐⭐ |
| **Qdrant** | 独立服务 | 亿级 | Docker / 云 | 强 | 生产、性能敏感 | ⭐⭐⭐⭐ |
| **Milvus** | 分布式系统 | 十亿级 | Docker / K8s | 强 | 大规模生产 | ⭐⭐⭐⭐⭐ |
| **Pinecone** | 托管 SaaS | 自动扩展 | 零运维 | 强 | 快速上线、MVP | ⭐⭐⭐⭐ |
| **pgvector** | PG 扩展 | 百万级 | 已有 PG 即可 | SQL 级 | 已有 PG 栈的团队 | ⭐⭐⭐ |
| **Weaviate** | 独立服务 | 亿级 | Docker / 云 | 强（GraphQL） | 多模态、GraphQL 偏好 | ⭐⭐⭐ |

更详细的性能数据和链接见 [[../08-资源/rag/vector-db|向量数据库选型指南（资源）]]。

### 6.2 逐个速览

#### Chroma — 原型首选

```python
import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("agent_notes")

collection.add(
    documents=["Agent Memory 分工作记忆、情节记忆、语义记忆三层"],
    metadatas=[{"source": "15-agent-memory.md", "section": "架构"}],
    ids=["chunk_001"],
)

results = collection.query(
    query_texts=["Memory 系统怎么分层？"],
    n_results=5,
    where={"source": "15-agent-memory.md"},  # metadata 过滤
)
```

- 优势：5 行代码、自动持久化、与 LangChain 深度集成。
- 劣势：不支持分布式，大规模性能不足。
- 学习成本：30 分钟。

#### FAISS — 本地性能之王

```python
import faiss
import numpy as np

d = 768  # 向量维度
n = 10000  # 向量数量

# 构建 HNSW 索引
index = faiss.IndexHNSWFlat(d, 32)  # 32 个邻居
index.add(vectors.astype("float32"))

# 检索 Top-5
D, I = index.search(query_vector.reshape(1, -1).astype("float32"), k=5)
```

- 优势：Facebook 出品，20+ 索引算法，CPU/GPU 都支持，百万级 QPS 10000+。
- 劣势：只是算法库，没有服务端、没有 metadata 过滤、没有持久化 API。
- 适合：算法实验、本地 benchmark、作为其他系统的底层索引引擎。

#### Qdrant — Rust 性能 + 强过滤

```python
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, Filter, FieldCondition, MatchValue

client = QdrantClient(url="http://localhost:6333")

client.create_collection(
    collection_name="agent_notes",
    vectors_config=VectorParams(size=768, distance=Distance.COSINE),
)

client.upsert(
    collection_name="agent_notes",
    points=[{
        "id": 1,
        "vector": embedding,
        "payload": {"text": "...", "source": "15-agent-memory.md", "access_level": "public"},
    }],
)

results = client.search(
    collection_name="agent_notes",
    query_vector=query_embedding,
    limit=5,
    query_filter=Filter(must=[
        FieldCondition(key="access_level", match=MatchValue(value="public")),
    ]),
)
```

- 优势：Rust 编写性能好，过滤表达式强大，支持多向量（ColBERT 等）。
- 劣势：生态不如 Milvus 成熟。
- 适合：性能敏感的中大规模生产。

#### Milvus — 大规模生产首选

```python
from pymilvus import MilvusClient

client = MilvusClient(uri="http://localhost:19530")

client.create_collection(
    collection_name="agent_notes",
    dimension=768,
    metric_type="COSINE",
)

client.insert(
    collection_name="agent_notes",
    data=[{
        "id": 1,
        "vector": embedding,
        "text": "...",
        "source": "15-agent-memory.md",
    }],
)

results = client.search(
    collection_name="agent_notes",
    data=[query_embedding],
    limit=5,
    filter='source == "15-agent-memory.md"',
    output_fields=["text", "source"],
)
```

- 优势：分布式架构、十亿级向量、多种索引、GPU 加速、云原生。
- 劣势：部署复杂度高，Standalone 模式适合中小规模。
- 适合：企业级 RAG、Paper Agent 等需要高可用的场景。
- 部署：`docker compose up -d`（Standalone）或 K8s + Helm（集群）。

#### Pinecone — 零运维托管

- 优势：完全托管、自动扩展、开箱即用。
- 劣势：收费、数据在第三方、国内访问可能受限。
- 适合：创业公司 MVP、不想管基础设施的团队。

#### pgvector — 已有 PostgreSQL 的最简方案

```sql
CREATE EXTENSION vector;
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    content TEXT,
    embedding vector(768),
    metadata JSONB
);
CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops);
```

- 优势：不引入新组件，SQL 生态完整，事务支持。
- 劣势：百万级以上性能不如专用向量库。
- 适合：已有 PG 栈、向量规模 < 100 万的团队。

---

## 7. 选型决策

### 7.1 决策树

```text
你的需求是什么？
│
├─ 学习 / 快速原型
│   └─ Chroma（最简单，配合 LangChain 开箱即用）
│
├─ 算法实验 / 索引优化
│   └─ FAISS（算法最全，性能 benchmark 标准工具）
│
├─ 生产环境
│   ├─ 不想管基础设施
│   │   └─ Pinecone（托管）或 Zilliz Cloud（Milvus 托管）
│   ├─ 数据量 < 500 万，追求性能
│   │   └─ Qdrant
│   ├─ 数据量 > 500 万，需要分布式
│   │   └─ Milvus
│   └─ 已有 PostgreSQL 且规模不大
│       └─ pgvector
│
└─ Agent Memory 存储
    └─ 小规模：Chroma / SQLite + 向量扩展
       中大规模：Qdrant / Milvus（配合 [[15-agent-memory|Agent Memory]] 设计）
```

### 7.2 本项目推荐路径

结合 [[06-路线图/learning-roadmap-development|开发岗学习路线]]：

| 阶段 | 推荐向量库 | 原因 |
|:---|:---|:---|
| 第 1 周 Naive RAG | Chroma | 最快跑通端到端 |
| 第 2 周 Advanced RAG | Milvus | 学习生产级部署和 SDK |
| 项目作品集 | Milvus + Redis | Paper Agent 等高可用场景 |
| 算法实验 | FAISS | 索引优化、量化、混合检索 benchmark |

---

## 8. 与 RAG 管线的集成

### 8.1 向量库在 RAG 中的位置

```text
                    ┌──────────────┐
  用户问题 ──────────>│ Query Rewrite │（可选：HyDE、Multi-Query）
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │   向量检索     │ ← 本文核心：Top-K 召回
                    │  (+ BM25)    │ ← 混合检索
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │   Reranker   │（可选：Cohere、BGE-Reranker）
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  上下文注入    │ → LLM 生成带引用回答
                    └──────────────┘
```

向量库只覆盖「向量检索」这一步。完整 RAG 管线见 [[20-rag-full-pipeline|RAG 全链路实战]]。

### 8.2 LangChain 集成示例

与 [[04-langchain-guide|LangChain 框架指南]] 第 7 节衔接：

```python
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

# 1. 准备文档（切分后）
docs = [
    Document(
        page_content="Agent Memory 分三层：工作记忆、情节记忆、语义记忆。",
        metadata={"source": "15-agent-memory.md", "section": "架构"},
    ),
    # ... 更多片段
]

# 2. 创建向量库并入库
vectorstore = Chroma.from_documents(
    documents=docs,
    embedding=OpenAIEmbeddings(model="text-embedding-3-small"),
    collection_name="agent_notes",
    persist_directory="./chroma_db",
)

# 3. 创建 Retriever
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 5},
)

# 4. 检索
results = retriever.invoke("Memory 系统怎么设计？")
for doc in results:
    print(f"[{doc.metadata['source']}] {doc.page_content[:80]}...")
```

切换到 Milvus：

```python
from langchain_milvus import Milvus

vectorstore = Milvus.from_documents(
    documents=docs,
    embedding=OpenAIEmbeddings(model="text-embedding-3-small"),
    connection_args={"uri": "http://localhost:19530"},
    collection_name="agent_notes",
)
```

框架层换库很容易，但**索引质量取决于切分、Embedding 和 eval，不取决于 LangChain 封装**。

### 8.3 混合检索（Hybrid Search）

纯向量检索的弱点：精确关键词匹配差（如产品型号、错误码、人名）。

```text
混合检索 = 向量检索（语义） + BM25（关键词）
  -> 分数融合（RRF 或加权）
  -> 去重
  -> Top-K
```

| 方法 | 说明 |
|:---|:---|
| RRF（Reciprocal Rank Fusion） | 按排名倒数加权融合，简单有效 |
| 加权融合 | `score = α × vector_score + (1-α) × bm25_score` |
| Milvus 2.5+ | 原生支持 BM25 + Dense 混合检索 |
| Qdrant | 通过 payload 索引 + 稀疏向量支持 |

开发岗学习路线第 2 周要求实现 BM25 + 向量混合检索，这是从 Naive RAG 到 Advanced RAG 的关键一步。

---

## 9. 与 Agent Memory 的关系

[[15-agent-memory|Agent Memory]] 推荐的三层架构中，向量库出现在两层：

```text
Layer 1: 工作记忆 — 内存（最近 10-20 轮对话）
Layer 2: 情节记忆 — 向量数据库（本次会话关键事件）
Layer 3: 语义记忆 — 向量库 + 知识图谱（跨会话长期知识）
```

向量库在 Memory 场景与 RAG 场景的区别：

| 维度 | RAG 知识库 | Agent Memory |
|:---|:---|:---|
| 写入时机 | 离线批量入库 | 在线实时写入 |
| 更新频率 | 低（文档变更时） | 高（每轮对话可能写入） |
| 检索意图 | 回答用户问题 | 回忆历史事实和偏好 |
| 数据生命周期 | 长期稳定 | 需要衰减和清理策略 |
| 元数据 | 文档来源、章节 | 时间戳、重要性、用户 ID |

Memory 场景的额外工程要求：

- **时间衰减**：越久远的记忆权重越低。
- **重要性加权**：关键事实（用户名、偏好）提升检索权重。
- **去重合并**：避免相似记忆重复入库污染检索。

---

## 10. 生产实践要点

### 10.1 入库管线检查清单

| 检查项 | 判断标准 |
|:---|:---|
| 切分粒度 | 每个 chunk 能独立表达完整语义（256~512 token 常见） |
| 重叠（Overlap） | 相邻 chunk 有 10%~20% 重叠，避免关键信息被切断 |
| 元数据完整 | 至少 source + chunk_index + doc_type |
| Embedding 一致性 | 入库和检索用同一模型、同一维度 |
| 批量写入 | 用 batch insert，不要逐条写入 |
| 索引参数 | 根据数据量选择 HNSW 的 `efConstruction` 和 `M` 参数 |

### 10.2 检索质量保障

| 策略 | 做法 |
|:---|:---|
| 固定 eval query 集 | 20~50 条业务问题 + 期望召回文档 |
| 监控召回率 | Hit@K、MRR（Mean Reciprocal Rank） |
| A/B 索引对比 | 不同切分 / Embedding / 索引参数并行评测 |
| 检索日志 | 记录 query、Top-K 结果、最终使用的片段 |
| 定期重建 | Embedding 模型升级时重建索引 |

### 10.3 性能与成本

| 优化方向 | 手段 |
|:---|:---|
| 降低存储 | IVF-PQ 量化（FAISS / Milvus） |
| 降低延迟 | HNSW 调参、GPU 加速、缓存热门 query |
| 降低 Embedding 成本 | 批量离线入库、缓存 query embedding |
| 控制上下文膨胀 | Top-K 不要太大（5~10 通常足够），配合 Reranker 精选 |

### 10.4 权限与多租户

生产环境必须考虑数据隔离：

```text
方案 1：metadata filter（推荐起步）
  每条向量带 tenant_id / user_id / access_level
  检索时强制加 filter 条件

方案 2：Collection 隔离
  每个租户独立 Collection
  隔离性强，但管理成本高

方案 3：独立实例
  大客户的完全物理隔离
```

---

## 11. 常见坑

| 坑 | 原因 | 修复 |
|:---|:---|:---|
| 检索结果不相关 | 切分太碎或太大、Embedding 模型不匹配 | 调整 chunk size，换领域 Embedding 模型 |
| 换模型后检索变差 | 索引没重建 | 新建 Collection，全量 re-embed |
| 回答无法溯源 | metadata 没存 source | 入库时强制写入 source 和 chunk_index |
| Top-K 太大 | 召回太多无关片段污染上下文 | 减小 K，加 Reranker |
| 只搜向量不搜关键词 | 纯语义检索漏掉精确匹配 | 加 BM25 混合检索 |
| Chroma 上生产翻车 | 超过 10 万向量性能骤降 | 迁移到 Qdrant / Milvus |
| 没有 eval 就调参 | 不知道召回质量是否变好 | 建固定 eval query 集，量化 Hit@K |
| 向量库当文档存储 | payload 塞全文 | 原文放对象存储，向量库只存摘要 + 引用 |

---

## 12. 学习路线

建议按下面顺序学习：

1. 先读 [[04-langchain-guide|LangChain 框架指南]] 第 7 节，用 Chroma 跑通最小 RAG。
2. 回到本文，理解 Embedding、ANN 索引和 metadata 设计。
3. 读 [[14-context-engineering|长上下文问题与修复]]，理解检索结果如何影响上下文质量。
4. 用 FAISS 做索引算法实验（FLAT vs HNSW vs IVF），建立性能直觉。
5. 读 [[20-rag-full-pipeline|RAG 全链路实战]]，把向量库放进完整管线。
6. Docker 部署 Milvus，把 Chroma 原型迁移过去。
7. 实现混合检索 + Reranker，用 eval query 集量化提升。
8. 结合 [[15-agent-memory|Agent Memory]]，理解向量库在记忆系统里的角色。

官方资源：

| 步骤 | 资源 |
|:---|:---|
| Embedding 原理 | [Sentence Transformers](https://www.sbert.net/) |
| FAISS 入门 | [FAISS Wiki](https://github.com/facebookresearch/faiss/wiki/Getting-started) |
| Chroma 文档 | [Chroma Docs](https://docs.trychroma.com/) |
| Milvus 部署 | [Milvus Quick Start](https://milvus.io/docs/install_standalone-docker.md) |
| Qdrant 文档 | [Qdrant Docs](https://qdrant.tech/documentation/) |
| 混合检索 | [Milvus Hybrid Search](https://milvus.io/docs/multi-vector-search.md) |

---

## 13. 推荐实战：为 Paper Agent 搭建向量索引

目标：为 [[04-langchain-guide|LangChain 框架指南]] 第 15 节的 Paper Agent MVP 搭建检索底座。

MVP 范围：

```text
arXiv 论文摘要
  -> 解析 + 切分（按段落）
  -> Embedding（text-embedding-3-small 或 bge-m3）
  -> 入库（Chroma 原型 -> Milvus 生产）
  -> 检索接口（Top-5 + metadata filter）
  -> eval query 集验证召回质量
```

分阶段实施：

| 阶段 | 向量库 | 目标 |
|:---|:---|:---|
| 第 1 天 | Chroma | 跑通入库 + 检索 + LangChain Retriever |
| 第 3 天 | FAISS | 对比 HNSW vs FLAT 的召回率和延迟 |
| 第 5 天 | Milvus | Docker 部署，迁移数据，加 metadata filter |
| 第 7 天 | Milvus + BM25 | 混合检索 + Reranker + eval 报告 |

入库 schema 建议：

```python
{
    "id": "arxiv_2402.14034_chunk_3",
    "vector": [...],
    "metadata": {
        "arxiv_id": "2402.14034",
        "title": "AgentScope: A Flexible yet Robust Multi-Agent Platform",
        "authors": "Gao et al.",
        "year": 2024,
        "section": "abstract",
        "chunk_index": 3,
    }
}
```

---

## 14. 面试表达

如果面试官问「你怎么选向量数据库」，不要只说「看数据量」。更好的回答结构是：

```text
我选向量库会看四个维度：数据规模、部署约束、过滤需求、团队技术栈。

比如 Paper Agent 项目：
- 数据规模：50 万篇论文摘要，约 200 万向量
- 部署：需要 Docker 一键部署，后续可能上 K8s
- 过滤：按年份、领域、作者做 metadata filter
- 技术栈：Python + LangChain + FastAPI

对比后选 Milvus Standalone：
- Chroma 不适合 200 万级别的生产
- FAISS 没有服务端和 metadata 过滤
- Qdrant 也可以，但 Milvus 生态更成熟、学习资料更多
- Pinecone 国内访问和成本是问题

同时我会建一组 eval query（20 条），用 Hit@5 和 MRR 量化不同
切分策略和 Embedding 模型的召回质量，而不是凭感觉调参。
```

这类回答能体现你知道向量库在 RAG 管线里的位置，也有量化评估意识。

---

## 15. 总结

向量数据库的正确打开方式：

- 用它做 RAG 和 Memory 的 **语义召回层**。
- 用 **metadata** 保证溯源、过滤和权限。
- 用 **混合检索 + Reranker** 弥补纯向量的不足。
- 用 **eval query 集** 量化召回质量，不靠感觉调参。
- 用 **Collection 版本管理** 安全地升级 Embedding 和切分策略。
- 把 **切分、Embedding 选择、上下文注入和评估** 握在自己手里。

最终目标不是「装一个向量库」，而是构建一个**召回准、可溯源、可评估、可扩展**的检索底座。

---

## 参考资源

- [向量数据库选型指南（项目资源）](../08-资源/rag/vector-db.md)
- [Milvus 官方文档](https://milvus.io/docs)
- [Chroma 官方文档](https://docs.trychroma.com/)
- [Qdrant 官方文档](https://qdrant.tech/documentation/)
- [FAISS GitHub](https://github.com/facebookresearch/faiss)
- [RAG 全链路实战](20-rag-full-pipeline.md)
- [Agent Memory](15-agent-memory.md)
- [LangChain 框架指南](04-langchain-guide.md)
