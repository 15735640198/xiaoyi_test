import requests
import json

API_BASE = "https://你的内网GLM地址/v1/chat/completions"
API_KEY = "你的key"
MODEL = "你的模型名"

# 构造一个带 cache_control 的消息列表
# 第1条 system 和第2条 user 都标记 cache，模拟 Claude Code 的行为
messages = [
    {
        "role": "system",
        "content": [
            {"type": "text", "text": "你是一个有帮助的助手。", "cache_control": {"type": "ephemeral"}}
        ]
    },
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "你好，请用中文回答。", "cache_control": {"type": "ephemeral"}}
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