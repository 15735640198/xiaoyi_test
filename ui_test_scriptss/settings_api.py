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


# ── 星闪 ──

def query_nearlink():
    """查询星闪开关状态 → 'on' | 'off' | 'unknown'"""
    return query_setting('星闪和蓝牙', '星闪', 'toggle_row', scroll=2)


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


# ── 朗读速度（语速）──

def _navigate_to_speech_rate_page():
    """
    导航到语速设置页面: 设置 > 关怀和无障碍 > 屏幕朗读 > 更多设置 > 语音设置
    返回: 页面 layout 或 None
    """
    layout = navigate_to_page('关怀和无障碍', 4)
    if not layout:
        return None
    # 点击"屏幕朗读"进入子页面
    if not click_by_text(layout, '屏幕朗读', 2.5):
        for _ in range(4):
            swipe_up()
            layout = dump_layout()
            if click_by_text(layout, '屏幕朗读', 2.5):
                break
        else:
            return None
    # 点击"更多设置"进入第三级页面
    layout = dump_layout()
    if not click_by_text(layout, '更多设置', 2.5):
        for _ in range(3):
            swipe_up()
            layout = dump_layout()
            if click_by_text(layout, '更多设置', 2.5):
                break
        else:
            return None
    # 点击"语音设置"进入第四级页面
    layout = dump_layout()
    if not click_by_text(layout, '语音设置', 2.5):
        for _ in range(3):
            swipe_up()
            layout = dump_layout()
            if click_by_text(layout, '语音设置', 2.5):
                break
        else:
            return None
    return dump_layout()


def query_speech_rate():
    """
    查询语速（朗读速度） → 字符串(如 '10000.000000') | 'unknown' | None
    """
    layout = _navigate_to_speech_rate_page()
    if not layout:
        return None
    return read_status(layout, '语速', 'slider_row')


def set_speech_rate(value):
    """
    设置语速（朗读速度）
    value: 0-100（轨道百分比）
    返回: (success: bool, new_value: str)
    """
    layout = _navigate_to_speech_rate_page()
    if not layout:
        return False, None
    success = set_slider(layout, '语速', value)
    if not success:
        return False, None
    time.sleep(1)
    layout = dump_layout()
    new_val = read_status(layout, '语速', 'slider_row')
    return (new_val is not None and new_val != 'unknown'), new_val


# ── 锁屏方式 ──

def query_lock_screen_method():
    """
    查询锁屏方式状态 → dict | None

    返回:
        {
            'face': 'enrolled' | 'not_enrolled' | 'unknown',
            'fingerprint': 'enrolled' | 'not_enrolled' | 'unknown',
            'lock_password': 'set' | 'unknown',
        }

    注意: 锁屏密码类型(图案/PIN/密码)需进入安全验证页面才能查看，无法自动化查询。
          若人脸或指纹已录入，可推断锁屏密码已设置。
    """
    layout = navigate_to_page('生物识别和密码', 2)
    if not layout:
        return None

    result = {'face': 'unknown', 'fingerprint': 'unknown', 'lock_password': 'unknown'}

    # 人脸识别和指纹是卡片布局（左右并排），状态在 Column 文本中（如 "人脸识别, 未录入"）
    for keyword, key in [('人脸识别', 'face'), ('指纹', 'fingerprint')]:
        comps = find_by_text(layout, keyword)
        for c in comps:
            text = get_text(c)
            if '已录入' in text:
                result[key] = 'enrolled'
                break
            if '未录入' in text:
                result[key] = 'not_enrolled'
                break

    # 锁屏密码: 人脸或指纹已录入 → 密码必已设置（知识库: 指纹/人脸需先设密码）
    if result['face'] == 'enrolled' or result['fingerprint'] == 'enrolled':
        result['lock_password'] = 'set'

    return result


# ── 来电铃声 ──

def _navigate_to_ringtone_page():
    """
    导航到来电铃声选择页: 设置 > 声音和振动 > 来电铃声
    返回: 页面 layout 或 None
    """
    layout = navigate_to_page('声音和振动', 3)
    if not layout:
        return None
    if not click_by_text(layout, '来电铃声', 2.5):
        for _ in range(3):
            swipe_up()
            layout = dump_layout()
            if click_by_text(layout, '来电铃声', 2.5):
                break
        else:
            return None
    return dump_layout()


def _get_checked_ringtone(layout):
    """获取当前选中铃声 Radio 的 (名称, 是否默认)"""
    radios = find_components(layout, lambda c: attr(c, 'type', '') == 'Radio')
    for radio in radios:
        if attr(radio, 'checked', '') == 'true':
            name = get_text(radio)
            return name, '(默认)' in name
    return None, False


def query_ringtone():
    """
    查询来电铃声是否为默认铃声 → dict | None

    返回:
        {'sim1': {'name': str, 'is_default': bool}, 'sim2': {...}}  (双卡)
        {'default': {'name': str, 'is_default': bool}}              (单卡/无卡)
    """
    layout = _navigate_to_ringtone_page()
    if not layout:
        return None

    has_dual_sim = bool(find_by_text(layout, '卡 1')) and bool(find_by_text(layout, '卡 2'))

    if has_dual_sim:
        result = {}
        for tab_text, key in [('卡 1', 'sim1'), ('卡 2', 'sim2')]:
            click_by_text(layout, tab_text, 1.5)
            layout = dump_layout()
            name, is_default = _get_checked_ringtone(layout)
            result[key] = {'name': name, 'is_default': is_default}
        return result
    else:
        name, is_default = _get_checked_ringtone(layout)
        return {'default': {'name': name, 'is_default': is_default}}


