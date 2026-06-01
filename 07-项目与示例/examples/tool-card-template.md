# Tool Card 模板

> 一个好工具不是“能被调用”就够了，而是要让模型知道什么时候该用、怎么用、失败后怎么恢复。

## 模板

```markdown
## Tool: search_papers

**Purpose**：按关键词搜索论文元数据，返回标题、摘要、作者、年份、链接和引用信息。

**Use When**：
- 用户需要查找某个主题的代表论文。
- Agent 需要为答案补充可引用证据。
- 需要比较不同方法的提出时间和核心贡献。

**Do Not Use When**：
- 用户已经给了具体 PDF，并要求只基于该 PDF 回答。
- 问题需要网页实时信息而不是学术论文。

**Input Schema**：
```json
{
  "query": "string, required",
  "year_from": "integer, optional",
  "year_to": "integer, optional",
  "max_results": "integer, default 5, max 20"
}
```

**Output Schema**：
```json
{
  "ok": true,
  "items": [
    {
      "title": "string",
      "authors": ["string"],
      "year": 2025,
      "abstract": "string, truncated to 800 chars",
      "url": "string",
      "source": "arXiv | Semantic Scholar | OpenAlex"
    }
  ],
  "next_page_token": "string | null"
}
```

**Errors**：

| error | retryable | Agent 应对 |
|:---|:---:|:---|
| `rate_limited` | yes | 降低 `max_results` 或稍后重试 |
| `empty_result` | no | 改写 query 或放宽年份 |
| `source_unavailable` | yes | 切换备用数据源 |

**Security**：
- 只访问公开论文元数据。
- 不抓取付费墙内容。
- 不把 API key 写入 trace。

**Example**：
```json
{
  "query": "agentic rag evaluation",
  "year_from": 2023,
  "max_results": 5
}
```
```

## 常见问题

### 工具描述要不要写很长？

可以长，但要结构化。模型更容易理解“Use When / Do Not Use / Input / Output / Errors”这种稳定格式。

### 工具返回越全越好吗？

不是。返回越长，上下文越容易被噪声污染。工具应该返回下一步决策需要的信息，并保留可追溯引用。

### 要不要让模型自己生成 API 参数？

可以，但参数范围必须由 schema 限制。对真实外部 API，建议加一层适配器做校验、分页、截断和重试。
