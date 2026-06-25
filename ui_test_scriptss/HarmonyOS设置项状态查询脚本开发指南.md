# HarmonyOS 设置项状态查询脚本开发指南

基于 `hdc` + `uitest` 命令行工具，通过 Python 脚本自动化查询 HarmonyOS 设备中任意设置项的状态。

## 一、概述

### 核心原理

```
┌──────────────┐     ┌───────────────────┐     ┌──────────────────┐
│  hdc shell   │────>│  uitest dumpLayout │────>│  控件树 JSON 文件  │
│  命令执行    │     │  生成布局快照       │     │  (设备端 /data/)  │
└──────────────┘     └───────────────────┘     └────────┬─────────┘
                                                        │
                     ┌───────────────────┐              │ hdc file recv
                     │  uitest uiInput   │              ▼
                     │  click / swipe    │<─────┌──────────────────┐
                     │  模拟用户操作      │      │  Python 解析 JSON │
                     └───────────────────┘      │  定位目标组件      │
                              ▲                 │  读取状态属性      │
                              │                 └──────────────────┘
                              │ 导航需要点击时
                     ┌───────────────────┐
                     │  aa start          │
                     │  启动目标应用       │
                     └───────────────────┘
```

### 适用场景

| 场景 | 示例 |
|------|------|
| 查询开关状态 | 个人热点、蓝牙、WiFi、飞行模式、NFC |
| 查询文本值 | WiFi 名称、设备名称、IP 地址、亮度百分比 |
| 查询滑块值 | 亮度、音量、字号大小 |
| 查询选择项 | 省电模式、屏幕刷新率、分辨率 |

### 不适用场景

- 需要 root 权限的系统底层配置
- 后台无 UI 界面的服务状态（用 `hdc shell ps`、`hdc shell hidumper` 等）
- 加密/安全相关的敏感信息

---

## 二、环境准备

### 2.1 安装 hdc

hdc（HarmonyOS Device Connector）随 DevEco Studio 附带。

1. 下载 DevEco Studio：https://developer.huawei.com/consumer/cn/download/
2. 安装后，hdc 位于：
   ```
   <DevEco Studio 安装目录>\sdk\<版本号>\openharmony\toolchains\hdc.exe
   ```
3. 将上述路径加入系统环境变量 PATH
4. **重新打开终端**，验证：

```bash
hdc version
# 输出: Ver: 3.2.0d
```

> **避坑**：修改 PATH 后必须重新打开终端窗口，旧窗口不会刷新。

### 2.2 连接设备

**USB 连接**：
- 用数据线连接设备与电脑
- 在设备上开启「设置 > 关于手机 > 连续点击版本号 7 次」开启开发者选项
- 在「设置 > 系统与更新 > 开发者选项」中开启「USB 调试」

**WiFi 连接**：
```bash
# 先通过 USB 连接，然后:
hdc tmode port 8710                    # 设备端开启 TCP 监听
hdc tconn 192.168.1.100:8710           # 电脑端连接设备 IP
```

**验证连接**：
```bash
hdc list targets
# 输出设备序列号表示连接成功:
# 3UJ0225328003793
# 或: 192.168.1.100:8710
```

> 若输出 `[Empty]` 说明没有设备连接。

### 2.3 Python 环境

需要 Python 3.8+，仅使用标准库（无需 pip install）。

```bash
python --version
# Python 3.12.7
```

---

## 三、开发流程（5 个关键步骤）

以下每个步骤都包含实际可运行的命令和多个示例。

### 步骤 1：确定目标应用的包名和 Ability 名

#### 为什么需要

HarmonyOS 通过 `aa start` 命令启动应用，需要指定包名（bundleName）和 Ability 名。不同设备、不同系统版本的包名可能不同，必须先查清楚。

#### 方法 A：从已安装应用列表中搜索

```bash
# 列出所有已安装应用，过滤关键词
hdc shell bm dump -a | findstr -i settings
```

实际输出示例：
```
com.huawei.hmos.settings          # ← 这就是设置应用的包名
com.huawei.hmos.systemmanager
```

#### 方法 B：查看指定包的详细信息（含 Ability 名）

```bash
hdc shell bm dump -n com.huawei.hmos.settings
```

实际输出示例（截取关键部分）:
```
"entryModuleName": "phone_settings"
...
{
  "name": "com.huawei.hmos.settings.MainAbility",   # ← 这就是主 Ability 名
  "type": 1,
  ...
}
```

#### 方法 C：查看 aa start 命令语法

不同系统版本的 `aa start` 参数可能不同，务必先查帮助：

```bash
hdc shell aa start --help
```

