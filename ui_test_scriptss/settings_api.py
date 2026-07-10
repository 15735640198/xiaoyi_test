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

# ── 当前设置页面标题 ──

def query_current_settings_page():
    """
    查询当前设置页面的标题 → str | None

    如果当前不在设置App中，返回 None。
    否则返回页面标题文本（如 '声音和振动'、'字体大小和界面缩放'）。
    """
    layout = dump_layout()
    if not layout:
        return None

    # 检查是否在设置App中
    settings_nodes = find_components(
        layout, lambda c: 'settings' in attr(c, 'bundleName', ''))
    if not settings_nodes:
        return None

    # 查找页面标题: 状态栏(y<117)以下、标题区域(y 130~250)的 Text 组件
    title_candidates = []
    for c in find_components(layout, lambda c: attr(c, 'type', '') == 'Text'):
        txt = attr(c, 'text', '') or attr(c, 'originalText', '')
        if not txt:
            continue
        b = parse_full_bounds(attr(c, 'bounds', ''))
        if b and 130 < b[1] < 250:
            title_candidates.append((b[1], txt))

    if title_candidates:
        title_candidates.sort(key=lambda x: x[0])
        return title_candidates[0][1]

    return None


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


# ── 颜色反转 ──

def query_color_inversion():
    """查询颜色反转状态 → 'on' | 'off' | 'unknown'"""
    return query_setting('关怀和无障碍', '颜色反转', 'text_value', scroll=4)


def set_color_inversion(desired):
    """设置颜色反转 → (success, new_status)"""
    return toggle_setting('关怀和无障碍', '颜色反转', 'text_value', desired,
                          scroll=4, third_level_toggle='颜色反转')


# ── NFC 与默认付款应用 ──

def query_nfc():
    """查询 NFC 开关状态 → 'on' | 'off' | 'unknown'"""
    return query_setting('多设备协同', 'NFC', 'text_value', scroll=1)


def set_nfc(desired):
    """开关 NFC → (success, new_status)"""
    return toggle_setting('多设备协同', 'NFC', 'text_value', desired,
                          scroll=1, third_level_toggle='NFC')


def _open_nfc_page():
    """导航到 NFC 子页面，返回 layout 或 None"""
    layout = navigate_to_page('多设备协同', 1)
    if not layout:
        return None
    if not click_by_text(layout, 'NFC', 2.5):
        for _ in range(3):
            swipe_up()
            layout = dump_layout()
            if click_by_text(layout, 'NFC', 2.5):
                break
        else:
            return None
    time.sleep(1)
    return dump_layout()


def query_default_payment_app():
    """
    查询默认付款应用 → 应用名称文本 | None
    需进入 多设备协同 > NFC 子页面读取。
    """
    layout = _open_nfc_page()
    if not layout:
        return None
    return read_text_value_raw(layout, '默认付款应用')


def set_default_payment_app(app_name):
    """
    设置默认付款应用
    app_name: 付款应用名称关键词 (如 '华为钱包' 或 '钱包')
    → (success, message)
    """
    layout = _open_nfc_page()
    if not layout:
        return False, '未找到 NFC 入口'

    # 点击"默认付款应用"行
    if not click_by_text(layout, '默认付款应用', 2.0):
        return False, '未找到默认付款应用入口'
    time.sleep(2)
    layout = dump_layout()

    # 在列表中查找目标应用
    for i in range(5):
        matches = find_components(layout, lambda c: app_name in (
            attr(c, 'text', '') + attr(c, 'originalText', '')))
        if matches:
            target = matches[0]
            center = parse_bounds(attr(target, 'bounds'))
            if center:
                click_at(center[0], center[1], 2.0)
                time.sleep(1)
                # 返回到 NFC 子页面
                hdc_shell('uitest', 'uiInput', 'keyEvent', 'Back')
                time.sleep(1)
                layout = dump_layout()
                current = read_text_value_raw(layout, '默认付款应用')
                return True, f'默认付款应用已设置为: {current}'
        swipe_up(1.0)
        layout = dump_layout()

    return False, f'未找到匹配的付款应用: {app_name}'


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


def connect_wlan(ssid, password=None):
    """
    连接指定 WiFi 网络 → (success, message)

    Args:
        ssid: WiFi 名称
        password: WiFi 密码 (开放网络可不传)

    Returns:
        (True, '已连接') 成功
        (False, 原因) 失败
    """
    layout = navigate_to_page('WLAN', 4)
    if not layout:
        return False, '未找到WLAN入口'

    # 确保 WLAN 已开启
    wlan_status = read_status_toggle_row(layout, 'WLAN')
    if wlan_status == 'off':
        toggle_operation(layout, 'WLAN', 'toggle_row', 'on')
        time.sleep(3)
        layout = dump_layout()
    elif wlan_status != 'on':
        return False, f'WLAN开关状态异常: {wlan_status}'

    # 滑动查找目标 WiFi
    found_layout = None
    for i in range(5):
        if find_by_text_nearest(layout, ssid):
            found_layout = layout
            break
        swipe_up()
        layout = dump_layout()

    if not found_layout:
        return False, f'未找到WiFi: {ssid}'

    # 点击 WiFi
    click_by_text(layout, ssid, 3.0)
    layout = dump_layout()

    # 检查是否已连接 (详情页有"断开连接")
    if find_by_text(layout, '断开连接'):
        return True, '已连接(无需重复连接)'

    # 查找密码输入框
    ti = None
    for c in find_components(layout, lambda c: attr(c, 'type') == 'TextInput'):
        ti = c
        break

    if ti:
        if not password:
            return False, '需要密码但未提供'
        center = parse_bounds(attr(ti, 'bounds'))
        if not center:
            return False, '无法定位密码输入框'
        click_at(center[0], center[1], 0.5)
        hdc_shell('uitest', 'uiInput', 'text', password)
        time.sleep(1)
        # 点击"连接"
        layout = dump_layout()
        click_by_text(layout, '连接', 5.0)
    else:
        # 无密码输入框 = 已保存/开放网络, 点击后自动连接
        # 直接等待验证, 不需要额外操作
        pass

    # 等待连接结果
    time.sleep(5)
    layout = dump_layout()

    # 验证: 检查 WiFi 名称旁是否有"已连接"
    comps = find_by_text_nearest(layout, ssid)
    if not comps:
        return False, '连接后未找到WiFi'
    all_texts = find_components(layout, lambda c: attr(c, 'type') == 'Text')
    for comp in comps:
        center = parse_bounds(attr(comp, 'bounds'))
        if not center:
            continue
        for t in all_texts:
            tc = parse_bounds(attr(t, 'bounds'))
            if tc and abs(tc[1] - center[1]) < 100 and tc[0] > center[0] - 50:
                val = get_text(t)
                if '已连接' in val:
                    return True, '已连接'
    return False, '连接超时或密码错误'


