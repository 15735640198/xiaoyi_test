"""
HarmonyOS hdc 工具模块

提供设备连接、布局获取、组件搜索、UI 操作、状态读取等公共功能。
所有设置操作脚本共享此模块。

用法:
  from hdc_utils import *
"""

import subprocess
import json
import os
import re
import sys
import time
import tempfile

# ═══════════════════════════════════════════════════════════════
# 常量
# ═══════════════════════════════════════════════════════════════

SETTINGS_BUNDLE = 'com.huawei.hmos.settings'
SETTINGS_ABILITY = 'com.huawei.hmos.settings.MainAbility'

HDC_COMMON_PATHS = [
    r'D:\lzs\devecostudio-windows-6.1.1.280\DevEco Studio\sdk',
    os.path.expandvars(r'%LOCALAPPDATA%\Huawei\DevEcoStudio\sdk'),
    r'C:\Program Files\Huawei\DevEco Studio\sdk',
]

NAV_WAIT = 2.5
DUMP_WAIT = 1.0

HDC = None  # hdc 可执行文件路径，find_hdc() 后赋值
_screen_size = None  # 屏幕尺寸 (width, height)，get_screen_size() 后赋值


# ═══════════════════════════════════════════════════════════════
# 设备连接
# ═══════════════════════════════════════════════════════════════

def find_hdc():
    """查找 hdc 可执行文件路径，返回路径字符串"""
    global HDC
    try:
        r = subprocess.run(['hdc', 'version'], capture_output=True, text=True, timeout=5)
        if 'Ver:' in r.stdout:
            HDC = 'hdc'
            return HDC
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    for sdk_dir in HDC_COMMON_PATHS:
        if not os.path.isdir(sdk_dir):
            continue
        for root, dirs, files in os.walk(sdk_dir):
            if 'hdc.exe' in files:
                HDC = os.path.join(root, 'hdc.exe')
                return HDC
            depth = root.replace(sdk_dir, '').count(os.sep)
            if depth > 4:
                dirs.clear()
    HDC = 'hdc'
    return HDC


def run_cmd(cmd, timeout=30):
    """执行命令，返回合并的 stdout+stderr"""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout, encoding='utf-8', errors='replace')
        return (r.stdout or '') + (r.stderr or '')
    except FileNotFoundError:
        print(f"[ERROR] 命令不存在: {cmd[0]}")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        return ''


def hdc_shell(*args, timeout=30):
    """执行 hdc shell 命令"""
    return run_cmd([HDC, 'shell', *list(args)], timeout)


def check_device():
    """检查设备连接，返回设备 ID 或退出"""
    list_output = run_cmd([HDC, 'list', 'targets'], timeout=10)
    devices = [d.strip() for d in list_output.strip().splitlines()
               if d.strip() and 'Empty' not in d]
    if not devices:
        print("[ERROR] 未检测到设备")
        sys.exit(1)
    return devices[0]


# ═══════════════════════════════════════════════════════════════
# 布局获取
# ═══════════════════════════════════════════════════════════════