实际输出示例：
```
usage: aa start <options>
options list:
  -h, --help
  [-d <device-id>] [-a <ability-name> -b <bundle-name>] [-m <module-name>]
  [-D] [-E] [-S] [-N] [-C] [-R] [-c] [-s <window-mode>]
  ...
```

> **避坑**：`aa start` 的参数在不同版本有差异！
> - 部分版本用 `-n <bundleName>` + 位置参数 `<abilityName>`
> - 部分版本用 `-a <abilityName> -b <bundleName>`
> - **务必先跑 `aa start --help` 确认你的设备用哪种语法**

#### 示例 1：启动设置应用

```bash
# 查到包名: com.huawei.hmos.settings
# 查到 Ability: com.huawei.hmos.settings.MainAbility
# 查到语法: -a <ability> -b <bundle>

hdc shell aa start -a com.huawei.hmos.settings.MainAbility -b com.huawei.hmos.settings
# 输出: start ability successfully.
```

#### 示例 2：启动其他系统应用

```bash
# 查找电话应用
hdc shell bm dump -a | findstr -i dialer
# → com.ohos.dialer

# 查 Ability 名
hdc shell bm dump -n com.ohos.dialer
# → com.ohos.dialer.MainAbility

# 启动
hdc shell aa start -a com.ohos.dialer.MainAbility -b com.ohos.dialer
```

#### 示例 3：带 moduleName 启动

```bash
# 从 bm dump 输出中看到 entryModuleName: "phone_settings"
hdc shell aa start -a com.huawei.hmos.settings.MainAbility -b com.huawei.hmos.settings -m phone_settings
```

#### 在脚本中实现：多候选自动尝试

```python
SETTINGS_CANDIDATES = [
    ('com.huawei.hmos.settings', None, 'com.huawei.hmos.settings.MainAbility'),
    ('com.huawei.hmos.settings', 'phone_settings', 'com.huawei.hmos.settings.MainAbility'),
    ('com.huawei.hmossettings',  None, 'EntryAbility'),     # 老版本备选
    ('com.android.settings',     None, 'Settings'),          # AOSP 备选
]

def start_app(candidates):
    for bundle, mod, ability in candidates:
        args = ['aa', 'start', '-a', ability, '-b', bundle]
        if mod:
            args += ['-m', mod]
        output = hdc_shell(*args)
        if 'fail' not in output.lower():
            return True
    return False
```

---

### 步骤 2：导航到目标设置页面

#### 核心操作

```
dumpLayout (获取当前页面) → 按文本找到入口 → uiInput click (点击) → 等待页面加载 → 重复
```

#### 2a. 获取当前页面控件树

```bash
hdc shell uitest dumpLayout
```

实际输出：
```
DumpLayout saved to:/data/local/tmp/layout_1735308093471.json
```

> **关键发现**：文件名带时间戳！不是固定路径 `/data/local/tmp/layout.json`。
> 必须从 stdout 解析实际路径，再 `hdc file recv` 拉取。

拉取文件到本地：
```bash
hdc file recv /data/local/tmp/layout_1735308093471.json C:\temp\layout.json
```

在脚本中实现（自动解析路径）：
```python
def dump_layout():
    output = hdc_shell('uitest', 'dumpLayout')
    # 从输出中解析文件路径
    m = re.search(r'saved to:\s*(/\S+\.json)', output)
    remote_path = m.group(1) if m else '/data/local/tmp/layout.json'
    # 拉取到本地
    local_path = os.path.join(tempfile.gettempdir(), 'hm_layout.json')
    run_cmd([hdc, 'file', 'recv', remote_path, local_path])
    with open(local_path, 'r', encoding='utf-8') as f:
        return json.load(f)
```

#### 2b. 按文本查找并点击组件

找到文本对应的控件，获取其 bounds 中心坐标，然后点击：

```python
# 1. 在控件树中按文本查找
comps = find_by_text(layout, '移动网络')
# → [{attributes: {text: '移动网络', bounds: '[228,1521][421,1577]', type: 'Text', ...}}]

# 2. 解析 bounds 获取中心坐标
bounds = '[228,1521][421,1577]'  # [left,top][right,bottom]
# 中心点: x = (228+421)/2 = 324, y = (1521+1577)/2 = 1549

# 3. 点击
hdc shell uitest uiInput click 324 1549
```

#### 示例 1：点击「移动网络」进入子页面

```python
layout = dump_layout()
click_by_text(layout, '移动网络')
# 输出: 找到 '移动网络' (共 1 个匹配)
#       点击坐标 (324, 1549)
```

#### 示例 2：点击「蓝牙」进入子页面