# ── 星闪 ──

def query_nearlink():
    """查询星闪开关状态 → 'on' | 'off' | 'unknown'"""
    return query_setting('星闪和蓝牙', '星闪', 'toggle_row', scroll=2)


def set_nearlink(desired):
    """开关星闪 → (success, new_status)"""
    return toggle_setting('星闪和蓝牙', '星闪', 'toggle_row', desired, scroll=2)


# ── 蓝牙 ──

def query_bluetooth():
    """查询蓝牙开关状态 → 'on' | 'off' | 'unknown'"""
    return query_setting('星闪和蓝牙', '蓝牙', 'toggle_row', scroll=2)


def set_bluetooth(desired):
    """开关蓝牙 → (success, new_status)"""
    return toggle_setting('星闪和蓝牙', '蓝牙', 'toggle_row', desired, scroll=2)


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


# ── 屏幕亮度 ──

def query_brightness():
    """
    查询屏幕亮度百分比 → int (如 100) | None
    通过 UI slider 的 text 属性读取（0-255 标度），换算为百分比。
    """
    layout = navigate_to_page('显示和亮度', 2)
    if not layout:
        return None
    for i in range(2):
        for sl in find_sliders(layout):
            val = attr(sl, 'text', '') or attr(sl, 'originalText', '')
            if val:
                try:
                    return round(float(val) / 255 * 100)
                except ValueError:
                    pass
        swipe_up()
        layout = dump_layout()
    return None


# ── 字体大小和字体粗细 ──

def _open_font_size_page():
    """导航到字体大小和界面缩放页面"""
    layout = navigate_to_page('显示和亮度', 2)
    if not layout:
        return None
    if not click_by_text(layout, '字体大小和界面缩放'):
        for _ in range(3):
            swipe_up()
            layout = dump_layout()
            if click_by_text(layout, '字体大小和界面缩放'):
                break
        else:
            return None
    time.sleep(2)
    return dump_layout()


def query_font_size():
    """
    查询字体大小 → '小' | '标准' | '大' | '超大' | None
    """
    layout = _open_font_size_page()
    if not layout:
        return None
    return read_text_value_raw(layout, '字体大小')


def set_font_size(desired):
    """
    设置字体大小
    desired: '小' | '标准' | '大' | '超大'
    → (success, new_value)
    """
    layout = _open_font_size_page()
    if not layout:
        return False, None

    size_map = {'小': 0, '标准': 25, '大': 50, '超大': 75}
    if desired not in size_map:
        return False, None

    if not set_slider(layout, '字体大小', size_map[desired]):
        return False, None

    time.sleep(1)

    # 超大时弹出"设置更大字体"弹窗，点取消
    layout = dump_layout()
    if find_by_text(layout, '设置更大字体'):
        click_by_text(layout, '取消', 1.0)
        layout = dump_layout()

    new_val = read_text_value_raw(layout, '字体大小')
    return (new_val == desired), new_val


def query_font_weight():
    """
    查询字体粗细 → '最细' | '标准' | '最粗' | None
    """
    layout = _open_font_size_page()
    if not layout:
        return None
    return read_text_value_raw(layout, '字体粗细')


def set_font_weight(desired):
    """
    设置字体粗细（用 swipe 拖动 slider）
    desired: '最细' | '标准' | '最粗'
    → (success, new_value)
    """
    layout = _open_font_size_page()
    if not layout:
        return False, None

    # 找字体粗细 label 下方的 slider
    comps = find_by_text_nearest(layout, '字体粗细')
    if not comps:
        return False, None
    label_center = parse_bounds(attr(comps[0], 'bounds'))
    if not label_center:
        return False, None

    target_slider = None
    for sl in find_sliders(layout):
        sc = parse_bounds(attr(sl, 'bounds'))
        if sc and sc[1] > label_center[1] and abs(sc[1] - label_center[1]) < 200:
            target_slider = sl
            break
    if not target_slider:
        return False, None

    fb = parse_full_bounds(attr(target_slider, 'bounds', ''))
    if not fb:
        return False, None

    track_w = fb[2] - fb[0]
    cy = (fb[1] + fb[3]) // 2
    # 档位: 最细=最左, 标准=中间, 最粗=最右
    pct_map = {'最细': 0, '标准': 50, '最粗': 100}
    if desired not in pct_map:
        return False, None

    target_x = int(fb[0] + track_w * pct_map[desired] / 100)
    center_x = (fb[0] + fb[2]) // 2
    # 从 slider 中心 swipe 到目标位置
    hdc_shell('uitest', 'uiInput', 'swipe',
              str(center_x), str(cy), str(target_x), str(cy))
    time.sleep(2)

    layout = dump_layout()
    new_val = read_text_value_raw(layout, '字体粗细')
    return (new_val == desired), new_val


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


# ── 响铃时振动 ──

def query_ring_vibration():
    """查询响铃时振动状态 → 'on' | 'off' | 'unknown'"""
    return query_setting('声音和振动', '响铃时振动', 'toggle_row', scroll=3)


def set_ring_vibration(desired):
    """设置响铃时振动 → (success, new_status)"""
    return toggle_setting('声音和振动', '响铃时振动', 'toggle_row', desired, scroll=3)


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


# ── 铃声（来电、信息、通知）──

def _navigate_to_ringtone_selection(item_text='来电铃声'):
    """
    导航到铃声选择页: 设置 > 声音和振动 > {item_text}
    item_text: '来电铃声' | '信息铃声' | '通知铃声'
    返回: 页面 layout 或 None
    """
    layout = navigate_to_page('声音和振动', 3)
    if not layout:
        return None
    if not click_by_text(layout, item_text, 2.5):
        for _ in range(3):
            swipe_up()
            layout = dump_layout()
            if click_by_text(layout, item_text, 2.5):
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
    layout = _navigate_to_ringtone_selection('来电铃声')
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
    layout = _navigate_to_ringtone_selection('来电铃声')
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


