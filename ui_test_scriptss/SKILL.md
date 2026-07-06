---
name: harmonyos-settings-script
description: Use when generating Python scripts to query or toggle HarmonyOS settings (WLAN, Bluetooth, DND, developer mode, zoom gesture, battery saver, etc.), or when user mentions hdc/uitest/设置/开关/查询 in context of HarmonyOS device automation
---

# HarmonyOS 设置脚本生成器

## 概述

生成 Python 脚本，通过 `hdc` + `uitest` 自动化操作 HarmonyOS 设置。采用三层架构：

```
hdc_utils.py       底层工具: 设备连接、布局获取、组件搜索、UI 操作
settings_api.py    业务 API: 查询/切换设置项，封装导航路径和控件形态
xxx_manager.py     CLI 脚本: 命令行参数解析 → 调用 API → 输出结果
```

**核心原则**：脚本只是 API 的调度器，业务逻辑全在 `settings_api.py`。其他程序可直接 import API 使用。

## 触发条件

- 用户要求"生成" / "写"一个 HarmonyOS 设置脚本
- 用户提到查询/切换某个具体设置项
- 用户提到 hdc、uitest、dumpLayout 等设备自动化关键词
- 用户询问 HarmonyOS 设置页面结构

## 工作流程

### 第 1 步：识别目标

解析用户请求，确定：
- **目标设置项**：如"放大手势"、"省电模式"、"勿扰模式"
- **操作类型**：query（查询）/ on（打开）/ off（关闭）/ set（设置值）

### 第 2 步：从知识库提取上下文

读取 `HarmonyOS设置功能知识库.md`，只提取相关章节：

1. **环境信息**（第一章）：hdc 路径、包名/Ability 名
2. **目标页面**（第三章）：导航路径、入口文本
3. **滑动需求**（第八章）：滑动屏数
4. **控件形态**（第六章）：toggle_row / button_card / text_value / slider_row / nav_item / button_selected
5. **第三级页面**（第四章）：子页面 Toggle 文本（开关操作时需要）
6. **安全认证门**（第九章）：是否需要前置认证
7. **弹窗信息**（第七章 + 第十章 10.3）：是否触发弹窗/选择器
8. **页面加载时间**（第十二章 + 第十章 10.7）：是否需要额外等待
9. **⚠ 交互模式**（第十章 10.2）：匹配操作类型对应的交互模式 — **这是避免调试的关键步骤**

### 第 2.5 步：匹配交互模式（避免调试的关键）

在编写 API 函数前，先在知识库第十章「通用交互模式」的 10.2 交互模式索引中找到匹配的模式：

1. 识别操作类型：开关切换？查询？输入文本？连接设备？选择选项？
2. 在 10.2 索引表中找到匹配模式（A-L）
3. 按模式流程 + 第三章页面结构 → 直接编写代码
4. 检查 10.3 是否有已知弹窗需要处理
5. 检查 10.6 避坑清单是否有已知陷阱
6. 若模式+页面结构都齐全 → 直接生成，无需调试
7. 若模式已知但页面结构未知 → 只探索缺失的页面结构
8. 若模式未知 → 探索完整流程后补充到第十章

### 第 3 步：在 settings_api.py 中添加 API 函数

根据知识库信息，封装具体参数：

```python
# 示例: 在 settings_api.py 中添加"放大手势"API

def query_zoom_gesture():
    """查询放大手势状态 → 'on' | 'off' | 'unknown'"""
    return query_setting('关怀和无障碍', '放大手势', 'text_value', scroll=4)

def set_zoom_gesture(desired):
    """设置放大手势 → (success, new_status)"""
    return toggle_setting('关怀和无障碍', '放大手势', 'text_value', desired,
                          scroll=4, third_level_toggle='放大手势')
```

已有 API 函数（按分类归属排列）：

**网络与连接**