def dump_layout():
    """dumpLayout → 接收文件 → 返回 JSON dict"""
    output = hdc_shell('uitest', 'dumpLayout')
    time.sleep(DUMP_WAIT)
    m = re.search(r'saved to:\s*(/\S+\.json)', output)
    remote = m.group(1) if m else '/data/local/tmp/layout.json'
    local = os.path.join(tempfile.gettempdir(), 'hm_layout.json')
    run_cmd([HDC, 'file', 'recv', remote, local], timeout=15)
    with open(local, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_screen_size():
    """获取屏幕尺寸 (width, height)，首次调用时从 dumpLayout 根节点获取并缓存"""
    global _screen_size
    if _screen_size:
        return _screen_size
    layout = dump_layout()
    root_bounds = attr(layout, 'bounds')
    if root_bounds:
        fb = parse_full_bounds(root_bounds)
        if fb and fb[2] > 0 and fb[3] > 0:
            _screen_size = (fb[2], fb[3])
            return _screen_size
    _screen_size = (1260, 2772)
    return _screen_size


# ═══════════════════════════════════════════════════════════════
# 属性读取
# ═══════════════════════════════════════════════════════════════

def attr(comp, key, default=''):
    """读取组件属性 — 属性在 attributes 字典中，不是顶层"""
    a = comp.get('attributes')
    return a.get(key, default) if a else comp.get(key, default)


def get_text(comp):
    """读取组件文本 — 优先 text，其次 description"""
    return attr(comp, 'text', '') or attr(comp, 'description', '') or ''


# ═══════════════════════════════════════════════════════════════
# 组件搜索
# ═══════════════════════════════════════════════════════════════

def find_components(node, predicate, results=None):
    """递归搜索所有满足 predicate 的组件"""
    if results is None:
        results = []
    if isinstance(node, dict):
        if predicate(node):
            results.append(node)
        for c in node.get('children', []):
            find_components(c, predicate, results)
    elif isinstance(node, list):
        for item in node:
            find_components(item, predicate, results)
    return results


def find_by_text(node, text):
    """子串匹配查找文本组件"""
    return find_components(node, lambda c: text in get_text(c))


def find_by_text_nearest(node, text):
    """
    子串匹配查找文本组件，按文本长度差升序排序（最接近的优先）。
    避免 find_by_text 的子串碰撞: 搜索 '星闪' 时，
    '星闪' 标签(2字) 排在 '星闪和蓝牙' 标题(5字) 前面。
    """
    comps = find_by_text(node, text)
    return sorted(comps, key=lambda c: abs(len(get_text(c).strip()) - len(text)))


def find_button(node, text):
    """
    查找按钮: 子串匹配但排除含'设备'的长文本
    例如 find_button(layout, '配对') 匹配 "配对" 但不匹配 "已配对设备"
    """
    return find_components(node, lambda c: (
        text in get_text(c) and
        '设备' not in get_text(c) and
        len(get_text(c).strip()) <= 5
    ))


def find_toggles(node):
    """查找所有 Toggle/Switch 组件"""
    return find_components(node,
        lambda c: attr(c, 'type', '').lower() in ('toggle', 'switch'))


def find_sliders(node):
    """查找所有 Slider 组件"""
    return find_components(node,
        lambda c: attr(c, 'type', '').lower() == 'slider')


def find_buttons(node):
    """查找所有 Button 组件"""
    return find_components(node, lambda c: attr(c, 'type') == 'Button')


def find_menu_items(node):
    """查找所有 MenuItem 组件（选择器选项）"""
    return find_components(node, lambda c: attr(c, 'type') == 'MenuItem')


# ═══════════════════════════════════════════════════════════════
# 坐标解析
# ═══════════════════════════════════════════════════════════════

def parse_bounds(bounds):
    """解析 bounds 字符串 '[l,t][r,b]' → (cx, cy)"""
    if isinstance(bounds, str):
        nums = re.findall(r'\d+', bounds)
        if len(nums) >= 4:
            return ((int(nums[0]) + int(nums[2])) // 2,
                    (int(nums[1]) + int(nums[3])) // 2)
    return None


def parse_full_bounds(bounds):
    """解析 bounds 字符串 '[l,t][r,b]' → (l, t, r, b)"""
    if isinstance(bounds, str):
        nums = re.findall(r'\d+', bounds)
        if len(nums) >= 4:
            return (int(nums[0]), int(nums[1]), int(nums[2]), int(nums[3]))
    return None


# ═══════════════════════════════════════════════════════════════
# UI 操作
# ═══════════════════════════════════════════════════════════════

def click_at(x, y, wait=NAV_WAIT):
    """点击指定坐标"""
    hdc_shell('uitest', 'uiInput', 'click', str(x), str(y))
    time.sleep(wait)


def click_by_text(layout, text, wait=NAV_WAIT):
    """
    点击文本组件 — 自动找可点击父级
    Text 组件通常 clickable=false，真正可点击的是父级 Row
    """
    comps = find_by_text_nearest(layout, text)
    if not comps:
        return False
    center = parse_bounds(attr(comps[0], 'bounds'))
    if not center:
        return False
    # 找包含文本中心的最小可点击组件
    clickables = find_components(layout, lambda c: attr(c, 'clickable') == 'true')
    best = None
    best_area = float('inf')
    for c in clickables:
        fb = parse_full_bounds(attr(c, 'bounds', ''))
        if fb and fb[0] <= center[0] <= fb[2] and fb[1] <= center[1] <= fb[3]:
            area = (fb[2] - fb[0]) * (fb[3] - fb[1])
            if area < best_area:
                best_area = area
                best = ((fb[0] + fb[2]) // 2, (fb[1] + fb[3]) // 2)
    target = best if best else center
    click_at(target[0], target[1], wait)
    return True


def swipe_up(wait=1.5):
    """向上滑动（查看下方内容）"""
    w, h = get_screen_size()
    cx = str(w // 2)
    hdc_shell('uitest', 'uiInput', 'swipe', cx, str(int(h * 0.85)), cx, str(int(h * 0.25)))
    time.sleep(wait)


def swipe_down(wait=1.5):
    """向下滑动（查看上方内容）"""
    w, h = get_screen_size()
    cx = str(w // 2)
    hdc_shell('uitest', 'uiInput', 'swipe', cx, str(int(h * 0.25)), cx, str(int(h * 0.85)))
    time.sleep(wait)


def go_back(wait=1.5):
    """按返回键"""
    hdc_shell('uitest', 'uiInput', 'keyEvent', 'Back')
    time.sleep(wait)


# ═══════════════════════════════════════════════════════════════
# 状态读取
# ═══════════════════════════════════════════════════════════════

def read_toggle_state(comp):
    """读取 Toggle 状态 → 'on' | 'off' | 'unknown'"""
    val = attr(comp, 'checked', None)
    if val is True or val in ('true', 'True', 1, '1'):
        return 'on'
    if val is False or val in ('false', 'False', 0, '0'):
        return 'off'
    return 'unknown'


def read_status_toggle_row(layout, target_text):
    """toggle_row: 找目标文本附近的 Toggle, 读 checked"""
    comps = find_by_text_nearest(layout, target_text)
    if not comps:
        return None
    toggles = find_toggles(layout)
    for comp in comps:
        center = parse_bounds(attr(comp, 'bounds'))
        if not center:
            continue
        for tg in toggles:
            tc = parse_bounds(attr(tg, 'bounds'))
            if tc and abs(tc[1] - center[1]) < 80 and abs(tc[0] - center[0]) < 1200:
                return read_toggle_state(tg)
    return 'unknown'


def read_status_button_card(layout, target_text):
    """button_card: 找目标附近的 Button, 读按钮文本"""
    comps = find_by_text_nearest(layout, target_text)
    if not comps:
        return None
    buttons = find_buttons(layout)
    for comp in comps:
        center = parse_bounds(attr(comp, 'bounds'))
        if not center:
            continue
        for btn in buttons:
            bc = parse_bounds(attr(btn, 'bounds'))
            if bc and 20 < abs(bc[1] - center[1]) < 300:
                bt = get_text(btn)
                if '立即开启' in bt or '开启' in bt:
                    return 'off'
                if '立即关闭' in bt or '关闭' in bt:
                    return 'on'
    return 'unknown'


def read_status_text_value(layout, target_text, text_on='已开启', text_off='已关闭'):
    """text_value: 找目标右侧同行 Text, 读其内容"""
    comps = find_by_text_nearest(layout, target_text)
    if not comps:
        return None
    all_texts = find_components(layout, lambda c: attr(c, 'type') == 'Text')
    for comp in comps:
        center = parse_bounds(attr(comp, 'bounds'))
        if not center:
            continue
        for t in all_texts:
            tc = parse_bounds(attr(t, 'bounds'))
            if tc and abs(tc[1] - center[1]) < 60 and tc[0] > center[0] + 50:
                val = get_text(t)
                if text_off in val:
                    return 'off'
                if text_on in val:
                    return 'on'
                # 不是已开启/已关闭，可能是描述文字，继续找下一个
                continue
    return 'unknown'


def read_status_slider(layout, target_text):
    """slider_row: 读 Slider 的 text/originalText 属性 (不是 value!)"""
    comps = find_by_text_nearest(layout, target_text)
    if not comps:
        return None
    sliders = find_sliders(layout)
    for comp in comps:
        center = parse_bounds(attr(comp, 'bounds'))
        if not center:
            continue
        for sl in sliders:
            sc = parse_bounds(attr(sl, 'bounds'))
            if sc and abs(sc[1] - center[1]) < 200:
                return attr(sl, 'text', attr(sl, 'originalText', ''))
    return 'unknown'


def read_text_value_raw(layout, target_text):
    """读取 text_value 形态目标项的右侧文本内容（不做 on/off 判断，直接返回文本）"""
    comps = find_by_text_nearest(layout, target_text)
    if not comps:
        return None
    all_texts = find_components(layout, lambda c: attr(c, 'type') == 'Text')
    for comp in comps:
        center = parse_bounds(attr(comp, 'bounds'))
        if not center:
            continue
        for t in all_texts:
            tc = parse_bounds(attr(t, 'bounds'))
            if tc and abs(tc[1] - center[1]) < 60 and tc[0] > center[0] + 50:
                return get_text(t)
    return None


def read_status(layout, target_text, control_form,
                text_on='已开启', text_off='已关闭'):
    """
    根据 control_form 调用对应的状态读取函数
    返回: 'on' | 'off' | 'unknown' | 'unknown(xxx)' | None(未找到)
    """
    if control_form == 'toggle_row':
        return read_status_toggle_row(layout, target_text)
    elif control_form == 'button_card':
        return read_status_button_card(layout, target_text)
    elif control_form == 'text_value':
        return read_status_text_value(layout, target_text, text_on, text_off)
    elif control_form == 'slider_row':
        return read_status_slider(layout, target_text)
    elif control_form == 'nav_item':
        # 导航项无直接状态，需进入子页面
        return 'unknown'
    else:
        return 'unknown'


# ═══════════════════════════════════════════════════════════════
# 开关操作
# ═══════════════════════════════════════════════════════════════

def toggle_operation(layout, target_text, control_form, desired,
                     third_level_toggle_text=None):
    """
    根据 control_form 执行开关操作
    desired: 'on' 或 'off'
    返回: True 如果操作成功
    """
    if control_form == 'toggle_row':
        return _toggle_toggle_row(layout, target_text, desired)
    elif control_form == 'button_card':
        return _toggle_button_card(layout, target_text, desired)
    elif control_form == 'text_value' and third_level_toggle_text:
        return _toggle_text_value(layout, target_text, desired, third_level_toggle_text)
    else:
        return False


def _toggle_toggle_row(layout, target_text, desired):
    """toggle_row: 直接点击 Toggle"""
    comps = find_by_text_nearest(layout, target_text)
    if not comps:
        return False
    toggles = find_toggles(layout)
    for comp in comps:
        center = parse_bounds(attr(comp, 'bounds'))
        if not center:
            continue
        for tg in toggles:
            tc = parse_bounds(attr(tg, 'bounds'))
            if tc and abs(tc[1] - center[1]) < 80 and abs(tc[0] - center[0]) < 1200:
                click_at(tc[0], tc[1], 2.0)
                return True
    return False


def _toggle_button_card(layout, target_text, desired):
    """button_card: 点击 立即开启/立即关闭 按钮"""
    comps = find_by_text_nearest(layout, target_text)
    if not comps:
        return False
    buttons = find_buttons(layout)
    for comp in comps:
        center = parse_bounds(attr(comp, 'bounds'))
        if not center:
            continue
        for btn in buttons:
            bc = parse_bounds(attr(btn, 'bounds'))
            if bc and 20 < abs(bc[1] - center[1]) < 300:
                bt = get_text(btn)
                if desired == 'on' and ('立即开启' in bt or '开启' in bt):
                    click_at(bc[0], bc[1], 2.5)
                    return True
                if desired == 'off' and ('立即关闭' in bt or '关闭' in bt):
                    click_at(bc[0], bc[1], 2.5)
                    return True
    return False


def _toggle_text_value(layout, target_text, desired, toggle_text):
    """
    text_value: 进入子页面 → 找 Toggle → 切换
    toggle_text: 子页面中 Toggle 的文本
    """
    if not click_by_text(layout, target_text, 2.5):
        return False
    sub_layout = dump_layout()
    toggles = find_toggles(sub_layout)
    # 优先找名称匹配的 Toggle
    for tg in toggles:
        if toggle_text in get_text(tg):
            tc = parse_bounds(attr(tg, 'bounds'))
            if tc:
                state = read_toggle_state(tg)
                if state != desired:
                    click_at(tc[0], tc[1], 2.0)
                return True
    # 找不到名称匹配，用第一个 Toggle
    if toggles:
        tc = parse_bounds(attr(toggles[0], 'bounds'))
        if tc:
            state = read_toggle_state(toggles[0])
            if state != desired:
                click_at(tc[0], tc[1], 2.0)
            return True
    return False


def set_slider(layout, target_text, value):
    """
    slider_row: 在 Slider 轨道上点击目标位置设值
    value: 0-100
    返回: True 如果找到并点击了 Slider
    """
    comps = find_by_text_nearest(layout, target_text)
    if not comps:
        return False
    sliders = find_sliders(layout)
    for comp in comps:
        center = parse_bounds(attr(comp, 'bounds'))
        if not center:
            continue
        for sl in sliders:
            sc = parse_bounds(attr(sl, 'bounds'))
            if sc and abs(sc[1] - center[1]) < 200:
                fb = parse_full_bounds(attr(sl, 'bounds', ''))
                if fb:
                    target_x = int(fb[0] + (fb[2] - fb[0]) * value / 100)
                    target_y = (fb[1] + fb[3]) // 2
                    click_at(target_x, target_y)
                    return True
    return False


def input_text(x, y, text):
    """
    在指定坐标的文本框中输入文本（长按全选 → 替换输入）
    """
    # 长按显示上下文菜单
    hdc_shell('uitest', 'uiInput', 'longClick', str(x), str(y))
    time.sleep(1.5)
    # 点击"全选"
    layout = dump_layout()
    if not click_by_text(layout, '全选', 0.5):
        # 全选菜单未出现，直接点击输入
        click_at(x, y, 0.5)
    # 输入新文本（替换选中的文本）
    hdc_shell('uitest', 'uiInput', 'text', text)
    time.sleep(1)


# ═══════════════════════════════════════════════════════════════
# 导航
# ═══════════════════════════════════════════════════════════════

def restart_settings():
    """强制重启设置应用，确保从主页开始"""
    hdc_shell('aa', 'force-stop', SETTINGS_BUNDLE)
    time.sleep(1)
    hdc_shell('aa', 'start', '-a', SETTINGS_ABILITY, '-b', SETTINGS_BUNDLE)
    time.sleep(3)


def navigate_to_page(entry_text, scroll_screens=4):
    """
    启动设置并导航到目标页面
    返回: 页面 layout (dict) 或 None
    """
    restart_settings()
    layout = dump_layout()
    if click_by_text(layout, entry_text):
        return dump_layout()
    # 滑动查找入口
    for i in range(scroll_screens):
        swipe_up()
        layout = dump_layout()
        if click_by_text(layout, entry_text):
            return dump_layout()
    return None


def find_target_with_scroll(layout, target_text, control_form,
                            scroll_screens=4, text_on='已开启', text_off='已关闭'):
    """
    在页面上查找目标项，必要时滑动
    返回: (layout, status) 或 (layout, None)
    """
    status = read_status(layout, target_text, control_form, text_on, text_off)
    if status is not None:
        return layout, status
    for i in range(scroll_screens):
        swipe_up()
        layout = dump_layout()
        status = read_status(layout, target_text, control_form, text_on, text_off)
        if status is not None:
            return layout, status
    return layout, None


def search_setting(keyword, result_text=None):
    """
    通过设置首页搜索框搜索并跳转到目标设置页

    适用于无法通过常规导航到达、或导航层级过深的设置项。
    流程: 重启设置 → 点搜索框 → 输入关键词 → 点搜索结果 → 返回目标页

    Args:
        keyword: 搜索关键词 (输入到搜索框)
        result_text: 要点击的搜索结果文本 (默认用 keyword)
                     注意: 搜索结果文本可能与输入不同 (如带空格)

    Returns:
        目标页面 layout (dict) 或 None
    """
    restart_settings()
    layout = dump_layout()
    # 动态定位搜索框 (Search/SearchField 组件)
    search_comp = None
    for c in find_components(layout, lambda c: attr(c, 'type') in ('Search', 'SearchField')):
        search_comp = c
        break
    if search_comp:
        center = parse_bounds(attr(search_comp, 'bounds'))
        if center:
            click_at(center[0], center[1], 2.0)
    else:
        w, h = get_screen_size()
        click_at(w // 2, int(h * 0.14), 2.0)
    layout = dump_layout()
    # 找 TextInput 并点击激活
    for c in find_components(layout, lambda c: attr(c, 'type') == 'TextInput'):
        center = parse_bounds(attr(c, 'bounds'))
        if center:
            click_at(center[0], center[1], 0.5)
            break
    # 输入搜索文本
    hdc_shell('uitest', 'uiInput', 'text', keyword)
    time.sleep(3)
    # 点击搜索结果
    layout = dump_layout()
    target = result_text or keyword
    if click_by_text(layout, target, 3.0):
        return dump_layout()
    return None