def query_message_ringtone():
    """
    查询信息铃声是否为默认铃声 → dict | None

    返回:
        {'name': str, 'is_default': bool}
    """
    layout = _navigate_to_ringtone_selection('信息铃声')
    if not layout:
        return None
    name, is_default = _get_checked_ringtone(layout)
    return {'name': name, 'is_default': is_default}


def query_notification_ringtone():
    """
    查询通知铃声是否为默认铃声 → dict | None

    返回:
        {'name': str, 'is_default': bool}
    """
    layout = _navigate_to_ringtone_selection('通知铃声')
    if not layout:
        return None
    name, is_default = _get_checked_ringtone(layout)
    return {'name': name, 'is_default': is_default}


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


# ── 默认数据卡 ──

def query_default_data_card():
    """
    查询默认移动数据卡 → '卡 1' | '卡 2' | 'unknown' | None(未找到)

    移动网络 > SIM 卡管理, "默认移动数据"行有两个 Button(卡1/卡2),
    Button 的 selected 属性标识当前选择。
    """
    layout = navigate_to_page('移动网络', 1)
    if not layout:
        return None
    if not click_by_text(layout, 'SIM 卡管理', 2.5):
        return None
    layout = dump_layout()

    # 找"默认移动数据"文本
    comps = find_by_text_nearest(layout, '默认移动数据')
    if not comps:
        return None

    buttons = find_buttons(layout)
    all_texts = find_components(layout, lambda c: attr(c, 'type') == 'Text')

    for comp in comps:
        center = parse_bounds(attr(comp, 'bounds'))
        if not center:
            continue
        # 找同一行右侧 selected=true 的 Button
        for btn in buttons:
            bc = parse_bounds(attr(btn, 'bounds'))
            if bc and abs(bc[1] - center[1]) < 80 and bc[0] > center[0]:
                if attr(btn, 'selected') == 'true':
                    # 找 Button 内的 Text
                    fb = parse_full_bounds(attr(btn, 'bounds'))
                    if not fb:
                        return 'unknown'
                    for t in all_texts:
                        tb = parse_full_bounds(attr(t, 'bounds'))
                        if (tb and fb[0] <= tb[0] and tb[2] <= fb[2]
                                and fb[1] <= tb[1] and tb[3] <= fb[3]):
                            return get_text(t).strip()
                    return 'unknown'
    return 'unknown'


# ── WLAN 下自动下载 ──

def query_wlan_auto_download():
    """
    查询 WLAN 下自动下载状态 → 'on' | 'off' | 'unknown' | None(未找到)

    通过设置搜索框搜索"WLAN下自动下载"跳转到 更新选项 页面。
    实际路径: 关于本机 > 软件更新 > 更新选项, 但搜索直达更高效。
    """
    layout = search_setting('WLAN下自动下载', 'WLAN 下自动下载')
    if not layout:
        return None
    return read_status_toggle_row(layout, 'WLAN 下自动下载')


def set_wlan_auto_download(desired):
    """
    设置 WLAN 下自动下载 → (success, new_status)

    desired: 'on' 或 'off'
    """
    layout = search_setting('WLAN下自动下载', 'WLAN 下自动下载')
    if not layout:
        return False, None
    status = read_status_toggle_row(layout, 'WLAN 下自动下载')
    if status is None:
        return False, None
    if status == desired:
        return True, status
    success = toggle_operation(layout, 'WLAN 下自动下载', 'toggle_row', desired)
    if not success:
        return False, status
    time.sleep(1)
    layout = dump_layout()
    # 关闭时弹出确认对话框，点击"关闭"确认
    if click_by_text(layout, '关闭', 2.0):
        time.sleep(1)
        layout = dump_layout()
    new_status = read_status_toggle_row(layout, 'WLAN 下自动下载')
    return (new_status == desired), new_status


# ── SIM 卡管理 ──

def _navigate_to_sim_management():
    """导航到 SIM 卡管理子页面，返回 layout"""
    layout = navigate_to_page('移动网络', 1)
    if not layout:
        return None
    if not click_by_text(layout, 'SIM 卡管理', 2.5):
        return None
    return dump_layout()


def query_sim_status():
    """
    查询双卡状态 → dict {'卡 1': '未插卡'|运营商名, '卡 2': ...}

    移动网络 > SIM 卡管理, 卡槽旁的文本标识插卡状态。
    """
    layout = _navigate_to_sim_management()
    if not layout:
        return None
    result = {}
    all_texts = find_components(layout, lambda c: attr(c, 'type') == 'Text')
    for card in ['卡 1', '卡 2']:
        comps = find_by_text_nearest(layout, card)
        if not comps:
            result[card] = 'unknown'
            continue
        found = False
        for comp in comps:
            center = parse_bounds(attr(comp, 'bounds'))
            if not center or center[1] > 800:
                continue  # 跳过"默认移动数据"区域的同名文本
            for t in all_texts:
                tc = parse_bounds(attr(t, 'bounds'))
                if (tc and abs(tc[1] - center[1]) < 60
                        and tc[0] > center[0] + 50):
                    result[card] = get_text(t).strip()
                    found = True
                    break
            if found:
                break
        if not found:
            result[card] = 'unknown'
    return result


def query_sim_carrier():
    """
    查询 SIM 运营商归属 → dict {'卡 1': 运营商名|None, '卡 2': ...}

    未插卡时返回 None。
    """
    status = query_sim_status()
    if not status:
        return None
    result = {}
    for card, val in status.items():
        if val in ('未插卡', 'unknown'):
            result[card] = None
        else:
            result[card] = val
    return result


def query_sim_enabled(card='卡 1'):
    """
    查询指定 SIM 卡使用状态 → 'on' | 'off' | 'unknown' | None

    card: '卡 1' 或 '卡 2'
    SIM 卡管理页面, 卡槽旁有 Toggle 控制启用/禁用。
    """
    layout = _navigate_to_sim_management()
    if not layout:
        return None
    return read_status_toggle_row(layout, card)


