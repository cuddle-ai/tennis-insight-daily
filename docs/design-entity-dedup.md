# AI 语义去重 设计方案

## 问题

当前去重使用 `SequenceMatcher`（标题字符串相似度 >= 0.8），无法检测语义相同但表述不同的条目：

```
"Jannik Sinner wins Rome Masters title with straight-sets victory"
"辛纳直落两盘击败对手 罗马大师赛夺冠"
"Sinner claims Italian Open championship"
```

三条标题描述同一事件，但字符串相似度远低于 0.8。

## 方案：AI 直接判定

不做实体提取、归一化映射等中间步骤。直接将标题列表交给 AI，由 AI 根据规则判断哪些标题描述同一事件，返回分组结果。

### Prompt

```
你是网球新闻去重助手。给定一组新闻标题，找出描述同一事件的标题，将它们分为同一组。

判断规则：
- 核心事件相同即为重复。例如同一场比赛结果、同一项赛事赛程、同一球员的同一新闻，无论语言、详略、措辞差异
- 不同角度不算重复。例如"辛纳夺冠"和"辛纳夺冠后的排名变化"是不同事件
- 同一球员的不同赛事不算重复
- 拿不准的不要合并

标题列表：
{编号列表}

返回 JSON，格式为分组数组。每组是一个标题编号列表，第一个编号为保留的标题（优先选信息最完整的）。不在任何组中的标题视为独立条目，无需列出。

示例输出：
[[1, 3, 7], [2, 5]]

表示标题 1/3/7 描述同一事件（保留 1），标题 2/5 描述同一事件（保留 2），其余标题独立保留。
```

### 调用参数

- `temperature=0` — 稳定输出
- `model` — 复用 `ai.model` 配置
- 每批最多 50 条标题，超出分批

### 去重逻辑

```python
def ai_dedup(items, client, model, batch_size=50):
    # 1. 按批次构建标题编号列表，调用 AI
    # 2. 解析 JSON 分组结果
    # 3. 每组中取 weight 最高的条目保留（优先级已在排序阶段计算）
    # 4. 未出现在任何分组中的条目直接保留
```

### 降级

无 API key 或 AI 调用失败时，回退到当前 `SequenceMatcher`（threshold=0.8）。

## 代码变更

### `src/processor/dedup.py`

新增 `ai_dedup(items, client, model)` 函数，保留现有 `dedup_items` 作为降级方案。

### `src/main.py`

AI client 初始化提前到去重之前，调用 `ai_dedup` 替换当前 `dedup_items`。

执行顺序调整为：创建 client → AI 去重 → 日期过滤 → 排序 → AI 摘要 → 渲染。

## 成本

50 条标题约 400 tokens 输入 + 100 tokens 输出，日产量通常 50-100 条，1-2 次 API 调用，成本可忽略。