```python
layout = dump_layout()
click_by_text(layout, '蓝牙')
# 输出: 找到 '蓝牙' (共 1 个匹配)
#       点击坐标 (324, 820)
```

#### 示例 3：页面需要向下滑动才能看到目标项

```bash
# 从屏幕中部滑到底部
hdc shell uitest uiInput swipe 540 1800 540 400
```

```python
def swipe_up(distance=1400):
    """上滑滚动页面"""
    hdc_shell('uitest', 'uiInput', 'swipe', '540', '1800', '540', str(1800 - distance))

# 先滑动再查找
swipe_up()
layout = dump_layout()
click_by_text(layout, '个人热点')
```

#### 示例 4：返回上一页

```bash
# 方式 1: 返回键
hdc shell uitest systemInput keyEvent 2

# 方式 2: 点击左上角返回按钮（需从 layout 中查找）
```

```python
def go_back():
    """模拟返回键"""
    hdc_shell('uitest', 'systemInput', 'keyEvent', '2')
    time.sleep(1.5)
```

#### 示例 5：完整导航链（设置主页 → 移动网络 → 个人热点）

```python
# 启动设置
hdc_shell('aa', 'start', '-a', 'com.huawei.hmos.settings.MainAbility',
           '-b', 'com.huawei.hmos.settings')
time.sleep(3)

# 第一层：点击「移动网络」
layout = dump_layout()
click_by_text(layout, '移动网络')    # 等待 2.5s 页面加载

# 第二层：点击「个人热点」
layout = dump_layout()
click_by_text(layout, '个人热点')    # 等待 2.5s 页面加载

# 到达目标页面
layout = dump_layout()
```

---

### 步骤 3：理解布局 JSON 结构

#### 整体结构

`uitest dumpLayout` 输出的 JSON 是一棵控件树：

```json
{
  "attributes": {
    "type": "RootFrame",
    "bounds": "[0,0][1320,2772]"
  },
  "children": [
    {
      "attributes": {
        "type": "Text",
        "text": "设置",
        "bounds": "[48,155][205,246]"
      },
      "children": []
    },
    {
      "attributes": {
        "type": "Text",
        "text": "移动网络",
        "bounds": "[228,1521][421,1577]",
        "clickable": "true"
      },
      "children": []
    }
  ]
}
```

#### 关键要点：属性嵌套在 `attributes` 字典里

```python
# ❌ 错误：直接从顶层读
text = node.get('text')           # → None
type_ = node.get('type')          # → None
bounds = node.get('bounds')       # → None

# ✅ 正确：从 attributes 字典读
attrs = node.get('attributes', {})
text = attrs.get('text', '')      # → '移动网络'
type_ = attrs.get('type', '')     # → 'Text'
bounds = attrs.get('bounds', '')  # → '[228,1521][421,1577]'
```

封装为统一的访问函数：
```python
def attr(comp, key, default=''):
    """统一从 attributes 字典读取属性"""
    a = comp.get('attributes')
    if a is None:
        return comp.get(key, default)  # 兼容属性在顶层的格式
    return a.get(key, default)
```

#### 常用属性说明

| 属性名 | 含义 | 示例值 |
|--------|------|--------|
| `type` | 组件类型 | `Text`, `Button`, `Toggle`, `Slider`, `Image`, `Row`, `List` |
| `text` | 显示文本 | `移动网络`, `已开启` |
| `description` | 无障碍描述文本 | `个人热点开关` |
| `bounds` | 控件边界坐标 | `[228,1521][421,1577]` (格式: `[left,top][right,bottom]`) |
| `checked` | Toggle/Switch 的选中状态 | `true`, `false` |
| `clickable` | 是否可点击 | `true`, `false` |
| `enabled` | 是否启用 | `true`, `false` |
| `value` | Slider 的当前值 | `50` |

#### bounds 坐标格式解析

```
"[left,top][right,bottom]"
例如: "[228,1521][421,1577]"

中心点计算:
  x = (left + right) / 2 = (228 + 421) / 2 = 324
  y = (top + bottom) / 2 = (1521 + 1577) / 2 = 1549
```

```python
def parse_bounds(bounds):
    """解析 bounds 字符串，返回中心坐标 (x, y)"""
    if isinstance(bounds, str):
        nums = re.findall(r'\d+', bounds)
        if len(nums) >= 4:
            return ((int(nums[0]) + int(nums[2])) // 2,
                    (int(nums[1]) + int(nums[3])) // 2)
    return None
```

---

### 步骤 4：定位目标组件

#### 核心函数：递归遍历控件树

```python
def find_components(node, predicate, results=None):
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
```

#### 示例 1：按文本查找（最常用）

