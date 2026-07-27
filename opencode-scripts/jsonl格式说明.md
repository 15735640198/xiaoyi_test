# opencode 会话导出 (JSONL) 字段说明

## 1. 概述

每个 `.jsonl` 文件对应 opencode 的一个 session（一次 `opencode run` 会话），由 [export_opencode_sessions.py](export_opencode_sessions.py) 从 `opencode.db` 导出。

文件由若干 JSON 对象按顺序拼接：

- 第 1 个对象：`type=session`，会话级元信息
- 第 2 个起：`type=message`，会话中的每条消息（user / assistant），按 `time_created` 升序排列

> **存储格式**：导出脚本默认写紧凑 JSONL（每行一个 JSON 对象）。若文件被编辑器格式化为 `indent=2`，对象会跨多行，此时需用流式 `json.JSONDecoder().raw_decode` 解析，不能逐行 `json.loads`（会报 `Expecting property name`）。

### 示例文件

`ses_0784ea0c9ffeCmc8Ej9bow5ew8.jsonl`（slug=`neon-eagle`，标题 "Python test script from markdown"）：

- 1 个 session 对象
- 3 个 message 对象：1 条 user + 2 条 assistant
- assistant 消息的 parts 涵盖 step-start / reasoning / tool / text / step-finish 全部类型

## 2. 对象类型总览

| 对象 `type` | 数量 | 作用 |
|---|---|---|
| `session` | 1 | 会话元信息：模型、工作目录、token 统计、费用、时间戳 |
| `message` | N | 单条消息：角色（user/assistant）+ 内容片段 `parts` |

## 3. session 对象

### 顶层字段

| 字段 | 类型 | 说明 | 示例值 |
|---|---|---|---|
| `type` | string | 固定 `"session"`，标识对象类型 | `"session"` |
| `session_id` | string | 会话唯一 ID，`ses_` 开头 | `"ses_0784ea0c9ffeCmc8Ej9bow5ew8"` |
| `slug` | string | opencode 分配的随机两词标识，空则回落 `untitled` | `"neon-eagle"` |
| `title` | string | 会话标题（来自首条用户消息摘要） | `"Python test script from markdown"` |
| `directory` | string | 会话工作目录（opencode 运行时的 `--dir`） | `"D:/lzs/study_doc/harness_demo"` |
| `agent` | string | 使用的 agent 名称 | `"build"` |
| `model` | object | 模型信息，见下 | `{...}` |
| `tokens` | object | token 用量统计，见下 | `{...}` |
| `cost` | number | 会话总费用（美元） | `0.0` |
| `time_created` | int | 创建时间戳（毫秒） | `1784687976247` |
| `time_updated` | int | 最后更新时间戳（毫秒） | `1784687986364` |

### `model` 子对象

| 字段 | 说明 | 示例 |
|---|---|---|
| `id` | 模型名 | `"GLM-5.2"` |
| `providerID` | 模型提供商 | `"glm"` |
| `variant` | 变体 | `"default"` |

### `tokens` 子对象

| 字段 | 说明 |
|---|---|
| `input` | 输入 token 数 |
| `output` | 输出 token 数 |
| `reasoning` | 推理 token 数 |
| `cache_read` | 缓存读取 token 数 |
| `cache_write` | 缓存写入 token 数 |

## 4. message 对象

| 字段 | 类型 | 说明 | 示例值 |
|---|---|---|---|
| `type` | string | 固定 `"message"` | `"message"` |
| `message_id` | string | 消息唯一 ID，`msg_` 开头 | `"msg_f87b15f7b001R1ekoZdslEhWKW"` |
| `role` | string | 消息角色：`user` / `assistant` | `"user"` |
| `model` | object\|null | user 消息带 `{providerID, modelID}`；assistant 消息通常为 `null` | `{"providerID":"glm","modelID":"GLM-5.2"}` |
| `agent` | string | agent 名称 | `"build"` |
| `parts` | array | 内容片段数组，元素见第 5 节 | `[{...}, ...]` |
| `time_created` | int | 创建时间戳（毫秒） | `1784687976315` |
| `time_updated` | int | 更新时间戳（毫秒） | `1784687979771` |

## 5. part 类型详解

`parts` 数组每个元素是一个 part，按 `type` 区分。一条 assistant 消息通常对应一个"推理步骤"（step），结构为：

```
step-start → reasoning → (tool 或 text) → step-finish
```

### 5.1 `step-start`

标记一个推理步骤的开始，仅一个字段。

| 字段 | 说明 |
|---|---|
| `type` | `"step-start"` |

### 5.2 `reasoning`

模型内部思考过程（不直接输出给用户）。

