#!/usr/bin/env python3
"""
HarmonyOS 个人热点开关状态查询脚本

导航路径: 设置 > 移动网络 > 个人热点
使用工具: hdc + uitest 命令行 (dumpLayout / uiInput)
原理: 通过 uitest dumpLayout 获取控件树 JSON，解析 Toggle 组件的 checked 属性

依赖: hdc 已安装并在 PATH 中，设备已通过 USB/WiFi 连接
"""

import subprocess
import json
import os
import re
import sys
import time
import tempfile

# ── 配置 ──────────────────────────────────────────────
SETTINGS_BUNDLE = 'com.huawei.hmossettings'
SETTINGS_ABILITY = 'EntryAbility'
TEXT_MOBILE_NETWORK = '移动网络'
TEXT_PERSONAL_HOTSPOT = '个人热点'
REMOTE_LAYOUT_PATH = '/data/local/tmp/layout.json'
NAV_WAIT = 2.5          # 页面跳转后等待秒数
DUMP_WAIT = 1.0         # dumpLayout 后等待秒数
# ─────────────────────────────────────────────────────


def run_cmd(cmd: list, timeout: int = 30) -> str:
    """执行命令，返回合并的 stdout+stderr"""
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout, encoding='utf-8', errors='replace'
        )
        return (r.stdout or '') + (r.stderr or '')
    except FileNotFoundError:
        print(f"[ERROR] 命令不存在: {cmd[0]}，请确认 hdc 已安装并在 PATH 中")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print(f"[WARN] 命令超时: {' '.join(cmd)}")
        return ''


def hdc_shell(*args, timeout: int = 30) -> str:
    """执行 hdc shell 命令"""
    return run_cmd(['hdc', 'shell', *list(args)], timeout)