```python
def find_by_text(node, text):
    return find_components(node, lambda c: text in get_text(c))

# 用法
comps = find_by_text(layout, '个人热点')
# 返回所有 text 或 description 包含 '个人热点' 的组件
```

#### 示例 2：按类型查找 Toggle/Switch

```python
def find_toggles(node):
    return find_components(
        node,
        lambda c: attr(c, 'type', '').lower() in ('toggle', 'switch', 'toggleswitch')
    )

# 用法
toggles = find_toggles(layout)
for t in toggles:
    print(f"  text={get_text(t)} checked={attr(t, 'checked')}")
```

#### 示例 3：按类型查找 Slider（滑块）

```python
def find_sliders(node):
    return find_components(node, lambda c: attr(c, 'type', '').lower() == 'slider')

# 用法: 查找亮度滑块
sliders = find_sliders(layout)
for s in sliders:
    print(f"  value={attr(s, 'value')} bounds={attr(s, 'bounds')}")
```

#### 示例 4：按任意属性查找

```python
# 查找所有可点击的组件
clickables = find_components(layout, lambda c: attr(c, 'clickable') == 'true')

# 查找所有 checked 的组件
checked = find_components(layout, lambda c: attr(c, 'checked') == 'true')

# 查找所有带有 enabled 属性的组件
enabled = find_components(layout, lambda c: attr(c, 'enabled', '') != '')
```

#### 示例 5：多策略匹配 Toggle（开关通常不和文本在同一个组件）

设置页面中，"个人热点"文本和开关 Toggle 往往是**两个独立组件**，需要关联匹配：

```python
def find_toggle_for_text(layout, target_text):
    toggles = find_toggles(layout)
    text_comps = find_by_text(layout, target_text)

    # 策略1: Toggle 自身包含目标文本
    for t in toggles:
        if target_text in get_text(t):
            return t

    # 策略2: 离目标文本最近的 Toggle（按坐标距离）
    if text_comps and toggles:
        text_center = parse_bounds(attr(text_comps[0], 'bounds'))
        if text_center:
            nearest = min(toggles,
                key=lambda t: distance(text_center, parse_bounds(attr(t, 'bounds'))))
            return nearest

    # 策略3: 只有一个 Toggle，直接返回
    if len(toggles) == 1:
        return toggles[0]

    return None

def distance(p1, p2):
    if not p1 or not p2:
        return float('inf')
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])  # 曼哈顿距离
```

---

### 步骤 5：读取组件状态

#### 示例 1：读取 Toggle 开关状态

```python
def read_toggle_state(comp):
    """读取开关状态 → 'on' | 'off' | 'unknown'"""
    val = attr(comp, 'checked', None)
    if val is None:
        val = attr(comp, 'isOn', None)
    if val is True or val in ('true', 'True', 1, '1'):
        return 'on'
    if val is False or val in ('false', 'False', 0, '0'):
        return 'off'
    return 'unknown'

# 用法
layout = dump_layout()
toggle = find_toggle_for_text(layout, '个人热点')
if toggle:
    state = read_toggle_state(toggle)
    print(f"个人热点: {state}")  # → 个人热点: off
```

#### 示例 2：读取文本值（如 WiFi 名称）

```python
# 场景: WiFi 设置页面，读取当前连接的 WiFi 名称
layout = dump_layout()
# WiFi 名称通常显示在 "WLAN" 文本下方
comps = find_by_text(layout, 'WLAN')
if comps:
    # 找到 WLAN 标题旁边或下方的文本
    wlan_title = comps[0]
    wlan_center = parse_bounds(attr(wlan_title, 'bounds'))
    # 查找同区域下方的文本组件
    nearby_texts = find_components(layout, lambda c:
        attr(c, 'type') == 'Text' and
        parse_bounds(attr(c, 'bounds')) and
        parse_bounds(attr(c, 'bounds'))[1] > wlan_center[1] and  # y 在下方
        distance(wlan_center, parse_bounds(attr(c, 'bounds'))) < 500
    )
    for t in nearby_texts:
        text = get_text(t)
        if text and text != 'WLAN':
            print(f"WiFi 名称: {text}")
            break
```

#### 示例 3：读取 Slider 滑块值（如屏幕亮度）

```python
# 场景: 显示设置页面，读取亮度滑块值
layout = dump_layout()
sliders = find_sliders(layout)
if sliders:
    brightness_slider = sliders[0]  # 通常只有一个 Slider
    value = attr(brightness_slider, 'value', '')
    print(f"亮度值: {value}")  # → 亮度值: 85

    # 也可以通过 text 属性获取
    text_val = get_text(brightness_slider)
    if text_val:
        print(f"亮度文本: {text_val}")
```

