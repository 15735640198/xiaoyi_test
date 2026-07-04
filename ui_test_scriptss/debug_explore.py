#!/usr/bin/env python3
"""调试: 屏幕亮度查询 - 深入分析"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import json
import hdc_utils
from hdc_utils import *

find_hdc()
check_device()

restart_settings()
time.sleep(2)

layout = navigate_to_page('显示和亮度', 2)
if not layout:
    print("导航失败")
    sys.exit(1)

time.sleep(1)

# 打印 Slider 的完整 JSON（所有属性）
print("=== Slider 完整属性 ===")
sliders = find_sliders(layout)
for sl in sliders:
    print(json.dumps(sl, ensure_ascii=False, indent=2))

# 打印滑块附近(y=1700~2100)的所有组件
print("\n=== 滑块附近所有组件 (y=1700~2100) ===")
all_comps = find_components(layout, lambda c: True)
for c in all_comps:
    b = parse_full_bounds(attr(c, 'bounds', ''))
    if b and b[1] >= 1700 and b[3] <= 2100:
        txt = attr(c, 'text', '') or attr(c, 'originalText', '')
        print(f"  type={attr(c, 'type')} text={txt!r} id={attr(c, 'id', '')!r} bounds=[{b[0]},{b[1]}][{b[2]},{b[3]}]")

# 打印页面上所有带数字的文本组件
print("\n=== 含数字的 Text 组件 ===")
for c in find_components(layout, lambda c: attr(c, 'type') == 'Text'):
    txt = attr(c, 'text', '') or attr(c, 'originalText', '')
    if any(ch.isdigit() for ch in txt):
        b = parse_full_bounds(attr(c, 'bounds', ''))
        print(f"  text={txt!r} id={attr(c, 'id', '')!r} bounds=[{b[0]},{b[1]}][{b[2]},{b[3]}] center=({(b[0]+b[2])//2},{(b[1]+b[3])//2})")

print("\n=== 完成 ===")
