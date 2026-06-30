"""
HarmonyOS 设置操作 API

提供设置查询和开关操作的编程接口，可被 CLI 脚本或其他程序调用。
所有业务逻辑在此层，CLI 脚本只是调度器。

架构:
  hdc_utils.py  (底层工具: 设备连接、布局获取、组件搜索)
  settings_api.py (本文件: 业务 API)
  xxx_manager.py (CLI 脚本: 命令行参数 → 调用 API)

用法:
  from settings_api import query_dnd, set_dnd
  status = query_dnd()                    # → 'on' | 'off' | 'unknown'
  set_dnd('on')                           # → True | False

⚠ 新增 API 后，同步更新 SKILL.md 第 3 步的「已有 API 函数」表格。
"""

from hdc_utils import *


# ═══════════════════════════════════════════════════════════════
# 通用 API — 适用于任何设置项
# ═══════════════════════════════════════════════════════════════

def query_setting(entry, target, form, scroll=4,
                  text_on='已开启', text_off='已关闭'):
    """
    查询任意设置项状态

    Args:
        entry: 设置首页入口文本 (如 '关怀和无障碍')
        target: 目标设置项文本 (如 '放大手势')
        form: 控件形态 ('toggle_row'/'button_card'/'text_value'/'slider_row'/'nav_item')
        scroll: 滑动屏数 (知识库第八章)
        text_on/text_off: text_value 形态的状态文本

    Returns:
        'on' | 'off' | 'unknown' | 'unknown(xxx)' | None(未找到)
    """
    layout = navigate_to_page(entry, scroll)
    if not layout:
        return None
    layout, status = find_target_with_scroll(
        layout, target, form, scroll, text_on, text_off)
    return status


def toggle_setting(entry, target, form, desired, scroll=4,
                   third_level_toggle=None,
                   text_on='已开启', text_off='已关闭'):
    """
    切换任意设置项状态

    Args:
        desired: 'on' 或 'off'
        third_level_toggle: 子页面 Toggle 文本 (text_value 形态开关操作时需要)

    Returns:
        (success: bool, new_status: str)
    """
    layout = navigate_to_page(entry, scroll)
    if not layout:
        return False, None

    layout, status = find_target_with_scroll(
        layout, target, form, scroll, text_on, text_off)
    if status is None:
        return False, None

    # 已是目标状态
    if status == desired:
        return True, status

    # 执行操作
    success = toggle_operation(layout, target, form, desired, third_level_toggle)
    if not success:
        return False, status

    # 验证
    time.sleep(1)
    if form == 'text_value' and third_level_toggle:
        go_back(2.0)
    layout = dump_layout()
    new_status = read_status(layout, target, form, text_on, text_off)
    return (new_status == desired), new_status


def check_entry_exists(entry, target, scroll=4):
    """
    检查某个入口是否存在（用于开发者模式等"存在即开启"的场景）

    Returns:
        True=入口存在, False=不存在
    """
    layout = navigate_to_page(entry, scroll)
    if not layout:
        return False
    for i in range(scroll + 1):
        layout = dump_layout()
        if find_by_text(layout, target):
            return True
        if i < scroll:
            swipe_up()
            time.sleep(2)
    return False


def query_subpage_toggle(entry, target, scroll=4):
    """
    进入子页面查询 Toggle 状态（用于 nav_item 形态如个人热点）

    Returns:
        'on' | 'off' | 'unknown' | None
    """
    layout = navigate_to_page(entry, scroll)
    if not layout:
        return None
    # 查找并点击目标项
    found = find_by_text(layout, target)
    if not found:
        for i in range(scroll):
            swipe_up()
            layout = dump_layout()
            found = find_by_text(layout, target)
            if found:
                break
    if not found:
        return None
    click_by_text(layout, target, 2.5)
    sub_layout = dump_layout()
    toggles = find_toggles(sub_layout)
    if not toggles:
        return 'unknown'
    for tg in toggles:
        if target in get_text(tg) or '热点' in get_text(tg):
            return read_toggle_state(tg)
    return read_toggle_state(toggles[0])