#### 示例 4：读取开关项的副文本（如"已开启"/"已关闭"）

```python
# 场景: 蓝牙设置页面，读取蓝牙开关下方的状态文本
layout = dump_layout()
bt_comps = find_by_text(layout, '蓝牙')
if bt_comps:
    bt_center = parse_bounds(attr(bt_comps[0], 'bounds'))
    # 查找下方状态文本
    nearby = find_components(layout, lambda c:
        attr(c, 'type') == 'Text' and
        get_text(c) in ('已开启', '已关闭', '开启中', '关闭中') and
        distance(bt_center, parse_bounds(attr(c, 'bounds'))) < 300
    )
    if nearby:
        print(f"蓝牙状态: {get_text(nearby[0])}")
```

---

## 四、可复用工具函数库

以下是从实战脚本中提炼的完整工具函数，可直接复制到新脚本中使用：

```python
#!/usr/bin/env python3
"""HarmonyOS 设置项状态查询 - 通用工具函数库"""

import subprocess, json, os, re, sys, time, tempfile

# ── hdc 调用 ──

_HDC = 'hdc'  # 可替换为完整路径

def hdc_shell(*args, timeout=30):
    """执行 hdc shell 命令"""
    r = subprocess.run([_HDC, 'shell', *list(args)],
                       capture_output=True, text=True,
                       timeout=timeout, encoding='utf-8', errors='replace')
    return (r.stdout or '') + (r.stderr or '')

# ── 布局获取 ──

def dump_layout():
    """获取当前页面控件树 JSON"""
    output = hdc_shell('uitest', 'dumpLayout')
    time.sleep(1)
    # 解析动态文件路径
    m = re.search(r'saved to:\s*(/\S+\.json)', output)
    remote = m.group(1) if m else '/data/local/tmp/layout.json'
    local = os.path.join(tempfile.gettempdir(), 'hm_layout.json')
    subprocess.run([_HDC, 'file', 'recv', remote, local],
                   capture_output=True, timeout=15)
    with open(local, 'r', encoding='utf-8') as f:
        return json.load(f)

# ── 组件属性访问 ──

def attr(comp, key, default=''):
    """从 attributes 字典读取属性（核心函数）"""
    a = comp.get('attributes')
    if a is None:
        return comp.get(key, default)
    return a.get(key, default)

def get_text(comp):
    """获取组件文本"""
    return attr(comp, 'text', '') or attr(comp, 'description', '') or ''

# ── 组件查找 ──

def find_components(node, predicate, results=None):
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

def find_by_text(node, text):
    """按文本查找"""
    return find_components(node, lambda c: text in get_text(c))

def find_toggles(node):
    """查找所有 Toggle/Switch"""
    return find_components(node,
        lambda c: attr(c, 'type', '').lower() in ('toggle', 'switch', 'toggleswitch'))

def find_sliders(node):
    """查找所有 Slider"""
    return find_components(node, lambda c: attr(c, 'type', '').lower() == 'slider')

# ── 坐标与距离 ──

def parse_bounds(bounds):
    """解析 bounds → 中心坐标 (x, y)"""
    if isinstance(bounds, str):
        nums = re.findall(r'\d+', bounds)
        if len(nums) >= 4:
            return ((int(nums[0]) + int(nums[2])) // 2,
                    (int(nums[1]) + int(nums[3])) // 2)
    return None

def distance(p1, p2):
    """曼哈顿距离"""
    if not p1 or not p2:
        return float('inf')
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

# ── 交互操作 ──

def click_at(x, y, wait=2.5):
    """点击坐标"""
    hdc_shell('uitest', 'uiInput', 'click', str(x), str(y))
    time.sleep(wait)

def click_by_text(layout, text, wait=2.5):
    """按文本查找并点击"""
    comps = find_by_text(layout, text)
    if not comps:
        return False
    center = parse_bounds(attr(comps[0], 'bounds'))
    if not center:
        return False
    click_at(center[0], center[1], wait)
    return True

def swipe(x1, y1, x2, y2, wait=1.5):
    """滑动"""
    hdc_shell('uitest', 'uiInput', 'swipe', str(x1), str(y1), str(x2), str(y2))
    time.sleep(wait)

def go_back(wait=1.5):
    """返回键"""
    hdc_shell('uitest', 'systemInput', 'keyEvent', '2')
    time.sleep(wait)

# ── 状态读取 ──

def read_toggle_state(comp):
    """读取开关状态 → 'on' | 'off' | 'unknown'"""
    val = attr(comp, 'checked', None)
    if val is None:
        val = attr(comp, 'isOn', None)
    if val is True or val in ('true', 'True', 1, '1'):
        return 'on'
    if val is False or val in ('false', 'False', 0, '0'):
        return 'off'
    return 'unknown'

def find_toggle_for_text(layout, target_text):
    """多策略查找与目标文本关联的 Toggle"""
    toggles = find_toggles(layout)
    text_comps = find_by_text(layout, target_text)

    # 策略1: Toggle 自身包含目标文本
    for t in toggles:
        if target_text in get_text(t):
            return t
    # 策略2: 离目标文本最近的 Toggle
    if text_comps and toggles:
        tc = parse_bounds(attr(text_comps[0], 'bounds'))
        if tc:
            return min(toggles, key=lambda t: distance(tc, parse_bounds(attr(t, 'bounds'))))
    # 策略3: 只有一个 Toggle
    if len(toggles) == 1:
        return toggles[0]
    return None

# ── 调试 ──

def debug_print_toggles(layout):
    """打印所有 Toggle 信息"""
    toggles = find_toggles(layout)
    print(f"找到 {len(toggles)} 个 Toggle:")
    for i, t in enumerate(toggles):
        print(f"  [{i}] text={get_text(t)!r} checked={attr(t,'checked','N/A')} "
              f"bounds={attr(t,'bounds')}")

def debug_print_text_matches(layout, keyword):
    """打印包含关键词的所有组件"""
    comps = find_by_text(layout, keyword)
    print(f"找到 {len(comps)} 个包含 '{keyword}' 的组件:")
    for i, c in enumerate(comps[:10]):
        print(f"  [{i}] type={attr(c,'type')} text={get_text(c)!r} "
              f"bounds={attr(c,'bounds')}")
```