| 字段 | 类型 | 说明 |
|---|---|---|
| `type` | string | `"reasoning"` |
| `text` | string | 推理文本 |
| `time` | object | `{ start, end }` 毫秒时间戳 |

### 5.3 `tool`

工具调用（read / write / bash 等）。

| 字段 | 类型 | 说明 | 示例 |
|---|---|---|---|
| `type` | string | `"tool"` | `"tool"` |
| `tool` | string | 工具名 | `"read"` |
| `callID` | string | 调用 ID，`call_` 开头 | `"call_d26c9eb5bafb4a9b94d7f1d4"` |
| `state` | object | 调用状态与结果，见下 | `{...}` |

#### `state` 子对象

| 字段 | 类型 | 说明 |
|---|---|---|
| `status` | string | 调用状态：`completed` / `failed` 等 |
| `input` | object | 工具入参，结构随工具而定（如 read 的 `{ filePath }`） |
| `output` | string | 工具原始输出（文件内容、命令输出等） |
| `metadata` | object | 元信息，见下 |
| `title` | string | 展示用标题 |
| `time` | object | `{ start, end }` 毫秒时间戳 |

#### `metadata` 子对象

| 字段 | 类型 | 说明 |
|---|---|---|
| `preview` | string | 输出预览摘要 |
| `truncated` | bool | 是否被截断 |
| `loaded` | array | 已加载资源列表（常为空） |
| `display` | object | 展示信息，结构随工具而定 |

`display`（文件类工具）常见字段：`type`、`path`、`text`、`lineStart`、`lineEnd`、`totalLines`、`truncated`。

### 5.4 `text`

模型输出给用户的文本/代码。

| 字段 | 类型 | 说明 |
|---|---|---|
| `type` | string | `"text"` |
| `text` | string | 文本内容（可能含生成的代码） |
| `time` | object | `{ start, end }` 毫秒时间戳 |

### 5.5 `step-finish`

一个推理步骤的结束统计。

| 字段 | 类型 | 说明 | 示例 |
|---|---|---|---|
| `type` | string | `"step-finish"` | `"step-finish"` |
| `reason` | string | 结束原因：`tool-calls`（继续调工具）/ `stop`（结束） | `"tool-calls"` |
| `tokens` | object | 本步 token 统计，见下 | `{...}` |
| `cost` | number | 本步费用 | `0` |

#### `tokens` 子对象

| 字段 | 说明 |
|---|---|
| `total` | 总 token |
| `input` | 输入 token |
| `output` | 输出 token |
| `reasoning` | 推理 token |
| `cache.write` | 缓存写入 |
| `cache.read` | 缓存读取 |

## 6. 时间戳说明

所有 `time_created` / `time_updated` / `time.start` / `time.end` 均为 **Unix 毫秒时间戳**。转换为可读时间：

```python
from datetime import datetime
datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M:%S")
# 1784687976247 → 2026-07-22 10:39:36
```

## 7. 真实示例（基于示例文件）

### session 对象摘要

```json
{
  "type": "session",
  "session_id": "ses_0784ea0c9ffeCmc8Ej9bow5ew8",
  "slug": "neon-eagle",
  "title": "Python test script from markdown",
  "directory": "D:/lzs/study_doc/harness_demo",
  "agent": "build",
  "model": { "id": "GLM-5.2", "providerID": "glm", "variant": "default" },
  "tokens": { "input": 1073, "output": 92, "reasoning": 278, "cache_read": 14336, "cache_write": 0 },
  "cost": 0.0,
  "time_created": 1784687976247,
  "time_updated": 1784687986364
}
```

### 消息序列

| # | role | parts 组成 | 说明 |
|---|---|---|---|
| 1 | user | text | 用户请求：读取 `_harness_prompt_4.md` 并按指令生成脚本 |
| 2 | assistant | step-start → reasoning → tool(read) → step-finish | 读取了该 markdown 文件（工具调用） |
| 3 | assistant | step-start → reasoning → text → step-finish | 输出生成的 Python 脚本（`test_set_brightness`） |

## 8. 解析示例代码

兼容"紧凑 JSONL"与"被格式化的多行 JSON"两种情况：

```python
import json
from pathlib import Path

def load_jsonl(path):
    data = Path(path).read_text(encoding="utf-8")
    dec = json.JSONDecoder()
    idx, objs = 0, []
    while idx < len(data):
        while idx < len(data) and data[idx].isspace():
            idx += 1
        if idx >= len(data):
            break
        obj, idx = dec.raw_decode(data, idx)
        objs.append(obj)
    return objs

# 用法
objs = load_jsonl("ses_xxx.jsonl")
session = objs[0]                 # type=session
messages = objs[1:]               # type=message
for m in messages:
    for part in m["parts"]:
        print(part["type"])       # step-start / reasoning / tool / text / step-finish
```
