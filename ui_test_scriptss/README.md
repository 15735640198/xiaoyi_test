# HarmonyOS 个人热点开关状态查询脚本

通过 `hdc` + `uitest` 命令行工具，自动化导航到 **设置 > 移动网络 > 个人热点** 页面，查询"个人热点"开关的当前状态（开启/关闭）。

## 前置条件

### 1. 安装 hdc 工具

`hdc`（HarmonyOS Device Connector）随 **DevEco Studio** 或 **HarmonyOS SDK** 附带。

#### 方式一：安装 DevEco Studio（推荐）

1. 访问 [华为开发者下载中心](https://developer.huawei.com/consumer/cn/download/) 下载 DevEco Studio
2. 安装完成后，hdc 位于：
   ```
   <DevEco Studio 安装目录>\sdk\<版本号>\openharmony\toolchains\hdc.exe
   ```
   示例：`D:\DevEco Studio\sdk\4.1.0.600\openharmony\toolchains\hdc.exe`

#### 方式二：仅安装 HarmonyOS SDK 命令行工具

如果不想装完整 IDE，可以在 DevEco Studio 下载页选择「Command Line Tools」单独安装 SDK。

#### 配置 PATH

将 hdc 所在目录加入系统环境变量 PATH，然后新开终端验证：

```bash
hdc version
# 输出: Ver: 2.0.0a
```

> **注意**：配置 PATH 后必须**重新打开终端窗口**才能生效。

如果未配置 PATH，也可以临时使用——每次运行脚本时指定 hdc 路径，脚本会自动搜索常见的 SDK 安装路径。

### 2. 连接 HarmonyOS 设备

**USB 连接**：用数据线连接设备与电脑，在设备上开启"开发者选项"和"USB 调试"。

**WiFi 连接**（可选）：

```bash
hdc tmode port 12345          # 设备端开启 TCP 监听
hdc connect 192.168.1.100:12345  # 电脑端连接设备 IP
```

确认设备已连接：

```bash
hdc list targets
```

输出类似以下内容表示连接成功：

```
192.168.1.100:12345
```

若输出 `[Empty]` 说明没有设备连接。

### 3. Python 环境

需要 Python 3.8+（无需安装第三方库，仅使用标准库）。

```bash
python --version
```

## 使用方法

### 基本用法

```bash
python query_personal_hotspot_state.py
```

脚本会自动完成以下操作：

```
[1/4] 启动设置应用
[2/4] 导航到「移动网络」    ← dumpLayout 找到文本，uiInput click 点击
[3/4] 导航到「个人热点」    ← 同上
[4/4] 查询个人热点开关状态  ← dumpLayout 解析 Toggle 组件 checked 属性
```

### 输出示例

**成功查询：**

```
=======================================================
  HarmonyOS 个人热点开关状态查询
  路径: 设置 > 移动网络 > 个人热点
=======================================================
  hdc 可用: Ver: 5.0.x.xxx
  已连接设备: 192.168.1.100:12345

[1/4] 启动设置应用...

[2/4] 导航到「移动网络」...
  -> 找到 '移动网络' (共 1 个匹配)
  -> 点击坐标 (540, 820)

[3/4] 导航到「个人热点」...
  -> 找到 '个人热点' (共 1 个匹配)
  -> 点击坐标 (540, 1100)

[4/4] 查询个人热点开关状态...

-------------------------------------------------------
  >>> 个人热点开关状态: 已关闭 (OFF) <<<
-------------------------------------------------------
```

**查询失败（附带调试信息）：**

```
[4/4] 查询个人热点开关状态...

  >>> 未找到个人热点开关 <<<

  [DEBUG] 找到 3 个 Toggle/Switch:
    [0] type=Toggle text='个人热点' checked=True bounds=[800,300][900,350]
    [1] type=Toggle text='' checked=False bounds=[800,500][900,550]
    [2] type=Toggle text='' checked=False bounds=[800,700][900,750]

  [DEBUG] 找到 2 个包含'热点'的组件:
    [0] type=Text text='个人热点' bounds=[100,300][700,350]
    [1] type=Text text='热点设置' bounds=[100,900][700,950]
```

根据调试信息可以手动确认开关位置和属性名。

## 配置说明

脚本顶部的配置区：

```python
# 设置应用候选包名（会依次尝试）
SETTINGS_CANDIDATES = [
    ('com.huawei.hmossettings', 'entry', 'EntryAbility'),
    ('com.huawei.hmossettings', None,    'EntryAbility'),
    ('com.huawei.hmossettings', 'entry', 'MainAbility'),
    ('com.huawei.hmossettings', None,    'MainAbility'),
    ('com.android.settings',    None,    'Settings'),
]

TEXT_MOBILE_NETWORK = '移动网络'    # 移动网络入口文本
TEXT_PERSONAL_HOTSPOT = '个人热点'  # 个人热点入口文本
NAV_WAIT = 2.5                     # 页面跳转等待秒数
DUMP_WAIT = 1.0                    # dumpLayout 后等待秒数
```

### 需要调整的常见情况

| 情况 | 修改方式 |
|------|----------|
| 设置应用包名不同 | 将正确包名加入 `SETTINGS_CANDIDATES` 列表，可用以下命令确认：`hdc shell bm dump -a \| grep -i settings` |
| Ability 名不同 | 同样加入候选列表，常见值: `EntryAbility`、`MainAbility` |
| 设备性能较慢，页面加载慢 | 增大 `NAV_WAIT`（如改为 4.0） |
| dumpLayout 响应慢 | 增大 `DUMP_WAIT`（如改为 2.0） |
| 系统语言为英文 | 改为 `TEXT_MOBILE_NETWORK = 'Mobile network'`、`TEXT_PERSONAL_HOTSPOT = 'Personal hotspot'` |
| 脚本未找到 hdc | 在 `HDC_COMMON_PATHS` 中添加实际 SDK 安装路径 |

## 工作原理

```
┌──────────────────────────────────────────────────────────┐
│  hdc shell uitest dumpLayout                             │
│  → 设端生成 /data/local/tmp/layout.json (控件树 JSON)     │
│  → hdc file recv 拉取到本地                               │
│  → Python json.load 解析                                  │
├──────────────────────────────────────────────────────────┤
│  控件查找: 递归遍历 JSON 树                               │
│    find_by_text()  → 按 text/accessibilityText 匹配       │
│    find_toggles()  → 按 type=Toggle/Switch 匹配           │
│    parse_bounds()  → 从 "[l,t][r,b]" 提取中心坐标         │
├──────────────────────────────────────────────────────────┤
│  点击导航: hdc shell uitest uiInput click <x> <y>        │
├──────────────────────────────────────────────────────────┤
│  状态判断: 读取 Toggle 组件的 checked / isOn 属性         │
│    True / "true" / 1  → ON                               │
│    False / "false" / 0 → OFF                            │
└──────────────────────────────────────────────────────────┘
```

### Toggle 状态匹配策略

脚本按优先级依次尝试 4 种策略，任一命中即返回结果：

1. **Toggle 自身包含"个人热点"文本** → 直接读 `checked`
2. **离"个人热点"文本最近的 Toggle** → 坐标曼哈顿距离最小
3. **带 `checked`/`isOn` 属性且靠近目标文本的组件**
4. **页面仅有一个 Toggle** → 直接返回其状态

## 常见问题

### Q: 提示 "未找到 hdc 工具"

**原因**：hdc 不在 PATH 中，且默认安装路径搜索也未找到。

**解决**：
1. 确认已安装 DevEco Studio（[下载地址](https://developer.huawei.com/consumer/cn/download/)）
2. 找到 SDK 安装目录，例如 `D:\DevEco Studio\sdk\4.1.0.600\openharmony\toolchains\`
3. 将 toolchains 目录添加到系统环境变量 PATH
4. **必须重新打开终端**，然后运行 `hdc version` 验证
5. 如果仍不行，在脚本 `HDC_COMMON_PATHS` 列表中手动添加实际路径

### Q: 启动设置应用失败，所有候选包名均尝试失败

`aa start` 命令语法格式为：
```
hdc shell aa start -n <bundleName> [-m <moduleName>] <abilityName>
```

- `-n`：指定应用包名（此前脚本误写为 `-b`，已修正）
- `-m`：指定 module 名（可选，通常为 `entry`）
- 最后一个参数是 Ability 名（不带前缀标志）

**排查步骤**：
1. 手动执行确认设上的包名：
   ```bash
   hdc shell bm dump -a | grep -i "settings\|设置"
   ```
2. 将匹配到的包名/Module/Ability 加入 `SETTINGS_CANDIDATES`
3. 手动测试启动命令：
   ```bash
   hdc shell aa start -n <包名> [-m <module名>] <Ability名>
   ```

### Q: 还是不行，不想折腾启动命令

**绕过方案**：先手动在设备上打开「设置」应用并导航到个人热点页面，然后修改脚本跳过 Step 1-3，直接从 Step 4 开始：

```python
# 在 main() 函数中注释掉启动设置和导航的代码：
# Step 1, 2, 3 全部注释掉...
# 直接从 Step 4 开始:
print("\n[4/4] 查询个人热点开关状态...")
layout = dump_layout()
# ...
```

### Q: 提示 "未检测到已连接的设备"

- USB 连接：检查数据线是否支持数据传输，确认已开启 USB 调试
- WiFi 连接：确认设备和电脑在同一局域网，重新执行 `hdc connect`
- 多设备连接时脚本默认使用第一个，可用 `hdc -t <设备ID> shell` 指定

### Q: 提示 "未找到「移动网络」入口"

- 系统语言非中文：修改配置区的文本为对应语言
- 页面未加载完成：增大 `NAV_WAIT`
- 用 `hdc shell uitest dumpLayout` 手动 dump 一次，检查实际文本是否包含"移动网络"

### Q: 提示 "未找到个人热点开关"

- 查看调试输出中的 Toggle 列表，确认开关的属性名
- 部分版本 Toggle 状态属性可能不叫 `checked`/`isOn`，需根据调试信息调整 `_check_state()` 函数
- 确认已正确进入个人热点页面（而非停留在移动网络页面）

### Q: 脚本运行中途卡住

- 设备息屏会导致 UI 操作失败，建议保持屏幕常亮
- 可按 Ctrl+C 中断，重新运行
- 增加 `NAV_WAIT` 和 `DUMP_WAIT` 的等待时间

## 文件说明

```
query_personal_hotspot_state.py   主脚本
README.md                         本说明文档
```

## 参考文档

- [UI测试框架使用指导](https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/uitest-guidelines) - HarmonyOS 官方文档
- [@ohos.UiTest API 参考](https://developer.huawei.com/consumer/cn/doc/harmonyos-references/js-apis-uitest) - API 详细说明