---

## 五、调试技巧

### 技巧 1：手动 dumpLayout 检查页面结构

当脚本找不到目标组件时，手动 dump 一次看看实际内容：

```bash
# 1. 在设备上导航到目标页面（手动或用脚本）
# 2. dump 当前布局
hdc shell uitest dumpLayout
# 输出: DumpLayout saved to:/data/local/tmp/layout_1735308093471.json

# 3. 拉取到本地
hdc file recv /data/local/tmp/layout_1735308093471.json layout.json

# 4. 用 Python 检查
python -c "import json; d=json.load(open('layout.json','r',encoding='utf-8')); print(json.dumps(d, ensure_ascii=False, indent=2)[:2000])"
```

### 技巧 2：搜索特定文本确认存在

```python
# 写一个小脚本搜索布局中的关键词
import json
d = json.load(open('layout.json', 'r', encoding='utf-8'))

def search(node, kw):
    if isinstance(node, dict):
        a = node.get('attributes', {})
        t = a.get('text', '')
        if kw in t:
            print(f"FOUND: text={t!r} type={a.get('type')} bounds={a.get('bounds')}")
        for c in node.get('children', []):
            search(c, kw)

search(d, '热点')
search(d, '开关')
search(d, '开启')
```

### 技巧 3：手动点击测试坐标是否正确

```bash
# 先 dump 获取 bounds
hdc shell uitest dumpLayout

# 用解析出的坐标手动点击测试
hdc shell uitest uiInput click 324 1549

# 观察设备是否正确跳转
```

### 技巧 4：截图辅助调试

```bash
# 截图保存到设备
hdc shell snapshot_display -f /data/local/tmp/screen.png
# 拉取到本地
hdc file recv /data/local/tmp/screen.png screen.png
```

### 技巧 5：在脚本中加 debug_dump

当目标组件未找到时，自动打印所有 Toggle 和相关组件信息：

```python
def debug_dump(layout):
    """调试输出"""
    toggles = find_toggles(layout)
    print(f"\n  [DEBUG] {len(toggles)} 个 Toggle:")
    for i, t in enumerate(toggles):
        print(f"    [{i}] text={get_text(t)!r} checked={attr(t,'checked','N/A')} "
              f"bounds={attr(t,'bounds')}")
    # 打印包含关键词的组件
    comps = find_by_text(layout, '热点')
    print(f"  [DEBUG] {len(comps)} 个包含'热点'的组件:")
    for i, c in enumerate(comps[:10]):
        print(f"    [{i}] type={attr(c,'type')} text={get_text(c)!r} "
              f"bounds={attr(c,'bounds')}")
```

---

## 六、常见问题与避坑指南

### 坑 1：包名错误

**现象**：`aa start` 报 `failed to get information`

**原因**：包名拼写错误。例如 `com.huawei.hmossettings`（少了个点）vs 正确的 `com.huawei.hmos.settings`

**解决**：
```bash
# 用 bm dump -a 列出所有包名，直接复制
hdc shell bm dump -a | findstr -i settings
```

