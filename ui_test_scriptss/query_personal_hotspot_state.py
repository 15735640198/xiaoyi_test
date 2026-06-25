#!/usr/bin/env python3
"""
HarmonyOS 个人热点开关状态查询脚本

导航路径: 设置 > 移动网络 > 个人热点
使用工具: hdc + uitest 命令行 (dumpLayout / uiInput)
原理: 通过 uitest dumpLayout 获取控件树 JSON，解析 Toggle 组件的 checked 属性

依赖: hdc 已安装并在 PATH 中，设备已通过 USB/WiFi 连接

hdc 安装方式:
  1. 下载安装 DevEco Studio: https://developer.huawei.com/consumer/cn/download/
  2. 将 hdc 所在目录加入 PATH:
     <DevEco Studio>/sdk/<版本>/openharmony/toolchains/
  3. 验证: hdc version
"""

import subprocess
import json
import os
import re
import sys
import time
import tempfile

# ── 配置 ──────────────────────────────────────────────
# 设置应用的候选包名/Ability 名（按优先级排列，脚本会依次尝试）
SETTINGS_CANDIDATES = [
    # (bundleName, moduleName, abilityName)
    ('com.huawei.hmossettings', 'entry', 'EntryAbility'),
    ('com.huawei.hmossettings', None,    'EntryAbility'),   # 不带 -m 参数
    ('com.huawei.hmossettings', 'entry', 'MainAbility'),
    ('com.huawei.hmossettings', None,    'MainAbility'),
    ('com.android.settings',    None,    'Settings'),
    ('com.android.settings',    None,    'MainSettings'),
]

TEXT_MOBILE_NETWORK = '移动网络'
TEXT_PERSONAL_HOTSPOT = '个人热点'
REMOTE_LAYOUT_PATH = '/data/local/tmp/layout.json'
NAV_WAIT = 2.5          # 页面跳转后等待秒数
DUMP_WAIT = 1.0         # dumpLayout 后等待秒数

# hdc 常见安装路径（未在 PATH 中找到时自动搜索）
HDC_COMMON_PATHS = [
    # DevEco Studio SDK 默认位置
    os.path.expandvars(r'%LOCALAPPDATA%\Huawei\DevEcoStudio\sdk'),
    os.path.expandvars(r'%USERPROFILE%\AppData\Local\Huawei\DevEcoStudio\sdk'),
    os.path.expandvars(r'%USERPROFILE%\AppData\Roaming\Huawei\DevEcoStudio\sdk'),
    r'C:\Program Files\Huawei\DevEco Studio\sdk',
    r'D:\DevEco Studio\sdk',
    # macOS / Linux
    os.path.expandvars(r'$HOME/Library/Huawei/DevEcoStudio/sdk'),
    os.path.expandvars(r'$HOME/Huawei/DevEcoStudio/sdk'),
    # HarmonyOS SDK (standalone)
    os.path.expandvars(r'%USERPROFILE%\Huawei\HarmonyOS_SDK'),
]
# ─────────────────────────────────────────────────────


def find_hdc() -> str:
    """查找 hdc 可执行文件路径，返回 'hdc' 或完整路径，找不到则返回 None"""
    # 先检查 PATH 中是否有
    try:
        r = subprocess.run(['hdc', 'version'],
                           capture_output=True, text=True, timeout=5)
        if 'Ver:' in r.stdout or 'Ver: ' in r.stdout:
            return 'hdc'
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # 在已知 SDK 路径中搜索
    for sdk_dir in HDC_COMMON_PATHS:
        if not os.path.isdir(sdk_dir):
            continue
        for root, dirs, files in os.walk(sdk_dir):
            if 'hdc.exe' in files or 'hdc' in files:
                # 优先选择 toolchains 目录下的
                hdc_path = os.path.join(root, 'hdc' if 'hdc' in files else 'hdc.exe')
                print(f"  [INFO] 自动找到 hdc: {hdc_path}")
                return hdc_path
            # 限制搜索深度
            depth = root.replace(sdk_dir, '').count(os.sep)
            if depth > 4:
                dirs.clear()
    return None


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
    global _HDC
    return run_cmd([_HDC, 'shell', *list(args)], timeout)