def set_sim_enabled(card, desired):
    """
    设置指定 SIM 卡使用状态 → (success, new_status)

    card: '卡 1' 或 '卡 2'
    desired: 'on' 或 'off'
    """
    layout = _navigate_to_sim_management()
    if not layout:
        return False, None
    status = read_status_toggle_row(layout, card)
    if status is None:
        return False, None
    if status == desired:
        return True, status
    success = toggle_operation(layout, card, 'toggle_row', desired)
    if not success:
        return False, status
    time.sleep(1)
    layout = dump_layout()
    new_status = read_status_toggle_row(layout, card)
    return (new_status == desired), new_status


# ── 网络加速 ──

def query_network_acceleration():
    """
    查询"允许使用移动数据加速网络"状态 → 'on' | 'off' | 'unknown'

    移动网络 > 网络加速, toggle_row 形态。
    """
    layout = navigate_to_page('移动网络', 1)
    if not layout:
        return None
    for i in range(4):
        if find_by_text(layout, '网络加速'):
            break
        swipe_up()
        layout = dump_layout()
    if not click_by_text(layout, '网络加速', 2.5):
        return None
    layout = dump_layout()
    return read_status_toggle_row(layout, '允许使用移动数据加速网络')


def set_network_acceleration(desired):
    """
    设置"允许使用移动数据加速网络" → (success, new_status)
    """
    layout = navigate_to_page('移动网络', 1)
    if not layout:
        return False, None
    for i in range(4):
        if find_by_text(layout, '网络加速'):
            break
        swipe_up()
        layout = dump_layout()
    if not click_by_text(layout, '网络加速', 2.5):
        return False, None
    layout = dump_layout()
    status = read_status_toggle_row(layout, '允许使用移动数据加速网络')
    if status is None:
        return False, None
    if status == desired:
        return True, status
    success = toggle_operation(layout, '允许使用移动数据加速网络',
                               'toggle_row', desired)
    if not success:
        return False, status
    time.sleep(1)
    layout = dump_layout()
    new_status = read_status_toggle_row(layout, '允许使用移动数据加速网络')
    return (new_status == desired), new_status


# ── 系统语言 ──

def query_system_language():
    """
    查询当前系统语言 → 语言名称 (如 '简体中文') | None

    系统 > 语言和地区, 语言名在"语言"标题下方 (非右侧, 右侧是"编辑"按钮)。
    """
    layout = navigate_to_page('系统', 4)
    if not layout:
        return None
    if not click_by_text(layout, '语言和地区', 2.5):
        return None
    layout = dump_layout()
    # 找"语言"文本, 然后在其下方找语言名
    comps = find_by_text_nearest(layout, '语言')
    if not comps:
        return None
    all_texts = find_components(layout, lambda c: attr(c, 'type') == 'Text')
    for comp in comps:
        center = parse_bounds(attr(comp, 'bounds'))
        if not center:
            continue
        # 在"语言"下方 (y > center_y + 50, y < center_y + 200) 找文本
        for t in all_texts:
            tc = parse_bounds(attr(t, 'bounds'))
            if (tc and tc[1] > center[1] + 30 and tc[1] < center[1] + 200
                    and abs(tc[0] - center[0]) < 300):
                val = get_text(t).strip()
                if val and val != '编辑' and val != '添加语言':
                    return val
    return None


def add_system_language(language):
    """
    添加系统语言 → (success, message)

    language: 语言中文名 (如 '英语', '繁体中文')
    流程: 语言和地区 → 添加语言 → 点击目标语言
    注意: 仅添加到语言列表, 不自动设为默认。设为默认需手动拖拽排序。
    """
    layout = navigate_to_page('系统', 4)
    if not layout:
        return False, '未找到系统入口'
    if not click_by_text(layout, '语言和地区', 2.5):
        return False, '未找到语言和地区'
    layout = dump_layout()
    if not click_by_text(layout, '添加语言', 2.5):
        return False, '未找到添加语言入口'
    layout = dump_layout()
    # 在语言列表中查找并点击目标语言
    if click_by_text(layout, language, 3.0):
        time.sleep(1)
        layout = dump_layout()
        # 可能有确认弹窗
        for btn in ['确定', '添加', '确认']:
            if click_by_text(layout, btn, 2.0):
                time.sleep(1)
                break
        return True, f'已添加语言: {language}'
    return False, f'未找到语言: {language}'


# ── 输入法 ──

def query_default_input_method():
    """
    查询默认输入法 → 输入法名称 (如 '小艺输入法') | None

    系统 > 输入法, "默认输入法"行右侧显示当前输入法。
    """
    layout = navigate_to_page('系统', 4)
    if not layout:
        return None
    if not click_by_text(layout, '输入法', 2.5):
        return None
    layout = dump_layout()
    return read_text_value_raw(layout, '默认输入法')


# ── 日期和时间（自动时区、系统时区）──

def _open_date_time_page():
    """导航到 日期和时间 设置页，返回 layout 或 None"""
    layout = navigate_to_page('系统', 4)
    if not layout:
        return None
    if not click_by_text(layout, '日期和时间', 2.5):
        return None
    time.sleep(1)
    return dump_layout()


def query_auto_timezone():
    """
    查询自动时区开关状态 → 'on' | 'off' | 'unknown' | None(未找到)

    系统 > 日期和时间, "自动设置"行右侧 Toggle 的 checked 属性。
    """
    layout = _open_date_time_page()
    if not layout:
        return None
    return read_status_toggle_row(layout, '自动设置')


def set_auto_timezone(desired):
    """
    设置自动时区开关 → (success, new_status)

    系统 > 日期和时间, "自动设置"行 Toggle。
    """
    layout = _open_date_time_page()
    if not layout:
        return False, '未找到日期和时间入口'
    status = read_status_toggle_row(layout, '自动设置')
    if status is None:
        return False, '未找到自动设置开关'
    if status == desired:
        return True, status
    # 点击 Toggle 切换
    toggles = find_toggles(layout)
    comps = find_by_text_nearest(layout, '自动设置')
    for comp in comps:
        center = parse_bounds(attr(comp, 'bounds'))
        if not center:
            continue
        for tg in toggles:
            tc = parse_bounds(attr(tg, 'bounds'))
            if tc and abs(tc[1] - center[1]) < 80:
                click_at(tc[0], tc[1], 2.0)
                layout = dump_layout()
                new_status = read_status_toggle_row(layout, '自动设置')
                return (new_status == desired), new_status
    return False, status


