"""快速测试 wan2.7-image-pro 图片生成（DashScope 同步 multimodal-generation 接口）"""
import os
import sys
import base64

import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("DASHSCOPE_API_KEY", "")
model = os.getenv("DASHSCOPE_IMAGE_MODEL", "wan2.7-image-pro")

print(f"API Key: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else '(空)'}")
print(f"Model:   {model}\n")

if not api_key:
    print("✗ DASHSCOPE_API_KEY 未配置，退出")
    sys.exit(1)

SYNC_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"

prompt = (
    "Luxury perfume bottle photography, artistic and cinematic. "
    "Top notes: bergamot, lemon. Heart notes: rose, jasmine. Base notes: sandalwood, musk. "
    "Style: soft bokeh background, golden hour lighting, premium fragrance advertisement."
)
print(f"Prompt: {prompt[:80]}...\n")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}
body = {
    "model": model,
    "input": {
        "messages": [
            {"role": "user", "content": [{"text": prompt}]}
        ]
    },
    "parameters": {
        "size": "2K",
        "n": 1,
        "watermark": False,
        "thinking_mode": False,
    },
}

print("→ 调用同步接口（耗时 30-60s，请耐心等待）...")
try:
    resp = requests.post(SYNC_URL, json=body, headers=headers, timeout=180)
    print(f"  HTTP {resp.status_code}")
    if resp.status_code != 200:
        print(f"  Response: {resp.text[:500]}")
        sys.exit(1)
    data = resp.json()
except Exception as e:
    print(f"✗ 请求失败: {type(e).__name__}: {e}")
    sys.exit(1)

# 提取图片 URL
image_url = None
for choice in data.get("output", {}).get("choices", []):
    for content in choice.get("message", {}).get("content", []):
        if content.get("type") == "image":
            image_url = content.get("image")
            break

if not image_url:
    print(f"✗ 未找到图片 URL: {data}")
    sys.exit(1)

print(f"\n✓ 图片 URL: {image_url}")

# 下载并 base64
print("\n→ 下载并转 base64...")
try:
    img = requests.get(image_url, timeout=30)
    img.raise_for_status()
    b64 = base64.b64encode(img.content).decode("utf-8")
    print(f"  图片大小: {len(img.content)} bytes")
    print(f"  base64 长度: {len(b64)}")
    print("\n✓ 全流程通过！")
except Exception as e:
    print(f"✗ 下载失败: {type(e).__name__}: {e}")
    sys.exit(1)