| 设置项 | 查询函数 | 开关函数 |
|--------|---------|---------|
| WLAN | `query_wlan()` | `set_wlan('on'/'off')` / `connect_wlan(ssid, password)` |
| WLAN下自动下载 | `query_wlan_auto_download()` | `set_wlan_auto_download('on'/'off')` |
| 蓝牙开关 | `query_bluetooth()` | `set_bluetooth('on'/'off')` |
| 蓝牙设备 | `query_bluetooth_device(name)` | `connect_bluetooth(name)` / `disconnect_bluetooth(name)` |
| 星闪 | `query_nearlink()` | — |
| 飞行模式 | `query_flight_mode()` | `set_flight_mode('on'/'off')` |
| 个人热点 | `query_personal_hotspot()` | — |
| 热点配置 | `query_hotspot_config()` | `set_hotspot_name(name)` / `set_hotspot_password(pwd)` |
| 网络加速 | `query_network_acceleration()` | `set_network_acceleration('on'/'off')` |

**移动网络与 SIM 卡**

| 设置项 | 查询函数 | 开关函数 |
|--------|---------|---------|
| 默认数据卡 | `query_default_data_card()` | — |
| SIM卡状态 | `query_sim_status()` / `query_sim_carrier()` | — |
| SIM卡使用状态 | `query_sim_enabled(card)` | `set_sim_enabled(card, 'on'/'off')` |

**显示与亮度**

| 设置项 | 查询函数 | 开关函数 |
|--------|---------|---------|
| 屏幕亮度 | `query_brightness()` → 百分比 | — |
| 自动调节亮度 | `query_auto_brightness()` | `set_auto_brightness('on'/'off')` |
| 电子书模式 | `query_ebook_mode()` | — |

**声音**

| 设置项 | 查询函数 | 开关函数 |
|--------|---------|---------|
| 朗读速度 | `query_speech_rate()` | `set_speech_rate(value)` |
| 来电铃声 | `query_ringtone()` | `set_ringtone_default()` |

**电池**

| 设置项 | 查询函数 | 开关函数 |
|--------|---------|---------|
| 省电模式 | `query_power_saving()` | `set_power_saving('on'/'off')` |

**通知与免打扰**

| 设置项 | 查询函数 | 开关函数 |
|--------|---------|---------|
| 勿扰模式 | `query_dnd()` | `set_dnd('on'/'off')` |

**辅助功能**

| 设置项 | 查询函数 | 开关函数 |
|--------|---------|---------|
| 放大手势 | `query_zoom_gesture()` | `set_zoom_gesture('on'/'off')` |

**系统**

| 设置项 | 查询函数 | 开关函数 |
|--------|---------|---------|
| 系统导航模式 | `query_navigation_mode()` | — |
| 系统语言 | `query_system_language()` | `add_system_language(lang)` |
| 默认输入法 | `query_default_input_method()` | — |
| 自动时区 | `query_auto_timezone()` | `set_auto_timezone('on'/'off')` |
| 系统时区 | `query_timezone()` | `set_timezone(timezone_name)` |
| 存储空间 | `query_storage()` | — |
| 开发者模式 | `query_developer_mode()` | `set_developer_mode('on'/'off')` |
| USB调试 | `query_usb_debug()` | `set_usb_debug('on'/'off')` |

**安全**

| 设置项 | 查询函数 | 开关函数 |
|--------|---------|---------|
| 锁屏方式 | `query_lock_screen_method()` | —（安全验证，不可自动化） |
| 锁屏密码 | — | `set_lock_screen_password(password)` |
| 指纹录入状态 | `query_fingerprint()` | —（录入需物理传感器） |
| 隐私空间 | `query_privacy_space()` | `set_privacy_space(main_pwd, space_pwd)` |

### 第 4 步：生成 CLI 脚本（薄壳）

脚本只做三件事：解析参数 → 调用 API → 输出结果

```python
#!/usr/bin/env python3
"""HarmonyOS 勿扰模式管理（CLI 调度器）"""
import argparse
from hdc_utils import find_hdc, check_device
from settings_api import query_dnd, set_dnd

def main():
    parser = argparse.ArgumentParser(description='HarmonyOS 勿扰模式管理')
    parser.add_argument('--mode', required=True, choices=['on', 'off', 'query'])
    args = parser.parse_args()

    find_hdc()
    check_device()

    if args.mode == 'query':
        status = query_dnd()
        print(f"勿扰模式: {status}")
    else:
        success, new_status = set_dnd(args.mode)
        print(f"操作{'成功' if success else '失败'}: {new_status}")

if __name__ == '__main__':
    main()
```

### 第 5 步：保存、同步并测试