def query_timezone():
    """
    查询系统时区 → 时区文本 (如 'GMT+08:00 中国标准时间') | None

    系统 > 日期和时间, "时区"行右侧显示当前时区。
    """
    layout = _open_date_time_page()
    if not layout:
        return None
    return read_text_value_raw(layout, '时区')


def set_timezone(timezone_name):
    """
    设置系统时区 → (success, message)

    系统 > 日期和时间 > 时区选择列表。
    需先关闭自动时区（如开启），然后在列表中查找并点击目标时区。

    Args:
        timezone_name: 时区关键词，用于在列表中匹配
                       (如 '中国标准时间' 或 'GMT+08:00' 或 '北京')
    """
    layout = _open_date_time_page()
    if not layout:
        return False, '未找到日期和时间入口'

    # 如自动设置开启，先关闭
    auto_status = read_status_toggle_row(layout, '自动设置')
    if auto_status == 'on':
        toggles = find_toggles(layout)
        comps = find_by_text_nearest(layout, '自动设置')
        for comp in comps:
            center = parse_bounds(attr(comp, 'bounds'))
            if not center:
                continue
            for tg in toggles:
                tc = parse_bounds(attr(tg, 'bounds'))
                if tc and abs(tc[1] - center[1]) < 80:
                    click_at(tc[0], tc[1], 2.0)
                    break
            break
        time.sleep(1)
        layout = dump_layout()

    # 点击"时区"行进入选择列表
    if not click_by_text(layout, '时区', 3.0):
        return False, '未找到时区入口'
    time.sleep(2)

    # 在时区列表中查找目标
    layout = dump_layout()
    for i in range(10):
        # 查找匹配的时区项
        matches = find_components(layout, lambda c: timezone_name in (
            attr(c, 'text', '') + attr(c, 'originalText', '')))
        if matches:
            # 点击匹配项（Text 的 clickable=false，点击中心坐标即可）
            target = matches[0]
            center = parse_bounds(attr(target, 'bounds'))
            if center:
                click_at(center[0], center[1], 2.0)
                time.sleep(1)
                # 验证
                hdc_shell('uitest', 'uiInput', 'keyEvent', 'Back')
                time.sleep(1)
                layout = dump_layout()
                # 再次返回到日期和时间页
                hdc_shell('uitest', 'uiInput', 'keyEvent', 'Back')
                time.sleep(1)
                layout = dump_layout()
                current = read_text_value_raw(layout, '时区')
                if current and timezone_name in current:
                    return True, f'时区已设置为: {current}'
                return True, f'已选择时区 (当前: {current})'
        swipe_up(1.0)
        layout = dump_layout()

    return False, f'未找到匹配的时区: {timezone_name}'


# ── 时间制式、日期、时间 ──

def query_time_format():
    """
    查询时间制式 → '24小时' | '12小时' | 'unknown' | None
    """
    layout = _open_date_time_page()
    if not layout:
        return None
    status = read_status_toggle_row(layout, '24 小时制')
    if status == 'on':
        return '24小时'
    elif status == 'off':
        return '12小时'
    return status


def set_time_format(desired):
    """
    设置时间制式
    desired: '24小时' | '12小时' (也接受 '24' / '12')
    → (success, new_format)
    """
    if desired in ('24', '24小时', '24h'):
        target = 'on'
    elif desired in ('12', '12小时', '12h'):
        target = 'off'
    else:
        return False, None

    layout = _open_date_time_page()
    if not layout:
        return False, None
    status = read_status_toggle_row(layout, '24 小时制')
    if status is None:
        return False, None
    if status == target:
        return True, '24小时' if target == 'on' else '12小时'

    toggles = find_toggles(layout)
    comps = find_by_text_nearest(layout, '24 小时制')
    for comp in comps:
        center = parse_bounds(attr(comp, 'bounds'))
        if not center:
            continue
        for tg in toggles:
            tc = parse_bounds(attr(tg, 'bounds'))
            if tc and abs(tc[1] - center[1]) < 80:
                click_at(tc[0], tc[1], 2.0)
                layout = dump_layout()
                new_status = read_status_toggle_row(layout, '24 小时制')
                new_fmt = '24小时' if new_status == 'on' else '12小时'
                return (new_status == target), new_fmt
    return False, status


def query_date():
    """
    查询系统日期 → 如 '2026年7月6日' | None
    需自动设置关闭才显示日期行。
    """
    layout = _open_date_time_page()
    if not layout:
        return None
    return read_text_value_raw(layout, '日期')


def query_time():
    """
    查询系统时间 → 如 '15:47' | None
    需自动设置关闭才显示时间行。
    """
    layout = _open_date_time_page()
    if not layout:
        return None
    return read_text_value_raw(layout, '时间')


