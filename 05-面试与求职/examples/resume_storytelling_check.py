"""Check AI Agent resume bullets and project stories.

Runtime:
    Python 3.10+

Dependencies:
    Standard library only. See requirements.txt in this directory.

Usage:
    python docs/04-interview/examples/resume_storytelling_check.py --mode resume
    python docs/04-interview/examples/resume_storytelling_check.py --mode story
    python docs/04-interview/examples/resume_storytelling_check.py --mode resume --text "..."
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass


WEAK_WORDS = ("参与", "负责", "熟悉", "了解", "学习", "尝试")
ACTION_WORDS = (
    "设计",
    "实现",
    "构建",
    "优化",
    "接入",
    "评估",
    "部署",
    "重构",
    "沉淀",
)
TECH_WORDS = (
    "Agent",
    "RAG",
    "LangGraph",
    "LangChain",
    "Milvus",
    "FAISS",
    "FastAPI",
    "rerank",
    "Memory",
    "Tool",
    "评估",
)
METRIC_PATTERN = re.compile(r"(\d+(\.\d+)?%|\d+(\.\d+)?s|P95|Recall|准确率|成功率|延迟|成本|吞吐|QPS)")


@dataclass
class CheckResult:
    score: int
    warnings: list[str]
    suggestions: list[str]


def has_any(text: str, words: tuple[str, ...]) -> bool:
    return any(word.lower() in text.lower() for word in words)


def check_resume_bullet(text: str) -> CheckResult:
    warnings: list[str] = []
    suggestions: list[str] = []
    score = 100

    if not has_any(text, TECH_WORDS):
        score -= 20
        warnings.append("missing_agent_keywords")
        suggestions.append("补充 Agent / RAG / LangGraph / 向量库 / 评估框架等岗位关键词。")

    if not has_any(text, ACTION_WORDS):
        score -= 20
        warnings.append("missing_action")
        suggestions.append("把弱动词改成设计、实现、优化、评估、部署等具体动作。")

    if not METRIC_PATTERN.search(text):
        score -= 25
        warnings.append("missing_metric")
        suggestions.append("补充 Recall@5、准确率、延迟、成功率、成本等量化指标。")

    if has_any(text, WEAK_WORDS) and not METRIC_PATTERN.search(text):
        score -= 15
        warnings.append("weak_word_without_evidence")
        suggestions.append("如果使用参与、负责、熟悉等词，必须补充贡献边界和结果证据。")

    if len(text) < 45:
        score -= 10
        warnings.append("too_short")
        suggestions.append("项目 bullet 过短，建议写清场景、技术动作和结果。")

    if not suggestions:
        suggestions.append("保留当前写法，面试时准备架构图、评估集构造和失败案例。")

    return CheckResult(score=max(score, 0), warnings=warnings, suggestions=suggestions)


def check_project_story(text: str) -> CheckResult:
    sections = {
        "background": ("背景", "痛点", "问题", "场景", "为什么要做"),
        "task": ("目标", "指标", "衡量", "成功"),
        "action": ACTION_WORDS + TECH_WORDS + ("为什么选", "取舍", "替代方案"),
        "result": ("提升", "降低", "从", "到", "%", "Recall", "成功率", "延迟"),
        "reflection": ("复盘", "失败", "取舍", "下一步", "不足", "改进"),
    }

    warnings: list[str] = []
    suggestions: list[str] = []
    score = 100

    for section, words in sections.items():
        if not has_any(text, tuple(words)):
            score -= 18
            warnings.append(f"missing_{section}")

    if "missing_background" in warnings:
        suggestions.append("补充项目背景：谁使用、为什么原方案不够好。")
    if "missing_task" in warnings:
        suggestions.append("补充目标和指标：用什么衡量项目成功。")
    if "missing_action" in warnings:
        suggestions.append("补充你的技术动作：架构、模块、优化和工程实现。")
    if "missing_result" in warnings:
        suggestions.append("补充结果：指标提升、产物、业务价值或开源影响。")
    if "missing_reflection" in warnings:
        suggestions.append("补充复盘：失败案例、技术取舍或下一步计划。")

    if len(text) < 120:
        score -= 10
        warnings.append("story_too_short")
        suggestions.append("2 分钟项目故事通常需要覆盖背景、目标、架构、贡献、结果和复盘。")

    if not suggestions:
        suggestions.append("故事结构完整，建议继续准备 5 分钟架构版和 15 分钟深挖版。")

    return CheckResult(score=max(score, 0), warnings=warnings, suggestions=suggestions)


def print_result(result: CheckResult) -> None:
    print(f"score: {result.score}")
    print(f"warnings: {result.warnings}")
    print("suggestions:")
    for item in result.suggestions:
        print(f"- {item}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("resume", "story"), required=True)
    parser.add_argument("--text", default="")
    args = parser.parse_args()

    demo_resume = (
        "基于 LangGraph + FastAPI + Milvus 搭建企业知识库 Agent 服务，"
        "通过混合检索和 rerank 将 Recall@5 从 68% 提升到 84%，"
        "并接入日志追踪、失败重试和评估集回归。"
    )
    demo_story = (
        "背景是企业制度文档多，人工客服重复回答，关键词搜索无法处理流程类问题。"
        "目标是提升 Recall@5 和引用准确率。"
        "我设计了文档解析、混合检索、LangGraph 编排和评估回归四层架构，"
        "之所以选择 LangGraph，是因为复杂问题需要状态管理和工具调用，不适合单轮 prompt。"
        "通过章节切分、BM25 + dense retrieval 和 rerank 将 Recall@5 从 68% 提升到 84%。"
        "复盘时发现部分失败来自权限文档缺失，下一步会加入权限过滤和在线反馈。"
    )

    text = args.text.strip() or (demo_resume if args.mode == "resume" else demo_story)
    result = check_resume_bullet(text) if args.mode == "resume" else check_project_story(text)
    print_result(result)


if __name__ == "__main__":
    main()