def dump_layout() -> dict:
    """
    获取当前页面控件树
    优先尝试解析 stdout，失败则从设备拉取 layout.json 文件
    """
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
    run_cmd([_HDC, 'file', 'recv', REMOTE_LAYOUT_PATH, local_path], timeout=15)

    if not os.path.exists(local_path):
        raise RuntimeError("无法获取布局文件: dumpLayout 失败且文件拉取失败")

    with open(local_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_bounds(bounds) -> tuple:
    """解析 bounds 字段，返回中心坐标 (x, y)"""
    if isinstance(bounds, str):
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
    # 优先选择可点击的组件
    clickable_types = ('Text', 'TextComponent', 'Button', 'Row', 'ListItem', 'RowListItem')
    clickable = [c for c in comps if c.get('clickable', False) or
                 c.get('type', '') in clickable_types]
    target = clickable[0] if clickable else comps[0]
    print(f"  -> 找到 '{text}' (共 {len(comps)} 个匹配)")
    return click_component(target, wait)


def get_toggle_state(layout: dict, target_text: str) -> str:
    """
    查找目标开关状态
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

    # 策略3: 带 checked/isOn 属性且靠近目标文本的组件
    checked_comps = find_components(
        layout, lambda c: 'checked' in c or 'isOn' in c
    )
    for c in checked_comps:
        if target_text in get_text(c):
            return _check_state(c)
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


def start_settings():
    """
    启动设置应用
    依次尝试候选包名/Ability，首个成功即停止
    """
    for idx, (bundle, mod, ability) in enumerate(SETTINGS_CANDIDATES):
        args = ['aa', 'start', '-n', bundle]
        if mod:
            args += ['-m', mod]
        args.append(ability)

        print(f"  -> 尝试 #{idx+1}: aa start -n {bundle}"
              + (f" -m {mod}" if mod else "") + f" {ability}")
        output = hdc_shell(*args, timeout=10)

        # aa start 失败时输出类似 "failed" 或 "error"
        if 'fail' in output.lower() or 'error' in output.lower():
            print(f"    失败: {output.strip()[:120]}")
            continue
        print(f"    成功")
        return True

    return False


def main():
    global _HDC

    print("=" * 55)
    print("  HarmonyOS 个人热点开关状态查询")
    print("  路径: 设置 > 移动网络 > 个人热点")
    print("=" * 55)

    # 查找 hdc
    _HDC = find_hdc()
    if not _HDC:
        print("\n[ERROR] 未找到 hdc 工具！")
        print("")
        print("hdc 是 DevEco Studio 自带的设备调试工具，安装步骤:")
        print("  1. 下载 DevEco Studio:")
        print("     https://developer.huawei.com/consumer/cn/download/")
        print("  2. 安装后，hdc 位于:")
        print("     <DevEco Studio>/sdk/<版本>/openharmony/toolchains/hdc.exe")
        print("  3. 将上述路径加入系统环境变量 PATH")
        print("  4. 重新打开终端，运行 hdc version 验证")
        print("")
        print("如果已安装但脚本未找到，请在脚本顶部 HDC_COMMON_PATHS 中添加实际路径")
        sys.exit(1)

    print(f"  hdc: {_HDC}")

    # 验证 hdc 可用
    ver = run_cmd([_HDC, 'version'], timeout=10)
    for line in ver.splitlines():
        if 'Ver:' in line:
            print(f"  hdc 版本: {line.strip()}")
            break

    # 检查设备连接
    list_output = run_cmd([_HDC, 'list', 'targets'], timeout=10)
    devices = [d.strip() for d in list_output.strip().splitlines()
               if d.strip() and 'Empty' not in d]
    if not devices:
        print("[ERROR] 未检测到已连接的设备，请先通过 USB/WiFi 连接设备")
        print("  USB:  连接数据线 > 设备开启「USB 调试」> hdc list targets")
        print("  WiFi: hdc tconn <设备IP>:8710")
        sys.exit(1)
    print(f"  已连接: {devices[0]}")

    # Step 1: 启动设置应用
    print("\n[1/4] 启动设置应用...")
    if not start_settings():
        print("\n[FAIL] 所有候选包名均启动失败！")
        print("请手动在设备上打开「设置」应用，然后重新运行脚本")
        print("或者通过以下命令确认正确的设置应用包名:")
        print(f"  {_HDC} shell bm dump -a | grep -i settings")
        print("然后将正确的包名/Ability名加到 SETTINGS_CANDIDATES 中")
        return
    time.sleep(3)

    # Step 2: 进入移动网络
    print("\n[2/4] 导航到「移动网络」...")
    layout = dump_layout()
    if not click_by_text(layout, TEXT_MOBILE_NETWORK):
        print("\n[FAIL] 未找到「移动网络」入口")
        print("可能原因: 系统语言非中文、设置页面结构不同")
        print("建议: 修改脚本 TEXT_MOBILE_NETWORK 为对应语言的文本")
        debug_dump(layout)
        return

    # Step 3: 进入个人热点
    print("\n[3/4] 导航到「个人热点」...")
    layout = dump_layout()
    if not click_by_text(layout, TEXT_PERSONAL_HOTSPOT):
        print("\n[FAIL] 未找到「个人热点」入口")
        print("可能原因: 系统语言非中文、设置页面结构不同")
        print("建议: 修改脚本 TEXT_PERSONAL_HOTSPOT 为对应语言的文本")
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
