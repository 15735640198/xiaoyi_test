#!/usr/bin/env python3
"""调试: 屏幕亮度查询"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
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

# 打印所有含"亮度"的文本
print("=== 含'亮度'的组件 ===")
for c in find_components(layout, lambda c: '亮度' in (attr(c, 'text', '') + attr(c, 'originalText', ''))):
    b = parse_full_bounds(attr(c, 'bounds', ''))
    print(f"  type={attr(c, 'type')} text={attr(c, 'text', '')!r} orig={attr(c, 'originalText', '')!r} bounds=[{b[0]},{b[1]}][{b[2]},{b[3]}] center=({(b[0]+b[2])//2},{(b[1]+b[3])//2})")

# 打印所有 Slider
print("\n=== Slider 组件 ===")
sliders = find_sliders(layout)
print(f"Slider 数量: {len(sliders)}")
for sl in sliders:
    b = parse_full_bounds(attr(sl, 'bounds', ''))
    print(f"  type={attr(sl, 'type')} text={attr(sl, 'text', '')!r} orig={attr(sl, 'originalText', '')!r} value={attr(sl, 'value', '')!r} bounds=[{b[0]},{b[1]}][{b[2]},{b[3]}] center=({(b[0]+b[2])//2},{(b[1]+b[3])//2})")

# 测试 find_by_text_nearest
print("\n=== find_by_text_nearest('亮度') ===")
comps = find_by_text_nearest(layout, '亮度')
for c in comps[:5]:
    b = parse_full_bounds(attr(c, 'bounds', ''))
    txt = attr(c, 'text', '') or attr(c, 'originalText', '')
    print(f"  type={attr(c, 'type')} text={txt!r} center=({(b[0]+b[2])//2},{(b[1]+b[3])//2})")

# 测试 read_status_slider
print("\n=== read_status_slider('亮度') ===")
result = read_status_slider(layout, '亮度')
print(f"  返回: {result!r}")

# 测试新的 query_brightness
print("\n=== query_brightness() ===")
import settings_api
result2 = settings_api.query_brightness()
print(f"  返回: {result2!r}")

print("\n=== 完成 ===")