- API 函数加到 `settings_api.py`
- **同步更新 SKILL.md 的已有 API 函数表格**（第 3 步中的表格）
- CLI 脚本保存为 `query_<功能>_state.py` 或 `<功能>_manager.py`
- 在设备上运行验证

## 控件形态速查

| 形态 | 识别方法 | 读状态 | 切换操作 |
|------|---------|--------|---------|
| toggle_row | 文本旁有 Toggle | `attr(toggle, 'checked')` | 点 Toggle 中心 |
| button_card | 卡片内有 Button | 按钮文本"立即开启"=关 | 点 Button |
| text_value | 文本右侧有文本 | 右侧文本内容 | 进子页面 → Toggle |
| slider_row | 文本附近有 Slider | `attr(slider, 'text')`（不是 value！） | 按比例点轨道 |
| nav_item | 可点击、无状态 | 进子页面查看 | 进子页面 |
| button_selected | 文本右侧有多个 Button | `attr(button, 'selected')` = true 的 Button 内 Text | 点 selected=false 的 Button |

## 关键规则

1. **Slider 的值在 `text`/`originalText` 属性中，不是 `value`**
2. **选择器选项是 `MenuItem` 类型，不是 `Text`**
3. **Text 组件通常 `clickable=false`** — 要点击父级 Row
4. **`find_by_text` 是子串匹配** — 目标文本若是页面标题子串（如 `星闪` ← `星闪和蓝牙`），会碰撞命中标题导致 `unknown`。所有 `read_status_*`/`_toggle_*`/`click_by_text` 已改用 `find_by_text_nearest()` 按文本长度差排序规避。新增设置项时检查目标文本是否是入口文本的子串
5. **toggle_row 和 button_card 操作通常不触发弹窗** — 例外: 部分 toggle_row 关闭时弹出确认对话框（如"WLAN 下自动下载"），需在 toggle 后检查并点击确认按钮
6. **text_value 开关需要 3 步**：列表页 → 点击项 → 子页面 Toggle → 返回 → 验证
7. **导航前先 force-stop** — 使用 `restart_settings()`
8. **属性是嵌套的**：`node["attributes"]["text"]`
9. **API 函数不应包含 print** — 只返回结果，打印交给 CLI 脚本
10. **搜索直达** — 当设置项导航层级过深或不在常规入口时，用 `search_setting(keyword, result_text)` 通过设置首页搜索框搜索并跳转。搜索结果文本可能与输入不同（如带空格），需用实际结果文本作为 `result_text`

## 脚本命名规范

- 纯查询：`query_<功能>_state.py`
- 开关操作：`<功能>_manager.py`

## 已有文件结构

```
ui_test_scriptss/
├── hdc_utils.py              底层工具 (618行)
├── settings_api.py           业务 API (1178行)
├── template.py               CLI 模板 (62行)
├── query_zoom_gesture_state.py     41行
├── query_nearlink_state.py         41行
├── query_personal_hotspot_state.py 37行
├── query_developer_mode_state.py   36行
├── dnd_manager.py                  48行
├── bluetooth_manager.py            64行
├── speech_rate_manager.py          52行
├── lockscreen_method_manager.py    77行
├── ringtone_manager.py             70行
├── hotspot_config_manager.py       75行
├── auto_brightness_manager.py      50行
├── brightness_manager.py           屏幕亮度百分比查询
├── query_multi_status.py           综合查询 (省电/亮度/电子书/导航)
├── query_default_data_card.py      40行
├── wlan_auto_download_manager.py   50行
├── wlan_connect_manager.py         WiFi 连接 (ssid+password)
├── sim_card_manager.py             SIM卡状态/运营商/使用状态
├── network_acceleration_manager.py 网络加速
├── language_manager.py             系统语言查询/添加
├── input_method_manager.py         默认输入法查询
├── timezone_manager.py             自动时区开关/系统时区查询与设置
├── storage_manager.py              存储空间使用率/已用/总大小/应用占用查询
├── usb_debug_manager.py            USB调试开关查询与设置
├── developer_mode_manager.py       开发者模式查询与开关（点击版本号7次/关闭总开关）
├── fingerprint_manager.py          指纹录入状态查询
├── privacy_space_manager.py        隐私空间状态查询
├── 脚本生成失败说明.md             无法生成的功能及原因
├── HarmonyOS设置功能知识库.md       知识库 v5 (15章, 1527行)
└── SKILL.md                        本文件
```
