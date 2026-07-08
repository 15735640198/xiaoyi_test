import requests
import json

API_BASE = "https://api.openbitfun.com/v1/chat/completions"
API_KEY = "sk-z9yS9C0ZPyJGiCol8AzSny0lY55f3b77cQ4J4U5Y8e7lCaF5"
MODEL = "glm-5.1"

# 填充超过 1024 tokens 的大前缀，触发 cache 最低阈值
# 用一段长文本 + cache_control 标记，模拟 Claude Code 的 system prompt
FILLER = "你是一个知识渊博的AI助手，通晓各领域知识。" * 200  # 约 1600+ tokens
messages = [
    {
        "role": "system",
        "content": [
            {"type": "text", "text": FILLER, "cache_control": {"type": "ephemeral"}}
        ]
    },
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "请记住以下信息：" + "数据" * 100, "cache_control": {"type": "ephemeral"}}
        ]
    },
    {
        "role": "user",
        "content": "1+1等于几？简短回答。"
    }
]

# 第一次请求：期望创建缓存（cache_creation_input_tokens > 0）
r1 = requests.post(API_BASE, json={
    "model": MODEL,
    "messages": messages,
    "max_tokens": 100
}, headers={
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
})
print("=== 第一次请求 (期望创建缓存) ===")
print(json.dumps(r1.json().get("usage", {}), indent=2))

# 第二次请求：同样的 system+user 前缀，期望命中缓存（cache_read_input_tokens > 0）
r2 = requests.post(API_BASE, json={
    "model": MODEL,
    "messages": messages,
    "max_tokens": 100
}, headers={
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
})
print("=== 第二次请求 (期望命中缓存) ===")
print(json.dumps(r2.json().get("usage", {}), indent=2))