def set_time(hour, minute):
    """
    设置系统时间
    hour: 0-23, minute: 0-59
    需先关闭自动设置（如开启）。
    → (success, message)
    """
    layout = _open_date_time_page()
    if not layout:
        return False, '未找到日期和时间入口'

    # 关闭自动设置
    auto = read_status_toggle_row(layout, '自动设置')
    if auto == 'on':
        set_auto_timezone('off')
        time.sleep(1)
        layout = dump_layout()

    # 点击"时间"行打开选择器
    if not click_by_text(layout, '时间', 2.0):
        return False, '未找到时间入口'
    time.sleep(2)
    layout = dump_layout()

    # 找 TimePicker 中的 Column (小时列和分钟列)
    columns = find_components(layout, lambda c: attr(c, 'type', '') == 'Column')
    hour_col = None
    min_col = None
    for col in columns:
        txt = attr(col, 'text', '') or attr(col, 'originalText', '')
        b = parse_full_bounds(attr(col, 'bounds', ''))
        if not b or not txt:
            continue
        try:
            val = int(txt)
        except ValueError:
            continue
        cx = (b[0] + b[2]) // 2
        if cx < 660 and val < 24:
            hour_col = (b, val)
        elif cx >= 660 and val < 60:
            min_col = (b, val)

    if not hour_col or not min_col:
        # 点击取消关闭选择器
        click_by_text(layout, '取消', 0.5)
        return False, '无法读取时间选择器'

    cur_h = hour_col[1]
    cur_m = min_col[1]
    h_bounds = hour_col[0]
    m_bounds = min_col[0]

    def read_picker_val(bounds):
        """重新 dump 并读取指定列的当前值"""
        layout2 = dump_layout()
        for col in find_components(layout2, lambda c: attr(c, 'type', '') == 'Column'):
            txt = attr(col, 'text', '') or attr(col, 'originalText', '')
            b = parse_full_bounds(attr(col, 'bounds', ''))
            if not b or not txt:
                continue
            try:
                val = int(txt)
            except ValueError:
                continue
            # 按 X 坐标匹配列
            cx = (b[0] + b[2]) // 2
            bx = (bounds[0] + bounds[2]) // 2
            if abs(cx - bx) < 100:
                return val
        return None

    def swipe_column_to_target(bounds, target_val, max_val):
        """逐步点击相邻项直到到达目标值"""
        cx = (bounds[0] + bounds[2]) // 2
        cy = (bounds[1] + bounds[3]) // 2
        for _ in range(max_val + 1):
            cur = read_picker_val(bounds)
            if cur is None or cur == target_val:
                return
            diff = target_val - cur
            if diff > max_val // 2:
                diff -= max_val
            elif diff < -max_val // 2:
                diff += max_val
            if diff == 0:
                return
            # 点击相邻项位置: 增大点下方, 减小点上方
            if diff > 0:
                click_at(cx, cy + 138, 0.3)
            else:
                click_at(cx, cy - 138, 0.3)

    swipe_column_to_target(h_bounds, hour, 24)
    swipe_column_to_target(m_bounds, minute, 60)

    # 点击"确定"
    layout = dump_layout()
    if click_by_text(layout, '确定', 1.0):
        time.sleep(1)
        layout = dump_layout()
        new_time = read_text_value_raw(layout, '时间')
        return True, f'时间已设置为: {new_time}'

    return False, '无法确认设置'


# ── 存储空间 ──

def _open_storage_page():
    """导航到存储设置页，返回 layout 或 None"""
    restart_settings()
    layout = dump_layout()
    for i in range(8):
        comps = find_components(layout, lambda c: attr(c, 'text') == '存储')
        if comps:
            b = parse_bounds(attr(comps[0], 'bounds'))
            if b and b[1] < 1800:
                break
        swipe_up()
        layout = dump_layout()
    if not click_by_text(layout, '存储', 3.0):
        return None
    time.sleep(3)  # 等待存储计算完成
    return dump_layout()


def query_storage():
    """
    查询存储空间使用情况 → dict | None

    返回:
      {
        'usage_rate': '16%',           # 使用率
        'used': '83.02 GB',           # 已使用
        'total': '512 GB',            # 总大小
        'apps': [                     # 应用占用列表 (前N个)
          {'name': '卓易通', 'size': '3.43 GB'},
          ...
        ]
      }
    """
    layout = _open_storage_page()
    if not layout:
        return None

    result = {'usage_rate': None, 'used': None, 'total': None, 'apps': []}

    # 查找使用率百分比文本 (如 "16%")
    for c in find_components(layout, lambda c: True):
        txt = attr(c, 'text', '').strip()
        if txt and txt.endswith('%') and len(txt) <= 6:
            # 排除电池百分比 (id 含 battery)
            cid = attr(c, 'id', '')
            if 'battery' not in cid.lower() and 'Battery' not in cid:
                result['usage_rate'] = txt
                break

    # 查找"已使用 X GB/Y GB"文本
    for c in find_components(layout, lambda c: '已使用' in attr(c, 'text', '')):
        txt = attr(c, 'text', '').strip()
        # 解析 "已使用 83.02 GB/512 GB"
        m = re.match(r'已使用\s*(.+?)/\s*(.+)', txt)
        if m:
            result['used'] = m.group(1).strip()
            result['total'] = m.group(2).strip()
            break

    # 查找应用占用列表 (id 含 AppGroup 且含 .title)
    app_titles = find_components(
        layout, lambda c: 'AppGroup' in attr(c, 'id', '') and '.title' in attr(c, 'id', ''))
    app_sizes = find_components(
        layout, lambda c: 'AppGroup' in attr(c, 'id', '') and '.result' in attr(c, 'id', ''))

    for title in app_titles:
        tid = attr(title, 'id', '')
        # 从 title id 提取包名: Setting.Storage.AppGroup.<package>,0.title
        m = re.match(r'Setting\.Storage\.AppGroup\.(.+?),0\.title', tid)
        if not m:
            continue
        pkg = m.group(1)
        app_name = attr(title, 'text', '').strip()
        # 找对应的 size (同包名)
        for sz in app_sizes:
            if pkg in attr(sz, 'id', ''):
                result['apps'].append({
                    'name': app_name,
                    'size': attr(sz, 'text', '').strip()
                })
                break

    return result


# ── USB 调试 ──

def _open_developer_options():
    """导航到开发者选项页面，返回 layout 或 None"""
    restart_settings()
    layout = dump_layout()
    # 滑动查找"系统"入口
    for i in range(8):
        comps = find_components(layout, lambda c: attr(c, 'text') == '系统')
        if comps:
            b = parse_bounds(attr(comps[0], 'bounds'))
            if b and b[1] < 1800:
                break
        swipe_up()
        layout = dump_layout()
    if not click_by_text(layout, '系统', 3.0):
        return None
    # 滑动查找"开发者选项"
    layout = dump_layout()
    for i in range(6):
        if click_by_text(layout, '开发者选项', 3.0):
            time.sleep(2)
            return dump_layout()
        swipe_up()
        layout = dump_layout()
    return None


def query_usb_debug():
    """
    查询USB调试开关状态 → 'on' | 'off' | 'unknown' | None(未找到)

    系统 > 开发者选项, "USB 调试"行 Toggle (id=entry_toggle_usb_debug)。
    """
    layout = _open_developer_options()
    if not layout:
        return None
    # 通过 id 直接查找 Toggle
    for c in find_components(layout, lambda c: attr(c, 'id') == 'entry_toggle_usb_debug'):
        return read_toggle_state(c)
    # 滑动查找
    for i in range(4):
        swipe_up()
        layout = dump_layout()
        for c in find_components(layout, lambda c: attr(c, 'id') == 'entry_toggle_usb_debug'):
            return read_toggle_state(c)
    return None


