# 项目名称

> 一句话说明：这个 Agent 服务谁，完成什么任务，为什么需要 Agent。

## Demo

- 输入示例：
- 输出示例：
- 演示视频或截图：

## 目标用户

| 用户 | 任务 | 痛点 |
|:---|:---|:---|
| 例：准备论文综述的学生 | 快速找到代表论文并做对比 | 资料多、来源散、难以追溯 |

## 功能范围

### 做什么

- 功能 1
- 功能 2
- 功能 3

### 不做什么

- 不处理高风险自动交易/付款/删除。
- 不绕过登录、付费墙、验证码或网站条款。
- 不声称实时数据一定准确，所有外部信息保留来源。

## 架构

```text
User
  -> Channel (CLI/Web)
  -> Agent Loop
  -> Context Builder
  -> Tool Registry
  -> Tools / APIs / Storage
  -> Trace + Eval
```

## 工具列表

| 工具 | 用途 | 权限 | 失败处理 |
|:---|:---|:---:|:---|
| `search_xxx` | 搜索公开资料 | low | rate limit 后降级 |
| `write_artifact` | 写入本地结果 | medium | 路径白名单 |
| `confirm_action` | 人工确认 | high | 用户拒绝则停止 |

## 安装

```bash
git clone <repo>
cd <repo>
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 运行

```bash
python -m app "你的任务"
```

## 测试与评测

```bash
pytest
python scripts/run_eval.py --cases examples/eval-cases.jsonl
```

## 评测报告

| 指标 | 结果 |
|:---|:---:|
| Eval cases | 20 |
| Task success rate | 待填写 |
| Avg steps | 待填写 |
| Avg latency | 待填写 |
| Avg cost | 待填写 |

## 失败分析

| 失败类型 | 占比 | 修复方向 |
|:---|:---:|:---|
| 检索不到证据 | 待填写 | query rewrite / 多源检索 |
| 工具超时 | 待填写 | timeout / retry / fallback |
| 上下文污染 | 待填写 | 摘要、过滤、引用约束 |

## 简历表达

> 构建面向 X 场景的 Agent 系统，采用 ReAct loop + 工具注册表 + 分层 context builder，接入 N 个外部工具并对高风险动作设置 human-in-the-loop；设计 20 条端到端 eval case，任务成功率达到 X%，通过工具结果截断和缓存将平均成本降低 X%。

## 参考资料

- 官方文档：
- 论文：
- Benchmark：
