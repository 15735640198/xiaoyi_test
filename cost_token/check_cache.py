import requests
import json
import sys

# ====== 改成你要测的地址 ======
API_BASE = "https://api.openbitfun.com/v1/chat/completions"
API_KEY = "sk-z9yS9C0ZPyJGiCol8AzSny0lY55f3b77cQ4J4U5Y8e7lCaF5"
MODEL = "glm-5.1"
# =============================

# 大 payload，确保超过 1024 token 最低缓存阈值
FILLER = "你是一个知识渊博的AI助手，通晓各领域知识。" * 200
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
        "content": "回答：1+1=？只输出数字。"
    }
]

print(f"目标: {MODEL} @ {API_BASE}")
print()

for i in range(1, 3):
    r = requests.post(API_BASE, json={
        "model": MODEL,
        "messages": messages,
        "max_tokens": 50
    }, headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    })

    usage = r.json().get("usage", {})

    # 检查各种可能的缓存字段
    cached = usage.get("prompt_tokens_details", {}).get("cached_tokens", None)
    cache_creation = usage.get("cache_creation_input_tokens", None)
    cache_read = usage.get("cache_read_input_tokens", None)

    print(f"=== 第{i}次 ===")
    print(f"  prompt_tokens:    {usage.get('prompt_tokens', 'N/A')}")
    print(f"  completion_tokens:{usage.get('completion_tokens', 'N/A')}")

    supports = []
    if cached is not None:
        print(f"  cached_tokens:    {cached}")
        if cached > 0:
            supports.append(f"cached_tokens={cached}")
    if cache_creation is not None:
        print(f"  cache_creation:   {cache_creation}")
        if cache_creation > 0:
            supports.append(f"cache_creation={cache_creation}")
    if cache_read is not None:
        print(f"  cache_read:       {cache_read}")
        if cache_read > 0:
            supports.append(f"cache_read={cache_read}")
    if cached is None and cache_creation is None and cache_read is None:
        print("  [无任何缓存相关字段]")

    print()

    if i == 2 and supports:
        print(f"[OK] 模型支持 prompt caching: {', '.join(supports)}")
    elif i == 2 and cached is None and cache_creation is None and cache_read is None:
        print(f"[不支持] 模型不返回任何缓存字段，不支持 prompt caching")
    elif i == 2:
        print(f"[未命中] 有缓存字段但值全为 0，缓存可能未触发或不稳定")