def dump_layout() -> dict:
    """
    获取当前页面控件树
    优先尝试解析 stdout，失败则从设备拉取 layout.json 文件
    """
    # 执行 dumpLayout
    output = hdc_shell('uitest', 'dumpLayout')
    time.sleep(DUMP_WAIT)

    # 优先: stdout 直接输出 JSON
    stripped = output.strip()
    if stripped.startswith('{') or stripped.startswith('['):
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass

    # 回退: 从设备拉取文件
    local_path = os.path.join(tempfile.gettempdir(), 'hm_layout.json')
    run_cmd(['hdc', 'file', 'recv', REMOTE_LAYOUT_PATH, local_path], timeout=15)

    if not os.path.exists(local_path):
        raise RuntimeError("无法获取布局文件: dumpLayout 失败且文件拉取失败")

    with open(local_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_bounds(bounds) -> tuple:
    """解析 bounds 字段，返回中心坐标 (x, y)"""
    if isinstance(bounds, str):
        # 格式: "[left,top][right,bottom]"
        nums = re.findall(r'\d+', bounds)
        if len(nums) >= 4:
            return ((int(nums[0]) + int(nums[2])) // 2,
                    (int(nums[1]) + int(nums[3])) // 2)
    elif isinstance(bounds, list) and len(bounds) == 4:
        return ((bounds[0] + bounds[2]) // 2, (bounds[1] + bounds[3]) // 2)
    elif isinstance(bounds, dict):
        l = bounds.get('left', 0)
        t = bounds.get('top', 0)
        r = bounds.get('right', 0)
        b = bounds.get('bottom', 0)
        return ((l + r) // 2, (t + b) // 2)
    return None


def find_components(node, predicate, results=None) -> list:
    """递归查找满足条件的所有组件"""
    if results is None:
        results = []
    if isinstance(node, dict):
        if predicate(node):
            results.append(node)
        for child in node.get('children', []):
            find_components(child, predicate, results)
    elif isinstance(node, list):
        for item in node:
            find_components(item, predicate, results)
    return results


def get_text(comp: dict) -> str:
    """获取组件文本 (text 或 accessibilityText)"""
    return comp.get('text', '') or comp.get('accessibilityText', '') or ''


def find_by_text(node, text: str) -> list:
    """按文本查找组件"""
    return find_components(node, lambda c: text in get_text(c))


def find_toggles(node) -> list:
    """查找所有 Toggle/Switch 类型组件"""
    return find_components(
        node,
        lambda c: c.get('type', '').lower() in ('toggle', 'switch', 'toggleswitch')
    )


def _check_state(comp: dict) -> str:
    """从组件属性判断开关状态 -> 'on' | 'off' | 'unknown'"""
    val = comp.get('checked', comp.get('isOn', None))
    if val is True or val in ('true', 'True', 1, '1'):
        return 'on'
    if val is False or val in ('false', 'False', 0, '0'):
        return 'off'
    return 'unknown'


def _distance(p1, p2) -> float:
    if not p1 or not p2:
        return float('inf')
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def click_component(comp: dict, wait: float = NAV_WAIT) -> bool:
    """点击指定组件"""
    center = parse_bounds(comp.get('bounds'))
    if not center:
        print(f"  -> 无法获取组件坐标: bounds={comp.get('bounds')}")
        return False
    x, y = center
    print(f"  -> 点击坐标 ({x}, {y})")
    hdc_shell('uitest', 'uiInput', 'click', str(x), str(y))
    time.sleep(wait)
    return True


def click_by_text(layout: dict, text: str, wait: float = NAV_WAIT) -> bool:
    """通过文本查找并点击组件"""
    comps = find_by_text(layout, text)
    if not comps:
        print(f"  -> 未找到文本 '{text}'")
        return False
    # 优先选择可点击的组件 (有 onClick 或类型为 Text/Button)
    clickable = [c for c in comps if c.get('clickable', False) or
                 c.get('type', '') in ('Text', 'Button', 'Row', 'ListItem')]
    target = clickable[0] if clickable else comps[0]
    print(f"  -> 找到 '{text}' (共 {len(comps)} 个匹配)")
    return click_component(target, wait)


def get_toggle_state(layout: dict, target_text: str) -> str:
    """
    查找目标开关状态
    策略1: Toggle 自身包含目标文本
    策略2: 离目标文本最近的 Toggle
    策略3: 带 checked/isOn 属性且靠近目标文本的组件
    策略4: 只有一个 Toggle 时直接返回
    返回: 'on' | 'off' | 'unknown' | None
    """
    toggles = find_toggles(layout)
    text_comps = find_by_text(layout, target_text)

    # 策略1: Toggle 自身包含目标文本
    for t in toggles:
        if target_text in get_text(t):
            return _check_state(t)

    # 策略2: 离目标文本最近的 Toggle
    if text_comps and toggles:
        text_center = parse_bounds(text_comps[0].get('bounds'))
        if text_center:
            nearest = min(
                toggles,
                key=lambda t: _distance(text_center, parse_bounds(t.get('bounds')))
            )
            return _check_state(nearest)

    # 策略3: 带 checked/isOn 属性的组件中查找
    checked_comps = find_components(
        layout, lambda c: 'checked' in c or 'isOn' in c
    )
    for c in checked_comps:
        if target_text in get_text(c):
            return _check_state(c)
        # 检查是否靠近目标文本
        for tc in text_comps:
            if _distance(parse_bounds(tc.get('bounds')),
                         parse_bounds(c.get('bounds'))) < 500:
                return _check_state(c)

    # 策略4: 只有一个 Toggle，直接返回
    if len(toggles) == 1:
        return _check_state(toggles[0])

    return None


def debug_dump(layout: dict):
    """调试输出: 打印 Toggle 和包含"热点"的组件"""
    toggles = find_toggles(layout)
    print(f"\n  [DEBUG] 找到 {len(toggles)} 个 Toggle/Switch:")
    for i, t in enumerate(toggles):
        print(f"    [{i}] type={t.get('type')} text={get_text(t)!r} "
              f"checked={t.get('checked', 'N/A')} isOn={t.get('isOn', 'N/A')} "
              f"bounds={t.get('bounds')}")

    hotspot_comps = find_by_text(layout, '热点')
    print(f"\n  [DEBUG] 找到 {len(hotspot_comps)} 个包含'热点'的组件:")
    for i, c in enumerate(hotspot_comps[:10]):
        print(f"    [{i}] type={c.get('type')} text={get_text(c)!r} "
              f"checked={c.get('checked', 'N/A')} bounds={c.get('bounds')}")


def main():
    print("=" * 55)
    print("  HarmonyOS 个人热点开关状态查询")
    print("  路径: 设置 > 移动网络 > 个人热点")
    print("=" * 55)

    # 检查 hdc
    ver = run_cmd(['hdc', 'version'], timeout=10)
    if 'hdc' not in ver.lower() and '1.' not in ver:
        print("[ERROR] hdc 未安装或不在 PATH 中")
        sys.exit(1)
    print(f"  hdc 可用: {ver.strip().splitlines()[0] if ver else 'OK'}")

    # 检查设备连接
    list_output = run_cmd(['hdc', 'list', 'targets'], timeout=10)
    devices = [d.strip() for d in list_output.strip().splitlines()
               if d.strip() and 'Empty' not in d]
    if not devices:
        print("[ERROR] 未检测到已连接的设备，请先连接设备")
        sys.exit(1)
    print(f"  已连接设备: {devices[0]}")

    # Step 1: 启动设置应用
    print("\n[1/4] 启动设置应用...")
    hdc_shell('aa', 'start', '-a', SETTINGS_ABILITY, '-b', SETTINGS_BUNDLE)
    time.sleep(3)

    # Step 2: 进入移动网络
    print("\n[2/4] 导航到「移动网络」...")
    layout = dump_layout()
    if not click_by_text(layout, TEXT_MOBILE_NETWORK):
        print("[FAIL] 未找到「移动网络」入口")
        debug_dump(layout)
        return

    # Step 3: 进入个人热点
    print("\n[3/4] 导航到「个人热点」...")
    layout = dump_layout()
    if not click_by_text(layout, TEXT_PERSONAL_HOTSPOT):
        print("[FAIL] 未找到「个人热点」入口")
        debug_dump(layout)
        return

    # Step 4: 查询开关状态
    print("\n[4/4] 查询个人热点开关状态...")
    layout = dump_layout()
    state = get_toggle_state(layout, TEXT_PERSONAL_HOTSPOT)

    # 输出结果
    print("\n" + "-" * 55)
    if state == 'on':
        print("  >>> 个人热点开关状态: 已开启 (ON) <<<")
    elif state == 'off':
        print("  >>> 个人热点开关状态: 已关闭 (OFF) <<<")
    elif state == 'unknown':
        print("  >>> 个人热点开关状态: 未知 (找到开关但无法确定状态) <<<")
        debug_dump(layout)
    else:
        print("  >>> 未找到个人热点开关 <<<")
        debug_dump(layout)
    print("-" * 55)


if __name__ == '__main__':
    main()