### 坑 2：aa start 参数语法因版本而异

**现象**：报 `unknown option` 或参数不生效

**原因**：不同 HarmonyOS 版本的 `aa start` 参数格式不同

**解决**：先查帮助
```bash
hdc shell aa start --help
# 确认是 -a/-b 格式还是 -n 格式
```

### 坑 3：dumpLayout 文件路径不固定

**现象**：`hdc file recv` 报文件不存在

**原因**：`uitest dumpLayout` 输出的文件名带时间戳 `layout_<timestamp>.json`，不是固定的 `layout.json`

**解决**：从 stdout 解析实际路径
```python
m = re.search(r'saved to:\s*(/\S+\.json)', output)
remote_path = m.group(1) if m else default_path
```

### 坑 4：JSON 属性嵌套在 attributes 里

**现象**：所有 `comp.get('text')` 返回 None

**原因**：`dumpLayout` 的 JSON 结构中，属性不在节点顶层，而在 `node["attributes"]` 字典里

**解决**：用 `attr()` 函数统一访问
```python
def attr(comp, key, default=''):
    return comp.get('attributes', {}).get(key, default)
```

### 坑 5：页面加载太慢导致 dumpLayout 拿到旧页面

**现象**：点击后 dumpLayout 返回的还是上一个页面

**原因**：页面跳转需要时间，dumpLayout 执行太快

**解决**：增加等待时间
```python
click_by_text(layout, '移动网络', wait=3.0)  # 默认 2.5s，慢设备加到 3-4s
time.sleep(1)  # dumpLayout 前再等一下
layout = dump_layout()
```

### 坑 6：系统语言不是中文

**现象**：`find_by_text(layout, '移动网络')` 找不到

**原因**：设备系统语言为英文，文本是 `Mobile network`

**解决**：修改文本常量
```python
# 英文系统
TEXT_MOBILE_NETWORK = 'Mobile network'
TEXT_PERSONAL_HOTSPOT = 'Personal hotspot'

# 或先 dump 一次确认实际文本
```

### 坑 7：Toggle 和文本是两个独立组件

**现象**：找到了 Toggle 但 `get_text(toggle)` 返回空，无法确认是不是目标开关

**原因**：设置页面中，"个人热点"文本和开关 Toggle 是两个独立组件，Toggle 本身没有 text 属性

**解决**：用多策略匹配（见步骤 4 示例 5），按坐标距离关联文本和 Toggle

### 坑 8：屏幕息屏导致 UI 操作失败

**现象**：dumpLayout 返回空树或点击无反应

**原因**：设备屏幕已息屏

**解决**：
```bash
# 唤醒屏幕
hdc shell powermgr set screen on
# 或
hdc shell uitest systemInput keyEvent 2  # 按电源键
```

---

## 七、完整示例：查询蓝牙开关状态

以下是一个完整的、可直接运行的脚本示例，展示了上述所有步骤的整合：