def set_usb_debug(desired):
    """
    设置USB调试开关 → (success, new_status)

    系统 > 开发者选项, "USB 调试"行 Toggle。
    开启时可能弹出确认对话框，需点击"允许"确认。
    """
    layout = _open_developer_options()
    if not layout:
        return False, '未找到开发者选项入口'

    def find_usb_toggle(lay):
        for c in find_components(lay, lambda c: attr(c, 'id') == 'entry_toggle_usb_debug'):
            return c
        return None

    tg = find_usb_toggle(layout)
    if not tg:
        # 滑动查找
        for i in range(4):
            swipe_up()
            layout = dump_layout()
            tg = find_usb_toggle(layout)
            if tg:
                break
    if not tg:
        return False, '未找到USB调试开关'

    current = read_toggle_state(tg)
    if current == desired:
        return True, current

    # 点击 Toggle 切换
    center = parse_bounds(attr(tg, 'bounds'))
    if center:
        click_at(center[0], center[1], 2.0)
    else:
        return False, current

    # 检查是否有确认对话框（开启时可能弹出）
    layout = dump_layout()
    for btn_text in ['允许', '确定', '确认']:
        if click_by_text(layout, btn_text, 2.0):
            time.sleep(1)
            break

    layout = dump_layout()
    new_status = None
    tg2 = find_usb_toggle(layout)
    if tg2:
        new_status = read_toggle_state(tg2)
    return (new_status == desired), new_status


# ── 开发者模式（开启/关闭）──

def _open_about_device():
    """通过搜索导航到关于本机页面，返回 layout 或 None"""
    restart_settings()
    layout = dump_layout()
    # 点击搜索框
    for c in find_components(layout, lambda c: attr(c, 'type') in ('Search', 'SearchField')):
        center = parse_bounds(attr(c, 'bounds'))
        if center:
            click_at(center[0], center[1], 2.0)
            break
    layout = dump_layout()
    # 点击 TextInput 激活
    for c in find_components(layout, lambda c: attr(c, 'type') == 'TextInput'):
        center = parse_bounds(attr(c, 'bounds'))
        if center:
            click_at(center[0], center[1], 0.5)
            break
    # 输入搜索文本
    hdc_shell('uitest', 'uiInput', 'text', '关于本机')
    time.sleep(3)
    # 点击搜索结果 (通过 id 定位 searchResultItem)
    layout = dump_layout()
    results = find_components(layout, lambda c: attr(c, 'id') == 'searchResultItem')
    if results:
        center = parse_bounds(attr(results[0], 'bounds'))
        if center:
            # 找包含此中心的最小可点击组件
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
            click_at(target[0], target[1], 3.0)
            return dump_layout()
    return None


def set_developer_mode(desired):
    """
    设置开发者模式 → (success, new_status)

    开启: 关于本机 > 连续点击"HarmonyOS 版本"7 次
    关闭: 开发者选项 > 关闭顶部 Toggle > 确认弹窗
    """
    current = query_developer_mode()
    if current == desired:
        return True, current

    if desired == 'on':
        # 导航到关于本机
        layout = _open_about_device()
        if not layout:
            return False, '未找到关于本机页面'
        # 查找 HarmonyOS 版本 行
        version_title = None
        for c in find_components(layout, lambda c: 'harmonyos_version' in attr(c, 'id', '').lower()):
            if '.title' in attr(c, 'id', ''):
                version_title = c
                break
        if not version_title:
            # 滑动查找
            for i in range(3):
                swipe_up()
                layout = dump_layout()
                for c in find_components(layout, lambda c: 'harmonyos_version' in attr(c, 'id', '').lower()):
                    if '.title' in attr(c, 'id', ''):
                        version_title = c
                        break
                if version_title:
                    break
        if not version_title:
            return False, '未找到版本号'
        # 连续点击版本号 7 次
        center = parse_bounds(attr(version_title, 'bounds'))
        if not center:
            return False, '无法获取版本号位置'
        for i in range(7):
            click_at(center[0], center[1], 0.3)
        time.sleep(1)
        # 验证
        new_status = query_developer_mode()
        return (new_status == 'on'), new_status

    else:  # off
        # 导航到开发者选项
        layout = _open_developer_options()
        if not layout:
            return False, '未找到开发者选项入口'
        # 顶部第一个 Toggle 就是开发者选项总开关
        toggles = find_toggles(layout)
        if not toggles:
            return False, '未找到开发者选项开关'
        # 第一个 Toggle (y 最小) 是总开关
        first_tg = min(toggles, key=lambda t: (parse_bounds(attr(t, 'bounds', '')) or [0, float('inf')])[1])
        center = parse_bounds(attr(first_tg, 'bounds'))
        if center:
            click_at(center[0], center[1], 2.0)
        # 确认弹窗
        layout = dump_layout()
        for btn in ['确定', '关闭', '确认']:
            if click_by_text(layout, btn, 2.0):
                time.sleep(1)
                break
        # 验证: 开发者选项入口应消失
        time.sleep(1)
        new_status = query_developer_mode()
        return (new_status == 'off'), new_status


# ── 指纹状态查询 ──

def query_fingerprint():
    """
    查询指纹录入状态 → 'enrolled' | 'not_enrolled' | 'unknown' | None(未找到)

    生物识别和密码 > 指纹, 列表页指纹卡片内含"未录入"/"已录入"文本。
    注意: 仅支持查询，录入指纹需物理传感器交互，不可自动化。
    """
    layout = navigate_to_page('生物识别和密码', 4)
    if not layout:
        return None
    # 指纹和状态文本是上下排列（非左右），用 Column 文本判断
    # Column text 格式: "指纹, 未录入" 或 "指纹, 已录入"
    for c in find_components(layout, lambda c: '指纹' in attr(c, 'text', '')):
        txt = attr(c, 'text', '')
        if '已录入' in txt:
            return 'enrolled'
        if '未录入' in txt:
            return 'not_enrolled'
    # 备用: 查找含"录入"的 Text，检查是否在指纹附近
    fingerprint_comps = find_by_text_nearest(layout, '指纹')
    if fingerprint_comps:
        fb = parse_bounds(attr(fingerprint_comps[0], 'bounds'))
        if fb:
            for c in find_components(layout, lambda c: '录入' in attr(c, 'text', '')):
                cb = parse_bounds(attr(c, 'bounds', ''))
                if cb and abs(cb[1] - fb[1]) < 100 and abs(cb[0] - fb[0]) < 200:
                    if '已录入' in attr(c, 'text', ''):
                        return 'enrolled'
                    if '未录入' in attr(c, 'text', ''):
                        return 'not_enrolled'
    return 'unknown'