# ═══════════════════════════════════════════════════════════════
# 专用 API — 每个设置项一组函数，封装具体参数
# ═══════════════════════════════════════════════════════════════

# ── 勿扰模式 ──

def query_dnd():
    """查询勿扰模式状态 → 'on' | 'off' | 'unknown'"""
    return query_setting('情景模式', '免打扰', 'button_card', scroll=2)


def set_dnd(desired):
    """设置勿扰模式 → (success, new_status)"""
    return toggle_setting('情景模式', '免打扰', 'button_card', desired, scroll=2)


# ── 放大手势 ──

def query_zoom_gesture():
    """查询放大手势状态 → 'on' | 'off' | 'unknown'"""
    return query_setting('关怀和无障碍', '放大手势', 'text_value', scroll=4)


def set_zoom_gesture(desired):
    """设置放大手势 → (success, new_status)"""
    return toggle_setting('关怀和无障碍', '放大手势', 'text_value', desired,
                          scroll=4, third_level_toggle='放大手势')


# ── 开发者模式 ──

def query_developer_mode():
    """查询开发者模式状态 → 'on' | 'off'"""
    return 'on' if check_entry_exists('系统', '开发者选项', scroll=4) else 'off'


# ── 个人热点 ──

def query_personal_hotspot():
    """查询个人热点状态 → 'on' | 'off' | 'unknown'"""
    return query_subpage_toggle('移动网络', '个人热点', scroll=1)


# ── 省电模式 ──

def query_power_saving():
    """查询省电模式状态 → 'on' | 'off' | 'unknown'"""
    return query_setting('电池', '省电模式', 'toggle_row', scroll=4)


def set_power_saving(desired):
    """设置省电模式 → (success, new_status)"""
    return toggle_setting('电池', '省电模式', 'toggle_row', desired, scroll=4)


# ── 飞行模式 ──

def query_flight_mode():
    """查询飞行模式状态 → 'on' | 'off' | 'unknown'"""
    return query_setting('移动网络', '飞行模式', 'toggle_row', scroll=1)


def set_flight_mode(desired):
    """设置飞行模式 → (success, new_status)"""
    return toggle_setting('移动网络', '飞行模式', 'toggle_row', desired, scroll=1)


# ── WLAN ──

def query_wlan():
    """查询 WLAN 开关状态 → 'on' | 'off' | 'unknown'"""
    return query_setting('WLAN', 'WLAN', 'toggle_row', scroll=4)


def set_wlan(desired):
    """设置 WLAN 开关 → (success, new_status)"""
    return toggle_setting('WLAN', 'WLAN', 'toggle_row', desired, scroll=4)


# ── 蓝牙 ──

def query_bluetooth():
    """查询蓝牙开关状态 → 'on' | 'off' | 'unknown'"""
    return query_setting('星闪和蓝牙', '蓝牙', 'toggle_row', scroll=2)


def _open_bluetooth_page():
    """打开蓝牙设置页面，等待设备列表加载"""
    restart_settings()
    layout = dump_layout()
    if not (find_by_text(layout, '已配对设备') or find_by_text(layout, '其他设备')):
        if not click_by_text(layout, '星闪和蓝牙'):
            for _ in range(3):
                swipe_up()
                layout = dump_layout()
                if click_by_text(layout, '星闪和蓝牙'):
                    break
            else:
                return None
    # 等待设备列表
    for _ in range(10):
        layout = dump_layout()
        if find_by_text(layout, '已配对设备') or find_by_text(layout, '其他设备'):
            break
        time.sleep(1)
    time.sleep(5)
    return dump_layout()


def query_bluetooth_device(device_name):
    """
    查询蓝牙设备连接状态

    Returns:
        'connected' | 'disconnected' | 'not_found' | 'bluetooth_off'
    """
    layout = _open_bluetooth_page()
    if not layout:
        return 'not_found'
    if read_status_toggle_row(layout, '蓝牙') != 'on':
        return 'bluetooth_off'
    # 查找设备
    for _ in range(5):
        layout = dump_layout()
        comp = find_by_text(layout, device_name)
        if comp:
            center = parse_bounds(attr(comp[0], 'bounds'))
            if center:
                for c in find_by_text(layout, '已连接'):
                    cc = parse_bounds(attr(c, 'bounds'))
                    if cc and abs(cc[1] - center[1]) < 80:
                        return 'connected'
                return 'disconnected'
        swipe_up(2.5)
        time.sleep(2)
    return 'not_found'


