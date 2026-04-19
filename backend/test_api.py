"""
API 测试脚本

使用方式：
  确保服务已启动（python main.py），然后运行：
  python test_api.py
"""

import json
import requests

BASE_URL = "https://custom-fragrance.onrender.com"


def print_section(title: str):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print('='*55)


def print_result(resp: requests.Response):
    print(f"状态码: {resp.status_code}")
    try:
        data = resp.json()
        print(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception:
        print(resp.text)


# ── 测试 1：健康检查 ────────────────────────────────────────────

def test_health():
    print_section("TEST 1: GET /api/health")
    resp = requests.get(f"{BASE_URL}/api/health", timeout=5)
    print_result(resp)
    assert resp.status_code == 200, "健康检查失败"
    assert resp.json().get("status") in ("ok", "degraded"), "status 字段异常"
    print("✓ 健康检查通过")


# ── 测试 2：生成香水配方 ────────────────────────────────────────

def test_generate_perfume():
    print_section("TEST 2: POST /api/generate-perfume")

    # 按照 Agent1Input schema 构造请求体
    # （watch_data + questionnaire + weather）
    payload = {
        "watch_data": {
            "body_temperature": 36.5,   # 用户指定体温
            "latitude": 31.2304,        # 上海
            "longitude": 121.4737,
            "heart_rate": 72,
            "activity_level": "静息"
        },
        "questionnaire": {
            "occasion": "职场",
            "scent_preference": ["花香", "青草/绿叶"],
            "longevity": "4-6小时",
            "sillage": "近距离",
            "concentration": "淡香水(EDT)",
            "budget_level": "中档",
            "avoided_notes": [],
            "time_of_day": "上午"
        },
        "weather": {
            "temperature": 25.0,
            "humidity": 60,
            "condition": "晴天",
            "city": "上海",
            "season": "春",
            "temp_level": "温暖(20-30°C)",
            "humidity_level": "适中(40-70%)"
        }
    }

    print("发送请求数据：")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print("\n请求中，请稍候...\n")

    resp = requests.post(
        f"{BASE_URL}/api/generate-perfume",
        json=payload,
        timeout=60,     # Agent 调用 LLM，给足超时时间
    )
    print_result(resp)

    if resp.status_code == 200:
        data = resp.json()
        print("\n── 配方摘要 ──────────────────────────────")
        formula = data.get("formula", {})
        print(f"前调: {[n['name'] for n in formula.get('top_notes', [])]}")
        print(f"中调: {[n['name'] for n in formula.get('middle_notes', [])]}")
        print(f"后调: {[n['name'] for n in formula.get('base_notes', [])]}")
        print(f"浓度: {data.get('concentration_percentage')}%")
        print(f"留香: {data.get('estimated_longevity_hours')} 小时")
        print(f"调配量: {data.get('volume_ml')} ml")
        print(f"\n气味描述:\n{data.get('scent_description')}")
        print(f"\n选择理由:\n{data.get('selection_rationale')}")

        bg = data.get("background_image")
        if bg:
            print(f"\n✓ Agent3 背景图生成成功（base64 长度: {len(bg)} 字符）")
        else:
            print("\n⚠ background_image 为空（API Key 未配置或图片生成失败）")

        print("\n✓ 配方生成通过")
    else:
        print(f"\n✗ 配方生成失败（HTTP {resp.status_code}）")


# ── 主入口 ──────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\nCustom Fragrance API 测试")
    print(f"目标地址: {BASE_URL}")

    try:
        test_health()
    except Exception as e:
        print(f"✗ 健康检查异常: {e}")

    try:
        test_generate_perfume()
    except Exception as e:
        print(f"✗ 生成接口异常: {e}")

    print(f"\n{'='*55}")
    print("  测试完成")
    print('='*55)