def set_ringtone_default():
    """
    设置来电铃声为默认铃声
    返回: (success: bool, results: dict)
    """
    layout = _navigate_to_ringtone_page()
    if not layout:
        return False, None

    has_dual_sim = bool(find_by_text(layout, '卡 1')) and bool(find_by_text(layout, '卡 2'))
    tabs = [('卡 1', 'sim1'), ('卡 2', 'sim2')] if has_dual_sim else [(None, 'default')]

    all_success = True
    results = {}

    for tab_text, key in tabs:
        if tab_text:
            click_by_text(layout, tab_text, 1.5)
            layout = dump_layout()

        # 检查当前是否已是默认
        name, is_default = _get_checked_ringtone(layout)
        if is_default:
            results[key] = {'name': name, 'is_default': True}
            continue

        # 查找含"(默认)"的 Radio 并点击
        radios = find_components(layout, lambda c: attr(c, 'type', '') == 'Radio')
        clicked = False
        for radio in radios:
            if '(默认)' in get_text(radio):
                center = parse_bounds(attr(radio, 'bounds'))
                if center:
                    click_at(center[0], center[1], 2.0)
                    clicked = True
                    break

        if clicked:
            layout = dump_layout()
            name, is_default = _get_checked_ringtone(layout)
            results[key] = {'name': name, 'is_default': is_default}
            if not is_default:
                all_success = False
        else:
            results[key] = {'name': None, 'is_default': False}
            all_success = False

    return all_success, results


# ── 热点配置（名称、密码、加密方式）──

def _navigate_to_hotspot_page():
    """
    导航到个人热点子页面: 设置 > 移动网络 > 个人热点
    返回: 页面 layout 或 None
    """
    layout = navigate_to_page('移动网络', 1)
    if not layout:
        return None
    if not click_by_text(layout, '个人热点', 2.5):
        for _ in range(3):
            swipe_up()
            layout = dump_layout()
            if click_by_text(layout, '个人热点', 2.5):
                break
        else:
            return None
    return dump_layout()


def query_hotspot_config():
    """
    查询热点配置 → dict | None
    {
        'name': str,              # 热点名称
        'password': str,          # 密码
        'encryption': str,        # 加密方式（HarmonyOS 固定 WPA2-PSK）
    }
    """
    layout = _navigate_to_hotspot_page()
    if not layout:
        return None

    result = {}
    result['name'] = read_text_value_raw(layout, '设备名称')
    result['password'] = read_text_value_raw(layout, '密码')
    result['encryption'] = 'WPA2-PSK (固定，不可配置)'
    return result


def set_hotspot_name(name):
    """
    设置热点名称 → (success: bool, new_name: str)
    """
    layout = _navigate_to_hotspot_page()
    if not layout:
        return False, None
    if not click_by_text(layout, '设备名称', 2.5):
        return False, None
    layout = dump_layout()
    inputs = find_components(layout, lambda c: attr(c, 'type', '') == 'TextInput')
    if not inputs:
        return False, None
    fb = parse_full_bounds(attr(inputs[0], 'bounds', ''))
    if not fb:
        return False, None
    cx = (fb[0] + fb[2]) // 2
    cy = (fb[1] + fb[3]) // 2
    input_text(cx, cy, name)
    # 点击"确定"
    layout = dump_layout()
    click_by_text(layout, '确定', 2.0)
    # 验证
    layout = dump_layout()
    new_name = read_text_value_raw(layout, '设备名称')
    return (new_name == name), new_name


def set_hotspot_password(password):
    """
    设置热点密码 → (success: bool, new_password: str)
    """
    layout = _navigate_to_hotspot_page()
    if not layout:
        return False, None
    if not click_by_text(layout, '密码', 2.5):
        return False, None
    layout = dump_layout()
    inputs = find_components(layout, lambda c: attr(c, 'type', '') == 'TextInput')
    if not inputs:
        return False, None
    fb = parse_full_bounds(attr(inputs[0], 'bounds', ''))
    if not fb:
        return False, None
    cx = (fb[0] + fb[2]) // 2
    cy = (fb[1] + fb[3]) // 2
    input_text(cx, cy, password)
    # 点击"确定"
    layout = dump_layout()
    click_by_text(layout, '确定', 2.0)
    # 验证
    layout = dump_layout()
    new_pwd = read_text_value_raw(layout, '密码')
    return (new_pwd == password), new_pwd


# ── 自动调节亮度 ──

def query_auto_brightness():
    """查询自动调节亮度状态 → 'on' | 'off' | 'unknown'"""
    return query_setting('显示和亮度', '自动调节', 'toggle_row', scroll=2)


def set_auto_brightness(desired):
    """设置自动调节亮度 → (success, new_status)"""
    return toggle_setting('显示和亮度', '自动调节', 'toggle_row', desired, scroll=2)


# ── 电子书模式 ──

def query_ebook_mode():
    """查询电子书模式状态 → 'on' | 'off' | 'unknown'"""
    return query_setting('显示和亮度', '电子书模式', 'text_value', scroll=2)


# ── 系统导航模式 ──

def query_navigation_mode():
    """
    查询系统导航模式 → '手势导航' | '三键导航' | 'unknown' | None(未找到)

    系统 > 系统导航子页面, 通过"三键导航"Toggle 判断:
      三键导航 off → 手势导航
      三键导航 on  → 三键导航
    """
    layout = navigate_to_page('系统', 4)
    if not layout:
        return None
    # 进入系统导航子页面
    if not click_by_text(layout, '系统导航', 2.5):
        return None
    layout = dump_layout()
    status = read_status_toggle_row(layout, '三键导航')
    if status == 'on':
        return '三键导航'
    if status == 'off':
        return '手势导航'
    return 'unknown'
