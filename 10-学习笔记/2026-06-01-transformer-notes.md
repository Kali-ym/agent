# Transformer 学习笔记

来源：[Transformer 原文](../02-理论基础/03-transformer.md)
日期：2026-06-01

## 延伸问题

### Q1: Multi-Head Attention 为什么要分多个头，而不是用一个大的注意力？

> 多头让模型能同时关注不同位置的不同表示子空间。单头注意力会把所有信息压缩到一个平均值里，多头相当于让模型"从多个角度看问题"。
>
> 类比：看一段代码，一个头关注语法结构，一个头关注变量依赖，一个头关注控制流。

### Q2: 为什么 Attention 要除以 √d_k？

> 当 d_k 很大时，Q·K 的点积值会很大，softmax 会进入梯度极小的区域（接近 one-hot）。除以 √d_k 是为了让方差回到 1，保持梯度健康。
>
> 面试追问：如果不除会怎样？→ 训练不稳定，注意力分布过于尖锐。

### Q3: Position Encoding 为什么用 sin/cos 而不是学习的？

> 原始论文实验发现两者效果差不多，但 sin/cos 有外推性（能处理比训练时更长的序列）。后来 RoPE 证明了旋转位置编码在长序列上更好。
>
> 延伸阅读：RoPE → ALiBi → 现在主流用 RoPE

## 关键洞察

- Attention 本质是"加权平均"，权重由内容相似度决定
- Transformer 的并行性来自于去掉了 RNN 的时序依赖
- 面试高频：KV Cache 加速推理的原理

## 待深入

- [ ] Flash Attention 的 IO 优化原理
- [ ] GQA (Grouped Query Attention) 和 MQA 的区别
- [ ] KV Cache 在长上下文下的内存问题
