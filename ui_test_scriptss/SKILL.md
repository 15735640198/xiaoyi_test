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
4. **控件形态**（第六章）：toggle_row / button_card / text_value / slider_row / nav_item
5. **第三级页面**（第四章）：子页面 Toggle 文本（开关操作时需要）
6. **安全认证门**（第九章）：是否需要前置认证
7. **弹窗信息**（第七章）：是否触发弹窗/选择器
8. **页面加载时间**（第十二章）：是否需要额外等待

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

已有 API 函数：

| 设置项 | 查询函数 | 开关函数 |
|--------|---------|---------|
| 勿扰模式 | `query_dnd()` | `set_dnd('on'/'off')` |
| 放大手势 | `query_zoom_gesture()` | `set_zoom_gesture('on'/'off')` |
| 开发者模式 | `query_developer_mode()` | — |
| 个人热点 | `query_personal_hotspot()` | — |
| 省电模式 | `query_power_saving()` | `set_power_saving('on'/'off')` |
| 飞行模式 | `query_flight_mode()` | `set_flight_mode('on'/'off')` |
| WLAN | `query_wlan()` | `set_wlan('on'/'off')` |
| 蓝牙开关 | `query_bluetooth()` | — |
| 蓝牙设备 | `query_bluetooth_device(name)` | `connect_bluetooth(name)` / `disconnect_bluetooth(name)` |
| 屏幕亮度 | `query_brightness()` | — |

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

## 关键规则

1. **Slider 的值在 `text`/`originalText` 属性中，不是 `value`**
2. **选择器选项是 `MenuItem` 类型，不是 `Text`**
3. **Text 组件通常 `clickable=false`** — 要点击父级 Row
4. **`find_by_text` 是子串匹配** — 用 `find_button()` 加长度过滤
5. **toggle_row 和 button_card 操作不会触发弹窗**
6. **text_value 开关需要 3 步**：列表页 → 点击项 → 子页面 Toggle → 返回 → 验证
7. **导航前先 force-stop** — 使用 `restart_settings()`
8. **属性是嵌套的**：`node["attributes"]["text"]`
9. **API 函数不应包含 print** — 只返回结果，打印交给 CLI 脚本

## 脚本命名规范

- 纯查询：`query_<功能>_state.py`
- 开关操作：`<功能>_manager.py`

## 已有文件结构

```
ui_test_scriptss/
├── hdc_utils.py              底层工具 (473行)
├── settings_api.py           业务 API (400行)
├── template.py               CLI 模板 (62行)
├── query_zoom_gesture_state.py     41行
├── query_personal_hotspot_state.py 37行
├── query_developer_mode_state.py   36行
├── dnd_manager.py                  48行
├── bluetooth_manager.py            64行
├── HarmonyOS设置功能知识库.md       知识库 v5 (15章, 1468行)
└── SKILL.md                        本文件
```