# ── 锁屏密码设置 ──

def _input_password_to_textinput(layout, password):
    """在当前页面找到 TextInput，点击激活并输入密码，返回新 layout"""
    for c in find_components(layout, lambda c: attr(c, 'type') == 'TextInput'):
        center = parse_bounds(attr(c, 'bounds'))
        if center:
            click_at(center[0], center[1], 1.0)
            hdc_shell('uitest', 'uiInput', 'text', password)
            time.sleep(2)
            return dump_layout()
    return None


def set_lock_screen_password(password):
    """
    设置锁屏密码 → (success, message)

    生物识别和密码 > 指纹, 若未设置锁屏密码则进入密码设置页。
    流程: 输入密码 → 确认密码 → 完成。

    Args:
        password: 锁屏密码（数字字符串，如 '233333'）
    """
    layout = navigate_to_page('生物识别和密码', 4)
    if not layout:
        return False, '未找到生物识别和密码入口'
    # 点击"指纹"进入（未设密码时跳转到密码设置页）
    if not click_by_text(layout, '指纹', 3.0):
        return False, '未找到指纹入口'
    time.sleep(2)
    layout = dump_layout()
    # 检查是否在密码设置页（标题含"设置锁屏"或"密码"）
    is_pwd_page = False
    for c in find_components(layout, lambda c: '锁屏' in attr(c, 'text', '') or '设置' in attr(c, 'text', '')):
        if '密码' in attr(c, 'text', ''):
            is_pwd_page = True
            break
    if not is_pwd_page:
        # 可能已有锁屏密码，不在密码设置页
        return False, '锁屏密码已设置（无法通过脚本修改，需手动操作）'
    # 关闭弹窗（如有"知道了"）
    click_by_text(layout, '知道了', 1.0)
    time.sleep(1)
    layout = dump_layout()
    # 第一次输入密码
    layout = _input_password_to_textinput(layout, password)
    if not layout:
        return False, '未找到密码输入框'
    # 检查是否需要再次输入
    if find_components(layout, lambda c: '再次' in attr(c, 'text', '')):
        layout = _input_password_to_textinput(layout, password)
        if not layout:
            return False, '确认密码失败'
    time.sleep(2)
    return True, '锁屏密码设置成功'


# ── 隐私空间 ──

def query_privacy_space():
    """
    查询隐私空间状态 → 'not_setup' | 'setup' | 'unknown' | None(未找到)

    隐私和安全 > 隐私空间, 子页面有"开启"按钮=未设置，无"开启"按钮=已设置。
    """
    layout = navigate_to_page('隐私和安全', 4)
    if not layout:
        return None
    # 滑动查找"隐私空间"
    for i in range(6):
        comps = find_components(layout, lambda c: attr(c, 'text') == '隐私空间')
        if comps:
            b = parse_bounds(attr(comps[0], 'bounds'))
            if b and b[1] < 1800:
                break
        swipe_up()
        layout = dump_layout()
    if not click_by_text(layout, '隐私空间', 3.0):
        return None
    time.sleep(2)
    layout = dump_layout()
    # 子页面有"开启"按钮 = 未设置
    open_btns = find_components(layout, lambda c: attr(c, 'text') == '开启' and attr(c, 'type') == 'Button')
    if open_btns:
        return 'not_setup'
    # 无"开启"按钮 = 已设置
    return 'setup'


def set_privacy_space(main_password, space_password):
    """
    开启隐私空间 → (success, message)

    隐私和安全 > 隐私空间 > 开启。
    流程: 确认主空间密码 → 设置隐私空间密码（须与主空间不同）→ 确认密码 → 加载完成。

    Args:
        main_password: 主空间锁屏密码（如 '233333'）
        space_password: 隐私空间密码，必须与主空间密码不同（如 '244444'）
    """
    if main_password == space_password:
        return False, '隐私空间密码不能与主空间密码相同'

    layout = navigate_to_page('隐私和安全', 4)
    if not layout:
        return False, '未找到隐私和安全入口'
    # 滑动查找隐私空间
    for i in range(6):
        comps = find_components(layout, lambda c: attr(c, 'text') == '隐私空间')
        if comps:
            b = parse_bounds(attr(comps[0], 'bounds'))
            if b and b[1] < 1800:
                break
        swipe_up()
        layout = dump_layout()
    if not click_by_text(layout, '隐私空间', 3.0):
        return False, '未找到隐私空间入口'
    time.sleep(2)
    layout = dump_layout()
    # 点击"开启"
    open_btns = find_components(layout, lambda c: attr(c, 'text') == '开启' and attr(c, 'type') == 'Button')
    if not open_btns:
        return False, '隐私空间已设置（无开启按钮）'
    center = parse_bounds(attr(open_btns[0], 'bounds'))
    if center:
        click_at(center[0], center[1], 3.0)
    time.sleep(2)
    # 第一步: 确认主空间密码
    layout = dump_layout()
    if not find_components(layout, lambda c: '主空间' in attr(c, 'text', '')):
        return False, '未出现主空间密码确认页'
    layout = _input_password_to_textinput(layout, main_password)
    if not layout:
        return False, '主空间密码输入失败'
    # 第二步: 设置隐私空间密码
    if not find_components(layout, lambda c: '隐私空间密码' in attr(c, 'text', '')):
        return False, '未出现隐私空间密码设置页（主空间密码可能错误）'
    layout = _input_password_to_textinput(layout, space_password)
    if not layout:
        return False, '隐私空间密码输入失败'
    # 检查是否有错误提示（如密码重复）
    if find_components(layout, lambda c: '重复' in attr(c, 'text', '') or '重新输入' in attr(c, 'text', '')):
        return False, '密码不符合要求（可能与主空间重复）'
    # 第三步: 确认隐私空间密码
    if find_components(layout, lambda c: '再次' in attr(c, 'text', '')):
        layout = _input_password_to_textinput(layout, space_password)
        if not layout:
            return False, '确认密码失败'
    # 等待加载完成
    time.sleep(3)
    layout = dump_layout()
    if find_components(layout, lambda c: '加载' in attr(c, 'text', '')):
        time.sleep(3)
        layout = dump_layout()
    return True, '隐私空间开启成功'