def connect_bluetooth(device_name):
    """
    连接蓝牙设备

    Returns:
        (success: bool, status: str)
    """
    layout = _open_bluetooth_page()
    if not layout:
        return False, 'not_found'
    if read_status_toggle_row(layout, '蓝牙') != 'on':
        toggle_operation(layout, '蓝牙', 'toggle_row', 'on')
        time.sleep(3)

    # 查找设备
    for _ in range(5):
        layout = dump_layout()
        comp = find_by_text(layout, device_name)
        if comp:
            break
        swipe_up(2.5)
        time.sleep(2)
    else:
        return False, 'not_found'

    # 检查是否已连接
    center = parse_bounds(attr(comp[0], 'bounds'))
    for c in find_by_text(layout, '已连接'):
        cc = parse_bounds(attr(c, 'bounds'))
        if cc and abs(cc[1] - center[1]) < 80:
            return True, 'connected'

    # 点击设备
    click_by_text(layout, device_name, 1.0)

    # 处理配对弹窗
    for _ in range(10):
        layout = dump_layout()
        btn = find_button(layout, '配对')
        if btn:
            bc = parse_bounds(attr(btn[0], 'bounds'))
            if bc:
                click_at(bc[0], bc[1], 2.0)
                break
        time.sleep(1)

    # 等待连接
    for _ in range(15):
        time.sleep(2)
        layout = dump_layout()
        for c in find_by_text(layout, '已连接'):
            cc = parse_bounds(attr(c, 'bounds'))
            if cc and center and abs(cc[1] - center[1]) < 80:
                return True, 'connected'
        # 处理弹窗
        for btn_text in ['确定', '知道了']:
            btn = find_button(layout, btn_text)
            if btn:
                bc = parse_bounds(attr(btn[0], 'bounds'))
                if bc:
                    click_at(bc[0], bc[1], 2.0)
                    break

    return False, 'disconnected'


def disconnect_bluetooth(device_name):
    """
    断开蓝牙设备

    Returns:
        (success: bool, status: str)
    """
    layout = _open_bluetooth_page()
    if not layout:
        return False, 'not_found'
    if read_status_toggle_row(layout, '蓝牙') != 'on':
        return True, 'bluetooth_off'

    # 查找设备
    for _ in range(5):
        layout = dump_layout()
        comp = find_by_text(layout, device_name)
        if comp:
            break
        swipe_up(2.5)
        time.sleep(2)
    else:
        return False, 'not_found'

    center = parse_bounds(attr(comp[0], 'bounds'))
    # 检查是否已断开
    connected = False
    for c in find_by_text(layout, '已连接'):
        cc = parse_bounds(attr(c, 'bounds'))
        if cc and abs(cc[1] - center[1]) < 80:
            connected = True
            break
    if not connected:
        return True, 'disconnected'

    # 点击设备
    click_by_text(layout, device_name, 1.0)
    time.sleep(2)

    # 处理弹窗
    for btn_text in ['确定', '断开', '取消']:
        layout = dump_layout()
        btn = find_button(layout, btn_text)
        if btn:
            bc = parse_bounds(attr(btn[0], 'bounds'))
            if bc:
                click_at(bc[0], bc[1], 1.0)
                break

    # 等待断开
    for _ in range(15):
        time.sleep(2)
        layout = dump_layout()
        still_connected = False
        for c in find_by_text(layout, '已连接'):
            cc = parse_bounds(attr(c, 'bounds'))
            if cc and abs(cc[1] - center[1]) < 80:
                still_connected = True
                break
        if not still_connected:
            return True, 'disconnected'

    return False, 'connected'


# ── 屏幕亮度 (slider_row 示例) ──

def query_brightness():
    """查询屏幕亮度值 → 字符串(如 '81.000000') | 'unknown'"""
    return query_setting('显示和亮度', '亮度', 'slider_row', scroll=2)