```python
#!/usr/bin/env python3
"""查询 HarmonyOS 蓝牙开关状态：设置 > 蓝牙"""

import subprocess, json, os, re, sys, time, tempfile

_HDC = 'hdc'

def hdc_shell(*args, timeout=30):
    r = subprocess.run([_HDC, 'shell', *list(args)],
                       capture_output=True, text=True,
                       timeout=timeout, encoding='utf-8', errors='replace')
    return (r.stdout or '') + (r.stderr or '')

def dump_layout():
    output = hdc_shell('uitest', 'dumpLayout')
    time.sleep(1)
    m = re.search(r'saved to:\s*(/\S+\.json)', output)
    remote = m.group(1) if m else '/data/local/tmp/layout.json'
    local = os.path.join(tempfile.gettempdir(), 'hm_layout.json')
    subprocess.run([_HDC, 'file', 'recv', remote, local],
                   capture_output=True, timeout=15)
    with open(local, 'r', encoding='utf-8') as f:
        return json.load(f)

def attr(comp, key, default=''):
    a = comp.get('attributes')
    return a.get(key, default) if a else comp.get(key, default)

def get_text(comp):
    return attr(comp, 'text', '') or attr(comp, 'description', '') or ''

def find_components(node, pred, res=None):
    if res is None: res = []
    if isinstance(node, dict):
        if pred(node): res.append(node)
        for c in node.get('children', []):
            find_components(c, pred, res)
    elif isinstance(node, list):
        for i in node: find_components(i, pred, res)
    return res

def find_by_text(node, text):
    return find_components(node, lambda c: text in get_text(c))

def find_toggles(node):
    return find_components(node,
        lambda c: attr(c, 'type', '').lower() in ('toggle', 'switch'))

def parse_bounds(bounds):
    if isinstance(bounds, str):
        nums = re.findall(r'\d+', bounds)
        if len(nums) >= 4:
            return ((int(nums[0]) + int(nums[2])) // 2,
                    (int(nums[1]) + int(nums[3])) // 2)
    return None

def distance(p1, p2):
    if not p1 or not p2: return float('inf')
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

def click_by_text(layout, text, wait=2.5):
    comps = find_by_text(layout, text)
    if not comps: return False
    c = parse_bounds(attr(comps[0], 'bounds'))
    if not c: return False
    hdc_shell('uitest', 'uiInput', 'click', str(c[0]), str(c[1]))
    time.sleep(wait)
    return True

def read_toggle(comp):
    val = attr(comp, 'checked', None) or attr(comp, 'isOn', None)
    if val is True or val in ('true', 'True', 1, '1'): return 'on'
    if val is False or val in ('false', 'False', 0, '0'): return 'off'
    return 'unknown'

def find_toggle_for_text(layout, text):
    toggles = find_toggles(layout)
    for t in toggles:
        if text in get_text(t): return t
    text_comps = find_by_text(layout, text)
    if text_comps and toggles:
        tc = parse_bounds(attr(text_comps[0], 'bounds'))
        if tc:
            return min(toggles, key=lambda t: distance(tc, parse_bounds(attr(t, 'bounds'))))
    if len(toggles) == 1: return toggles[0]
    return None

def main():
    print("=" * 50)
    print("  蓝牙开关状态查询: 设置 > 蓝牙")
    print("=" * 50)

    # Step 1: 启动设置
    print("\n[1/3] 启动设置应用...")
    hdc_shell('aa', 'start',
              '-a', 'com.huawei.hmos.settings.MainAbility',
              '-b', 'com.huawei.hmos.settings')
    time.sleep(3)

    # Step 2: 点击「蓝牙」
    print("\n[2/3] 导航到「蓝牙」...")
    layout = dump_layout()
    if not click_by_text(layout, '蓝牙'):
        print("[FAIL] 未找到「蓝牙」入口")
        # 调试: 打印所有包含'蓝牙'的组件
        for c in find_by_text(layout, '蓝牙'):
            print(f"  type={attr(c,'type')} text={get_text(c)!r} bounds={attr(c,'bounds')}")
        return

    # Step 3: 查询开关状态
    print("\n[3/3] 查询蓝牙开关状态...")
    layout = dump_layout()
    toggle = find_toggle_for_text(layout, '蓝牙')

    print("\n" + "-" * 50)
    if toggle:
        state = read_toggle(toggle)
        print(f"  >>> 蓝牙开关: {state.upper()} <<<")
    else:
        print("  >>> 未找到蓝牙开关 <<<")
        # 调试输出
        toggles = find_toggles(layout)
        print(f"  [DEBUG] {len(toggles)} 个 Toggle:")
        for i, t in enumerate(toggles):
            print(f"    [{i}] text={get_text(t)!r} checked={attr(t,'checked','N/A')}")
    print("-" * 50)

if __name__ == '__main__':
    main()
```

---

## 八、开发流程速查表

| 步骤 | 做什么 | 关键命令/函数 |
|------|--------|---------------|
| 1. 查包名 | 确定目标应用的 bundleName 和 abilityName | `hdc shell bm dump -a \| findstr xxx` |
| 1. 查语法 | 确认 aa start 参数格式 | `hdc shell aa start --help` |
| 1. 启动应用 | 用正确参数启动 | `hdc shell aa start -a <ability> -b <bundle>` |
| 2. 获取布局 | dumpLayout + 解析路径 + file recv | `hdc shell uitest dumpLayout` |
| 2. 按文本点击 | 找到文本 → 解析 bounds → uiInput click | `click_by_text(layout, '文本')` |
| 2. 滑动页面 | 向上滑动滚动 | `hdc shell uitest uiInput swipe x1 y1 x2 y2` |
| 2. 返回上页 | 模拟返回键 | `hdc shell uitest systemInput keyEvent 2` |
| 3. 解析 JSON | 从 attributes 字典读属性 | `attr(comp, 'text')` |
| 4. 定位组件 | 按文本/类型/属性递归查找 | `find_by_text()`, `find_toggles()` |
| 4. 关联匹配 | 文本和 Toggle 是两个组件时按距离关联 | `find_toggle_for_text(layout, text)` |
| 5. 读状态 | 读取 checked/value/text 属性 | `read_toggle(comp)` |
| 调试 | 手动 dump 检查 | `hdc shell uitest dumpLayout` |
| 调试 | 截图 | `hdc shell snapshot_display -f <path>` |
