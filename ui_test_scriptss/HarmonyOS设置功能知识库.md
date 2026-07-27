# HarmonyOS 设置功能知识库

> 设备型号: Pura X 典藏版 | 系统: HarmonyOS NEXT | 语言: 中文
> 生成方式: 自动遍历设置所有页面（每页滚动 3 屏采集） + 人工补充
> 更新日期: 2025-06-29 (v5: 章节重编号, 一至十五连续编号, 去除 A/B/C 后缀; v4: 补充 Slider 操作、选择器交互、第三级页面全覆盖、安全认证门、跨设置依赖、页面加载时间、异常场景、控制中心操作)
> 用途: 作为 AI 生成设置操作脚本时的上下文知识库

---

## 一、环境信息

### 1.1 hdc 工具

| 项 | 值 |
|----|-----|
| hdc 路径 | `D:\lzs\devecostudio-windows-6.1.1.280\DevEco Studio\sdk\default\openharmony\toolchains\hdc.exe` |
| 验证命令 | `hdc version` → 输出 `Ver: 3.2.0d` |
| 设备序列号 | `3UJ0225328003793` |

### 1.2 设置应用

| 项 | 值 |
|----|-----|
| 包名 (bundleName) | `com.huawei.hmos.settings` |
| Ability 名 | `com.huawei.hmos.settings.MainAbility` |
| 启动命令 | `hdc shell aa start -a com.huawei.hmos.settings.MainAbility -b com.huawei.hmos.settings` |
| aa start 语法 | `aa start -a <abilityName> -b <bundleName> [-m <moduleName>]` |

### 1.3 uitest 命令行

| 命令 | 用途 | 输出 |
|------|------|------|
| `hdc shell uitest dumpLayout` | 获取控件树 JSON | `DumpLayout saved to:/data/local/tmp/layout_<timestamp>.json` |
| `hdc shell uitest uiInput click <x> <y>` | 点击坐标 | `No Error` |
| `hdc shell uitest uiInput swipe <x1> <y1> <x2> <y2>` | 滑动 | `No Error` |
| `hdc shell uitest uiInput keyEvent Back` | 返回键 | `No Error` |
| `hdc shell uitest uiInput keyEvent Home` | 主页键 | `No Error` |

### 1.4 控件树 JSON 结构

```
{
  "attributes": {                          ← 属性嵌套在 attributes 字典里
    "type": "RootFrame",                   ← 组件类型: Text/Toggle/Button/Row/Slider/...
    "text": "设置",                         ← 显示文本
    "description": "标题",                  ← 无障碍描述
    "bounds": "[0,0][1320,2772]",          ← 坐标: [left,top][right,bottom]
    "checked": "true",                     ← Toggle 状态 (仅 Toggle/Switch 有)
    "clickable": "true",                   ← 是否可点击
    "enabled": "true"                      ← 是否启用
  },
  "children": [ ... ]                      ← 子组件
}
```

**关键注意**:
- 属性在 `node["attributes"]` 中，不是顶层 → 用 `attr(node, key)` 函数访问
- `bounds` 格式为字符串 `"[left,top][right,bottom]"`，中心点 = `((left+right)/2, (top+bottom)/2)`
- Text 组件通常 `clickable=false`，真正可点击的是父级 Row → 点击时需找包含目标文本中心点的最小可点击组件
- `dumpLayout` 文件名带时间戳 → 从 stdout 解析路径: `re.search(r'saved to:\s*(/\S+\.json)', output)`

---

## 二、设置首页菜单项（共 24 项）

从上到下的完整列表:

| 序号 | 菜单文本 | 类别 | 备注 |
|------|----------|------|------|
| 1 | 仓颉编程语言小助手 | 账号 | 华为账号入口 |
| 2 | 云空间 | 账号 | |
| 3 | 查找设备 | 账号 | |
| 4 | WLAN | 网络 | 显示当前 WiFi 名 |
| 5 | 星闪和蓝牙 | 网络 | 含 Toggle |
| 6 | 移动网络 | 网络 | 含 Toggle |
| 7 | 卫星网络 | 网络 | |
| 8 | 多设备协同 | 互联 | |
| 9 | 桌面、外屏和个性化 | 个性化 | |
| 10 | 显示和亮度 | 显示 | 含 Toggle |
| 11 | 声音和振动 | 声音 | |
| 12 | 通知和状态栏 | 通知 | 含 Toggle |
| 13 | 情景模式 | 情景 | 含 Toggle |
| 14 | 系统 | 系统 | 含 Toggle |
| 15 | 应用和元服务 | 系统 | |
| 16 | 健康使用设备 | 系统 | |
| 17 | 关怀和无障碍 | 系统 | |
| 18 | 存储 | 系统 | |
| 19 | 电池 | 系统 | 含 Toggle |
| 20 | 生物识别和密码 | 安全 | 含 Toggle |
| 21 | 隐私和安全 | 安全 | |
| 22 | 小艺 | 智能 | |
| 23 | 畅连通信 | 通信 | |
| 24 | (关于手机) | 系统 | 在"系统"子页面内 |

---

## 三、各设置子页面详细结构

### 3.1 WLAN

- **导航路径**: 设置 > WLAN
- **入口文本**: `WLAN`
- **滑动需求**: 4 屏（WiFi 列表可很长）
- **子项**:

| 子项 | 形态 | 状态/操作说明 |
|------|------|------------|
| WLAN | toggle_row | checked → ON/OFF |
| 可用 WLAN | section_header | — |
| <WiFi 名称> | nav_item | 旁有"已连接"=当前连接 |
| 其他 WLAN | section_header | — |
| 添加其他网络 | nav_item | — |
| WLAN 安全检测 | toggle_row | checked → ON/OFF |

#### 3.1.1 WiFi 连接流程

WiFi 列表项为 `Row` (clickable=true), 内含 WiFi 名称 Text + 状态 Text ("已连接"/"已保存"/"加密"/"开放").
点击 WiFi 名称后的行为取决于网络状态:

| 场景 | 点击后行为 | 处理方法 |
|------|----------|---------|
| 已连接 | 进入详情页 (有"断开连接"/"删除该网络") | `find_by_text(layout, '断开连接')` 检测, 返回已连接 |
| 已保存 (密码保留) | 自动连接, 无弹窗 | 无需操作, 等待验证 |
| 已保存 (开放网络) | 自动连接, 无弹窗 | 无需操作, 等待验证 |
| 新加密网络 | 弹出密码输入弹窗 | TextInput(hint="密码") + `uitest uiInput text <密码>` + 点"连接"按钮 |

**密码输入弹窗结构**:
- 标题: WiFi 名称
- TextInput: hint="密码", 在页面上半部 (center≈(660, 465))
- "隐私" + "使用随机 MAC" 选项
- "高级选项" 可展开
- "连接" 按钮 (Text, clickable=false, 在 Button 内)

**连接验证**: 等待 5s 后 dump layout, 检查 WiFi 名称旁是否有"已连接"文本

**API**: `connect_wlan(ssid, password)` → `(success, message)`

---

### 3.2 星闪和蓝牙

- **导航路径**: 设置 > 星闪和蓝牙
- **入口文本**: `星闪和蓝牙`（注意: 不是"蓝牙"！）
- **入口状态**: 右侧显示 `已开启` 或无文本
- **子项**:

| 子项 | 形态 | 状态/操作说明 | 备注 |
|------|------|------------|------|
| 星闪 | toggle_row | checked=true → ON | |
| 蓝牙 | toggle_row | checked=true → ON | |
| 设备名称 | nav_item | 点击修改名称 | |
| 已配对设备 | section_header | — | 下方是已配对设备列表 |
| <设备名> | nav_item | 旁边有"已连接"文本=已连接 | 点击连接/断开 |
| 其他设备 | section_header | — | 下方是未配对设备列表 |
| <设备名> | nav_item | 点击发起配对 | Text不可点击，需点父级Row |

- **弹窗处理**:
  - 配对新设备时弹配对确认框，有 `配对` 和 `取消` 按钮
  - 配对失败弹提示框，有 `确定` 按钮
- **关键注意**:
  - 设备名 Text `clickable=false`，需点击父级 Row
  - `find_by_text('配对')` 会匹配到"已配对设备" → 用 `find_button()` 排除含"设备"的长文本
  - 设备列表加载需要时间，打开页面后等 5s 再搜索
  - 滑动查找后等 2s 列表刷新
  - 设备详情页（点齿轮图标进入）只有 `取消配对`，无连接/断开按钮

---

### 3.3 移动网络

- **导航路径**: 设置 > 移动网络
- **入口文本**: `移动网络`
- **子项**:

| 子项 | 形态 | 状态/操作说明 | 备注 |
|------|------|------------|------|
| 飞行模式 | toggle_row | checked → ON/OFF | |
| 移动数据 | nav_item | 进入子页面 | |
| SIM 卡管理 | nav_item | 进入子页面 | |
| 个人热点 | nav_item | 进入子页面（见下方） | |
| 流量管理 | nav_item | 进入子页面 | |
| 网络加速 | nav_item | — | |
| 国际上网服务 | nav_item | — | |
| VPN | nav_item | — | |

#### 3.3.2 SIM 卡管理子页面

- **导航路径**: 设置 > 移动网络 > SIM 卡管理
- **入口文本**: `SIM 卡管理`

| 子项 | 形态 | 状态/操作说明 |
|------|------|------------|
| 卡 1 | text_value + toggle_row | 右侧"未插卡"或运营商名称; 卡槽旁有 Toggle 控制启用/禁用 |
| 卡 2 | text_value + toggle_row | 右侧"未插卡"或运营商名称; 卡槽旁有 Toggle 控制启用/禁用 |
| 双卡上网 | 分区标题 | — |
| 默认移动数据 | button_selected | 右侧两个 Button("卡 1"/"卡 2"), Button 的 selected=true 表示当前选中 |
| 双卡通话 | 分区标题 | — |
| 默认拨号卡 | text_value | 右侧"不设置"或卡号 |
| 高级 | 分区标题 | — |
| SIM 卡保护 | nav_item | — |
| 天际通服务 | nav_item | — |
| 国际上网服务 | nav_item | — |

**默认移动数据 (button_selected 形态)**:
- "默认移动数据" Text 在左侧, 右侧 Stack 内有两个 Button
- Button 的 text 属性为空, 内含 Column → Text("卡 1"/"卡 2")
- `selected=true` 的 Button 是当前默认数据卡
- 查询: `query_default_data_card()` → '卡 1' | '卡 2'

#### 3.3.1 个人热点子页面

- **导航路径**: 设置 > 移动网络 > 个人热点
- **入口文本**: `个人热点`
- **子项**:

| 子项 | 形态 | 状态/操作说明 |
|------|------|------------|
| 个人热点 | toggle_row | Toggle checked → ON/OFF；Toggle 无文本，id=`...hotspot_switch_setting.result` |
| 设备名称 | text_value | 右侧显示热点名称；点击弹出对话框（TextInput + "确定"按钮） |
| 密码 | text_value | 右侧显示密码明文；点击弹出对话框（TextInput + "确定"按钮） |
| 已连接设备 | text_value | 右侧显示连接数（如"0 台"），id=`...connected_device_entry.result` |
| 更多共享设置 | nav_item | 子页面: 单次流量限制(text_value) + AP频段(text_value, id=`...ApBand.UpdateApBand.result`) + USB共享网络(toggle_row, id=`...hotspot_device_usb.result`) |
| 关于 | nav_item | — |

- **加密方式**: 不在页面上，HarmonyOS 热点加密固定为 WPA2-PSK，不可配置
- **状态判断**: Toggle 的 `checked` 属性
- **关键注意**: Toggle 可能与"个人热点"文本是两个独立组件，需按坐标距离关联匹配
- **USB 共享网络限制**: 开启 USB 共享网络会切换 USB 连接模式，导致 hdc 的 USB 调试连接立即断开。`set_usb_tethering('on')` 点击后无法在同一会话中验证结果，函数在连接断开时返回 `(True, 'on')` 表示点击已执行。关闭操作不受此限制，但前提是设备已重新连接。

**文本输入方法**（设置名称/密码时使用）:
1. 点击 text_value 项 → 弹出对话框，含 TextInput（type=TextInput）+ "确定"按钮
2. 长按 TextInput → 显示上下文菜单（SelectMenuButtonText 类型: 剪切/复制/全选/自动填充/翻译/分享）
3. 点击"全选" → 选中文本框全部内容
4. `uitest uiInput text <新文本>` → 替换选中的文本
5. 点击"确定" → 保存

#### 3.3.3 网络加速子页面

- **导航路径**: 设置 > 移动网络 > 网络加速
- **入口文本**: `网络加速` (需滑动 1-2 屏)
- **子项**:

| 子项 | 形态 | 状态/操作说明 |
|------|------|------------|
| 允许使用移动数据加速网络 | toggle_row | checked → ON/OFF |
| 允许使用云加速 | toggle_row | checked → ON/OFF |
| 拥塞加速 | text/nav_item | 需进一步探索 |
| 移动网络专线加速 | text/nav_item | 需进一步探索 |

- **API**: `query_network_acceleration()` / `set_network_acceleration('on'/'off')`
- **注意**: 无"视频加速模式"选项, 实际开关名为"允许使用移动数据加速网络"

#### 3.3.4 流量管理子页面

- **导航路径**: 设置 > 移动网络 > 流量管理
- **入口文本**: `流量管理` (需滑动 1-2 屏)
- **子项**:

| 子项 | 形态 | 状态/操作说明 |
|------|------|------------|
| 应用联网 | nav_item | 进入应用联网设置：两个标签（移动数据/WLAN），每个标签下有"全部"Toggle + 各应用Toggle，Toggle checked → ON/OFF；应用名 Text 与 Toggle 按 Y 坐标匹配（dy<80）；列表按字母排序，可滚动 |
| 本月数据流量排行 | section_header + "更多"按钮 | 点击"更多"进入流量排行页：两个标签(移动数据/WLAN)，WLAN标签下有应用列表(ListItem=应用名+流量值)，点击应用进入详情页(大数字+单位+"已使用流量"，时间选择器"最近30天/最近24小时"为MenuItem弹窗) |

- **注意**: 无"剩余流量"信息。剩余流量是运营商业务数据，不在设置 App 中显示。

---

### 3.4 卫星网络

- **导航路径**: 设置 > 卫星网络
- **入口文本**: `卫星网络`
- **滑动需求**: 2 屏
- **子项** (4 项):

| 子项 | 形态 | 状态/操作说明 |
|------|------|------------|
| 天通卫星通信 | button | 按钮文本判断状态 |

---

### 3.5 多设备协同

- **导航路径**: 设置 > 多设备协同
- **入口文本**: `多设备协同`
- **子项** (完整 15 项):

| 子项 | 类型 | 状态显示方式 |
|------|------|------------|
| 华为分享 | 导航项 | 右侧"仅分享过的设备可见" |
| 接续 | 导航项 | 右侧"已开启" |
| 跨设备剪贴板 | 导航项 | 右侧"已开启" |
| 跨设备互通 | 导航项 | 右侧"已开启" |
| 键鼠共享 | 导航项 | 右侧"已开启" |
| 多屏协同 | 导航项 | — |
| 超级终端 | 导航项 | 右侧"已开启" |
| 无线投屏 | 导航项 | 右侧"已开启" |
| 超级桌面 | 导航项 | 右侧"未连接" |
| HUAWEI HiCar | 导航项 | 右侧"未连接" |
| HUAWEI HiPlay | 导航项 | 右侧"已开启" |
| NFC | 导航项 | 右侧"已开启" |
| 通信共享 | 导航项 | — |
| 高级 | 导航项 | — |

- **状态判断**: 右侧文本"已开启"/"未开启"/"未连接"

---

### 3.6 桌面、外屏和个性化

- **导航路径**: 设置 > 桌面、外屏和个性化
- **入口文本**: `桌面、外屏和个性化`
- **滑动需求**: 2 屏
- **子项** (12 项):

| 子项 | 形态 | 状态/操作说明 |
|------|------|------------|
| 当前主题 | button | 显示当前主题名 |
| 查看主题 | button | — |
| 更多主题 | button | — |
| 应用 | button | — |

---

### 3.7 显示和亮度

- **导航路径**: 设置 > 显示和亮度
- **入口文本**: `显示和亮度`
- **Toggle 数**: 3 个
- **子项** (完整 19 项):

| 子项 | 形态 | 状态/操作说明 |
|------|------|------------|
| 显示模式 | text_value | 右侧"浅色"/"深色" |
| 深色模式 | text_value | 右侧"已关闭"/"已开启" |
| 自动调节 | toggle_row | checked → ON/OFF |
| 护眼模式 | text_value | 右侧"已关闭"/"已开启" |
| 电子书模式 | nav_item | 进入子页面 |
| 字体大小和界面缩放 | nav_item | 进入子页面（见下） |
| 休眠 | text_value | 右侧"10 分钟后" |
| 注视屏幕不熄屏 | toggle_row | checked → ON/OFF |
| 色彩调节与色温 | nav_item | 进入子页面 |
| 智能分辨率 | toggle_row | checked → ON/OFF |
| 屏幕刷新率 | text_value | 右侧"智能" |
| 高级设置 | nav_item | 进入子页面 |

**子页面: 字体大小和界面缩放**

- **导航路径**: 设置 > 显示和亮度 > 字体大小和界面缩放
- **页面结构**: 预览文本 + 3 个设置项，每项为 标签(text_value) + 下方 Slider

| 子项 | 形态 | 档位 | 右侧文本值 | 备注 |
|------|------|------|-----------|------|
| 字体大小 | text_value + slider | 4 档 (0%/25%/50%/75%) | 小/标准/大/超大 | 设为超大时弹出"设置更大字体"弹窗，需点取消 |
| 字体粗细 | text_value + slider | 3 档 (0%/50%/100%) | 最细/标准/最粗 | slider 在 label 下方，track click 无效需 swipe |
| 显示大小缩放 | text_value + slider | — | 默认/— | 未详细探查 |

**字体粗细 slider 注意**: label 和 slider 的 Y 差约 132px，但上方相邻的字体大小 slider 也在 200px 内，`find_by_text_nearest` + Y 匹配会误匹配到字体大小 slider。需找 label **下方**的 slider。且字体粗细 slider 不响应 track click，需用 `uitest uiInput swipe` 拖动。

---

### 3.8 声音和振动

- **导航路径**: 设置 > 声音和振动
- **入口文本**: `声音和振动`
- **Toggle 数**: 7 个
- **子项** (完整 32 项):

| 子项 | 形态 | 状态/操作说明 |
|------|------|------------|
| 来电铃声 | nav_item | 进入铃声选择页 |
| 信息铃声 | text_value | 右侧显示铃声名 |
| 通知铃声 | text_value | 右侧显示铃声名 |
| 声音模式 | text_value | 右侧"响铃"/"振动"/"静音" |
| 铃声音量 | slider_row | 读 value 属性 |
| 闹钟音量 | slider_row | 读 value 属性 |
| 媒体音量 | slider_row | 读 value 属性 |
| 通话音量 | slider_row | 读 value 属性 |
| 小艺音量 | slider_row | 读 value 属性 |
| 音量键默认控制 | text_value | 右侧"媒体音量" |
| 开机铃声 | toggle_row | checked → ON/OFF |
| 锁屏提示音 | toggle_row | checked → ON/OFF |
| 截屏提示音 | toggle_row | checked → ON/OFF |
| 通话智能降噪 | toggle_row | checked → ON/OFF |
| 立体声增强 | toggle_row | checked → ON/OFF |
| 响铃时振动 | toggle_row | checked → ON/OFF |
| 系统触感反馈 | toggle_row | checked → ON/OFF |

---

### 3.9 通知和状态栏

- **导航路径**: 设置 > 通知和状态栏
- **入口文本**: `通知和状态栏`
- **Toggle 数**: 9 个（每个应用一个 Toggle）
- **子项** (完整 27 项):

| 子项 | 形态 | 状态/操作说明 |
|------|------|------------|
| 状态栏 | nav_item | 进入子页面 |
| 实况窗 | nav_item | 进入子页面 |
| 通知管理 | nav_item | 进入子页面 |
| 锁屏通知 | nav_item | 进入子页面 |
| 横幅通知 | nav_item | 进入子页面 |
| 桌面角标 | nav_item | 进入子页面 |
| 优先通知 | nav_item | 进入子页面 |
| <应用名> | toggle_row | checked → ON(允许通知)/OFF(禁止通知) |
| 华为账号 | toggle_row | checked → ON/OFF |

- **状态判断**: 每个应用旁有 Toggle，`checked=false` 表示已关闭通知，`checked=true` 表示已开启
- **已关闭通知的应用**: 显示"已关闭通知"文本

---

### 3.10 情景模式

- **导航路径**: 设置 > 情景模式
- **入口文本**: `情景模式`
- **Toggle 数**: 2 个
- **子项** (完整 24 项):

| 子项 | 形态 | 状态/操作说明 |
|------|------|------------|
| 睡眠模式 | button_card | 按钮文本"立即开启"=off |
| 免打扰 | button_card | 按钮文本"立即开启"=off |
| 推荐开启与关闭 | toggle_row | checked → ON/OFF |
| 重要信息提醒 | toggle_row | checked → ON/OFF |
| 应用和元服务 | text_value | 右侧"未选择" |
| 联系人 | text_value | 右侧"仅允许收藏联系人" |
| 深色模式(关联) | text_value | 右侧"不关联" |
| 护眼模式(关联) | text_value | 右侧"不关联" |

- **状态判断**:
  - 情景模式开关: 右侧文本"已关闭"/条件开启时间
  - 推荐功能: Toggle `checked` 属性
  - 重要信息提醒: Toggle `checked` 属性

---

### 3.11 系统

- **导航路径**: 设置 > 系统
- **入口文本**: `系统`
- **Toggle 数**: 1 个
- **子项** (完整 30 项):

| 子项 | 形态 | 状态/操作说明 |
|------|------|------------|
| 语言和地区 | nav_item | — |
| 日期和时间 | text_value | 右侧"地区: 中国"+日期 |
| 系统导航 | nav_item | — |
| 输入法 | nav_item | — |
| 字体安装和管理 | nav_item | — |
| 快捷启动和手势 | nav_item | — |
| 智感握姿 | text_value | 右侧"已开启" |
| 单手兼容模式 | nav_item | — |
| 防误触模式 | toggle_row | checked → ON/OFF |
| 应用助手 | nav_item | — |
| 应用分身 | nav_item | — |
| 中转站 | nav_item | — |
| 智慧多窗 | nav_item | — |
| 智感支付 | text_value | 右侧"已关闭" |
| 智感扫码 | nav_item | — |
| SOS 紧急求助 | nav_item | — |
| 应急预警通知 | nav_item | — |
| 出行护航 | nav_item | — |
| 数据克隆 | nav_item | — |
| 备份和恢复 | nav_item | — |
| 重置 | nav_item | — |
| 定时开关机 | nav_item | — |
| **开发者选项** | nav_item | **存在=开发者模式已开启** |
| 用户体验改进计划 | nav_item | — |
| 认证标志 | nav_item | — |

- **开发者模式判断**: 「开发者选项」入口可见 = 已开启；不可见 = 未开启
- **注意**: 子页面较长，需滑动 2 次才能看到底部"开发者选项"

#### 3.11.1 语言和地区子页面

- **导航路径**: 设置 > 系统 > 语言和地区
- **入口文本**: `语言和地区`

| 子项 | 形态 | 状态/操作说明 |
|------|------|------------|
| 语言 | section_header + "编辑"按钮 | 右侧有"编辑"Text (非语言名) |
| <当前语言名> | Text (在"语言"下方) | 如"简体中文", 在标题下方而非右侧 |
| 添加语言 | nav_item (Column clickable) | 点击进入语言列表 |
| 地区 | section_header | — |
| 当前地区 | text_value | 右侧"中国" |

**语言名读取注意**: 语言名在"语言"标题**下方** (y 差 50-200px), 不是右侧 (右侧是"编辑"按钮)。`read_text_value_raw` 会误读"编辑", 需在下方查找。

**添加语言子页面**:
- "已添加语言" section: 显示已添加的语言 (Column clickable)
- "所有语言" section: 可选语言列表 (Column clickable)
- 每项: 中文名 + 原文 (如 "英语 / English", "繁体中文 / 繁體中文")
- 点击语言项 → 添加到已添加列表
- **设为默认需拖拽排序**: 点击"编辑"→长按拖拽到顶部, uitest 不支持此操作

**API**: `query_system_language()` / `add_system_language(lang)`

#### 3.11.2 输入法子页面

- **导航路径**: 设置 > 系统 > 输入法
- **入口文本**: `输入法`

| 子项 | 形态 | 状态/操作说明 |
|------|------|------------|
| 输入法管理 | section_header | 不可点击 |
| 默认输入法 | text_value | 右侧显示当前输入法名 (如"小艺输入法") |
| <输入法名> | nav_item (Column clickable) | 点击进入输入法设置 |

**注意**:
- 无"添加输入法"入口。输入法作为独立 App 安装, 安装后自动出现在列表中。
- 切换默认输入法: 点击"默认输入法"行 → 可能弹出选择器 (仅已安装输入法可选)
- **API**: `query_default_input_method()`

---

### 3.12 应用和元服务

- **导航路径**: 设置 > 应用和元服务
- **入口文本**: `应用和元服务`
- **滑动需求**: 4 屏
- **子项** (37 项):

| 子项 | 形态 | 状态/操作说明 |
|------|------|------------|
| 应用/元服务 | button | Tab 切换 |
| <应用名>（备忘录/查找设备/电子邮件等） | nav_item | 点击进入应用信息页 |

---

### 3.13 健康使用设备

- **导航路径**: 设置 > 健康使用设备
- **入口文本**: `健康使用设备`
- **滑动需求**: 2 屏
- **子项** (7 项):

| 子项 | 形态 | 状态/操作说明 |
|------|------|------------|
| 健康使用设备 | nav_item | 进入使用统计 |
| 取消 | button | 首次进入需同意条款，有"取消"按钮 |

---

### 3.14 关怀和无障碍

- **导航路径**: 设置 > 关怀和无障碍
- **入口文本**: `关怀和无障碍`
- **子项** (完整 26 项，分 3 大类):

| 分类 | 子项 | 类型 | 状态显示方式 |
|------|------|------|------------|
| — | 关怀模式 | 导航项 | 右侧"已关闭" |
| 视觉辅助 | 屏幕朗读 | 导航项 | 右侧"已关闭" |
| 视觉辅助 | 放大手势 | 导航项 | 右侧"已关闭" |
| 视觉辅助 | 高对比度文字 | 导航项 | 右侧"已关闭" |
| 视觉辅助 | 颜色反转 | 导航项 | 右侧"已关闭" |
| 视觉辅助 | 色彩校正 | 导航项 | 右侧"已关闭" |
| 视觉辅助 | 高级视觉辅助 | 导航项 | — |
| 听觉辅助 | 音频调节 | 导航项 | — |
| 听觉辅助 | 声音修复 | 导航项 | — |
| 听觉辅助 | 助听设备 | 导航项 | "未连接助听设备" |
| 听觉辅助 | 闪烁提醒 | 导航项 | — |
| 交互控制 | 屏幕触控 | 导航项 | — |
| 交互控制 | 无障碍快捷键 | 导航项 | — |

- **状态判断**: 右侧文本"已关闭"/"已开启"，进入子页面后有 Toggle

---

### 3.15 存储

- **导航路径**: 设置 > 存储
- **入口文本**: `存储`（需从设置首页滑动约 2 屏，确保文本不在屏幕底部边缘再点击）
- **滑动需求**: 4 屏
- **页面加载**: 进入后需等待 3s（存储计算）
- **子项**:

| 子项 | 形态 | id | 状态/操作说明 |
|------|------|-----|------------|
| 使用率 | text | (无id) | "16%" 百分比文本，bounds 约 [84,381][269,501] |
| 已使用/总大小 | text | (无id) | "已使用 83.02 GB/512 GB"，bounds 约 [84,501][556,550] |
| DataPanel | DataPanel | (无id) | 可视化进度环，bounds 约 [84,586][1236,694] |
| 类别标签 | text | (无id) | 应用/图片/视频/音频/文件/HarmonyOS/系统数据 |
| 应用大小 | text | `storage_app_data_size` | 分区标题 |
| 排序方式 | text_value | `AppGroup.SortType.title/result` | 右侧"大小" |
| 应用占用项 | text_value | `AppGroup.<包名>,0.title/result` | 右侧显示大小（如"3.43 GB"） |
| 一键清理 | — | — | 当前设备无此按钮 |

**关键规律**:
- 使用率文本以 `%` 结尾，无 id，需排除电池百分比（id 含 battery）
- 已使用/总大小文本以"已使用"开头，格式: `已使用 X GB/Y GB`
- 应用占用通过 id 匹配: `Setting.Storage.AppGroup.<包名>,0.title` 对应 `.result`
- "一键清理"按钮在当前设备/版本上不存在

---

### 3.16 电池

- **导航路径**: 设置 > 电池
- **入口文本**: `电池`
- **Toggle 数**: 3 个
- **子项** (完整 39 项):

| 子项 | 形态 | 状态/操作说明 |
|------|------|------------|
| 省电模式 | toggle_row | checked → ON/OFF |
| 显示电量百分比 | toggle_row | checked → ON/OFF |
| 无线反向充电 | toggle_row | checked → ON/OFF |
| 允许休眠时通知 | toggle_row | checked → ON/OFF |
| 电池健康 | nav_item | 进入子页面 |
| 电量使用情况 | 文本/图表 | 显示每小时电量记录 |
| 充电时段 | 文本 | 显示充电状态和时间段 |

---

### 3.17 生物识别和密码

- **导航路径**: 设置 > 生物识别和密码
- **入口文本**: `生物识别和密码`
- **滑动需求**: 2 屏
- **子项** (10 项):

| 子项 | 形态 | 状态/操作说明 |
|------|------|------------|
| 人脸识别 | text_value | 右侧"未录入"/"已录入" |
| 指纹 | text_value | 右侧"未录入"/"已录入" |
| 锁屏密码 | nav_item | — |
| 隐私密码 | nav_item | — |
| 锁定时允许访问 | section_header | — |
| 控制中心 | toggle_row | ❌ checked 始终 false，不可查询 |

- **注意**: 指纹/人脸识别需先设置锁屏密码才能使用

---

### 3.18 隐私和安全

- **导航路径**: 设置 > 隐私和安全
- **入口文本**: `隐私和安全`
- **滑动需求**: 4 屏
- **子项** (56 项):

| 子项 | 形态 | 状态/操作说明 |
|------|------|------------|
| 安全建议 | button | "安全建议 (3)" |
| 权限管理 | nav_item | 进入应用权限管理 |
| 位置 | nav_item | "14 个" 应用允许访问 |
| 相机 | nav_item | 使用时长 |
| 麦克风 | nav_item | 使用时长 |
| 图片和视频 | nav_item | — |
| 通讯录 | nav_item | — |
| 音乐和音频 | nav_item | — |
| 运动数据 | nav_item | — |
| 跨应用关联 | nav_item | — |
| 剪贴板 | nav_item | — |
| 设备发现和连接 | nav_item | — |
| 应用锁 | text_value | 右侧"访问应用需身份认证" |
| 隐私空间 | text_value | 右侧"独立于主空间的私密空间" |
| 防窥保护 | text_value | 右侧"实时检测是否有他人注视屏幕" |
| 超级隐私模式 | text_value | 右侧"一键关闭位置、相机和麦克风" |
| 密码保险箱 | text_value | 右侧"安全保存账号和密码" |
| 智能填充 | text_value | 右侧"自动填充个人常用信息" |
| 文件保密柜 | text_value | 右侧"加密保存图片、音视频和文档" |
| 数据和隐私 | text_value | 右侧"了解个人数据被如何收集与处理" |

---

### 3.19 小艺

- **导航路径**: 设置 > 小艺
- **入口文本**: `小艺`
- **滑动需求**: 2 屏
- **子项** (13 项):

| 子项 | 形态 | 状态/操作说明 |
|------|------|------------|
| 唤醒与对话 | button | 进入设置 |
| 小艺帮记 | nav_item | — |
| 小艺搜索 | nav_item | — |
| 小艺建议 | nav_item | — |
| 小艺翻译 | nav_item | — |
| 小艺字幕 | nav_item | — |
| 小艺通话 | nav_item | — |
| 智能服务 | nav_item | — |
| 个人智能计算透明性报告 | nav_item | — |

---

### 3.20 畅连通信

- **导航路径**: 设置 > 畅连通信
- **入口文本**: `畅连通信`
- **滑动需求**: 2 屏
- **子项** (5 项):

| 子项 | 形态 | 状态/操作说明 |
|------|------|------------|
| 开启畅连通信 | button | 按钮文本判断开关状态 |

### 3.17 更新选项（关于本机 > 软件更新 > 更新选项）

- **导航路径**: 设置 > 关于本机 > 软件更新 > 更新选项 (3 级导航, 无法通过常规入口到达)
- **推荐方式**: 使用 `search_setting('WLAN下自动下载', 'WLAN 下自动下载')` 搜索直达
- **搜索关键词**: `WLAN下自动下载` (输入无空格)
- **搜索结果文本**: `WLAN 下自动下载` (点击时需带空格)
- **搜索结果路径提示**: `关于本机 > 软件更新 > 更新选项`

| 子项 | 形态 | 状态/操作说明 |
|------|------|------------|
| 夜间安装 | toggle_row | checked → ON/OFF |
| WLAN 下自动下载 | toggle_row | checked → ON/OFF; **关闭时弹出确认对话框** |
| 协同更新 | toggle_row | checked → ON/OFF |

**WLAN 下自动下载确认弹窗** (关闭时):
- 标题: "关闭 WLAN 下自动下载"
- 描述: "关闭后，设备将无法在 WLAN 下自动下载。确定关闭？"
- 按钮: "取消" / "关闭"
- 处理: `click_by_text(layout, '关闭')` 点击确认

### 3.18 关于本机

- **导航路径**: 无法通过设置首页常规入口到达，使用搜索 `search_setting` 或自定义搜索导航
- **搜索关键词**: `关于本机`
- **页面加载**: 进入后需等待 2s

| 子项 | id | 形态 | 状态/操作说明 |
|------|-----|------|------------|
| 设备名称 | `version_info_group.display_device_name` | text_value | 右侧如"HuaweiHotspot" |
| 型号名称 | `version_info_group.display_device_name` | text_value | 右侧如"HUAWEI Pura X 典藏版" |
| 型号代码 | `version_info_group.product_model` | text_value | 右侧如"VDE-AL10" |
| **HarmonyOS 版本** | `version_info_group.harmonyos_version.title/result` | text_value | 右侧如"6.1.0"，**连续点击 7 次开启开发者模式** |
| 软件版本 | `version_info_group.software_version.title/result` | text_value | 右侧如"6.1.0.117 (SP6C00E115R3P6patch15)" |

- **开启开发者模式**: 在关于本机页面连续点击"HarmonyOS 版本"行 7 次
- **搜索导航注意**: `search_setting('关于本机')` 可能点击到搜索框文本而非搜索结果，需通过 `searchResultItem` id 定位搜索结果后点击其可点击父级

---

## 四、第三级页面结构（text_value / nav_item 子页面内部）

> 当控件形态为 `text_value` 或 `nav_item` 时，需要点击进入子页面才能操作。
> 本节记录子页面内部的控件结构，让脚本知道"进去后找什么"。

### 总体规律

| 列表页形态 | 子页面内通常有什么 | 操作方式 |
|-----------|------------------|---------|
| text_value (右侧"已关闭") | **1 个同名 Toggle** | 点击 Toggle 切换 |
| text_value (右侧具体值) | 选择器 / 列表 | 点击选项设值 |
| nav_item | 子页面内容各异 | 需具体分析 |

### 关怀和无障碍 — 子页面结构

| 子项 | 列表页形态 | 子页面内控件 | 子页面形态 | 操作方式 |
|------|----------|------------|----------|---------|
| 关怀模式 | text_value | "开启"按钮 (nav_item) | nav_item | 点击"开启"按钮 |
| 屏幕朗读 | text_value | Toggle "屏幕朗读" (checked=false) + "更多设置" | toggle_row | 点 Toggle 切换 |
| **放大手势** | text_value | **Toggle "放大手势" (checked=false)** | toggle_row | 点 Toggle 切换 |
| 高对比度文字 | text_value | Toggle "高对比度文字" (checked=false) | toggle_row | 点 Toggle 切换 |
| 颜色反转 | text_value | Toggle "颜色反转" (checked=false) | toggle_row | 点 Toggle 切换 |
| 色彩校正 | text_value | Toggle "色彩校正" (checked=false) | toggle_row | 点 Toggle 切换 |

**关键规律**: 关怀和无障碍的 text_value 项，子页面内有一个**同名 Toggle**，Toggle 名称与列表项名称完全一致。

### 显示和亮度 — 子页面结构

| 子项 | 列表页形态 | 子页面内控件 | 操作方式 |
|------|----------|------------|---------|
| 深色模式 | text_value ("已关闭") | Toggle "定时开启"(false) + Toggle "全天开启"(false) | 两个 Toggle 都关闭=深色模式关闭 |
| 护眼模式 | text_value ("已关闭") | Toggle "智能开启"(false) + Toggle "全天开启"(false) + Toggle "屏幕低频闪"(false) + text_value "定时开启"(right="已关闭") | 任一 Toggle 开启=护眼模式开启 |
| 电子书模式 | text_value | Toggle "电子书模式" (checked=false) | 点 Toggle 切换 |

### 多设备协同 — 子页面结构

| 子项 | 列表页形态 | 子页面内控件 | 操作方式 |
|------|----------|------------|---------|
| 接续 | text_value ("已开启") | 无 Toggle，仅描述文本 | 状态在列表页读取，子页面无操作 |
| 跨设备剪贴板 | text_value ("已开启") | 无 Toggle，仅描述文本 | 同上 |
| NFC | text_value ("已开启") | Toggle "NFC"(true) + Toggle "NFC 读卡通知勿扰"(false) + text_value "默认付款应用" | 点 NFC Toggle 切换 |
| 超级终端 | text_value | 需进一步探索 | — |
| 无线投屏 | text_value | 需进一步探索 | — |

**关键规律**: 多设备协同中部分项（接续、跨设备剪贴板）子页面**只有描述文本无 Toggle**，状态只能在列表页通过右侧文本读取，无法在子页面操作。

### 系统 — 子页面结构

| 子项 | 列表页形态 | 子页面内控件 | 操作方式 |
|------|----------|------------|---------|
| 智感握姿 | text_value ("已开启") | Toggle "智感握姿" (checked=true) | 点 Toggle 切换 |
| 智感支付 | text_value ("已关闭") | Toggle "智感支付" (false) + text_value "默认支付方式" | 点 Toggle 切换 |
| 系统导航 | nav_item | 子页面: 3个 Toggle (无文字, 靠坐标匹配最近Text) | 见下方补充 |
| 日期和时间 | text_value ("2026年x月x日") | Toggle "24小时制" + Toggle "自动设置" + text_value "时区" | 见下方补充 |

**日期和时间子页面详细结构**:

| 控件 | id | 形态 | 状态/操作 |
|------|-----|------|----------|
| 24 小时制 | `Time24HourGroup.Time24HourItem` | toggle_row | checked → ON(24小时)/OFF(12小时) |
| 自动设置（自动时区） | `DateTimeZoneGroup.auto_setting.result` | toggle_row | checked → ON/OFF |
| 日期 | `DateTimeZoneGroup.date_setting` | text_value | 右侧如"2026年7月6日"，仅自动设置关闭时显示 |
| 时间 | `DateTimeZoneGroup.time_setting` | text_value | 右侧如"15:47"，仅自动设置关闭时显示 |
| 时区 | `DateTimeZoneGroup.time_zone_setting.result` | text_value | 右侧显示如"GMT+08:00 中国标准时间" |

- **时区/日期/时间行仅在"自动设置"关闭时显示和可点击**，开启时不显示
- 点击时区行进入时区选择列表：按字母排序，右侧有字母索引 (A-Z)
- 列表项格式：城市/地区 (国家) + GMT偏移量，如"阿布扎比 (阿拉伯联合酋长国)" / "GMT+4:00"
- 列表项 Text clickable=false，需点击坐标
- 点击时间行打开 TimePicker（两列滚动轮：左小时右分钟，底部"取消"/"确定"按钮）
- 点击日期行打开 DatePicker（三列滚动轮：年/月/日，底部"取消"/"确定"按钮）
- 滚动轮操作方式：**点击相邻项位置**（选中项上方/下方 138px 处）可精确移动 1 步；swipe 方式不够精确不推荐
- Column 的 text 属性显示当前选中值，可用于每步验证

**开发者选项子页面详细结构**:

| 控件 | id | 形态 | 状态/操作 |
|------|-----|------|----------|
| 开发者选项 | — | toggle_row | 顶部 Toggle，checked=开发者模式状态 |
| 充电温度限制 | — | toggle_row | checked → ON/OFF |
| 自动系统更新 | — | toggle_row | checked → ON/OFF |
| 系统回退 | `entry_title_system_rollback_settings` | nav_item | — |
| **USB 调试** | `entry_toggle_usb_debug` | toggle_row | checked → ON/OFF，开启时可能弹确认对话框 |
| 意图框架调试 | `entry_title_insight_intent_settings` | toggle_row | checked → ON/OFF |
| 显示刷新频率 | — | toggle_row | checked → ON/OFF |
| 关闭充电 | `entry_toggle_usb_not_charging` | toggle_row | checked → ON/OFF |
| 清除受信任设备 | `entry_title_recall_usb_authorize` | nav_item | — |
| 无线调试 | — | toggle_row | checked → ON/OFF |

- **导航**: 系统 > 开发者选项（需滑动 2 次找到入口）
- USB 调试 Toggle 通过 id=`entry_toggle_usb_debug` 直接定位，无需文本匹配
- ⚠ **关闭 USB 调试会导致 hdc 连接断开**，脚本测试时仅测 query 模式

| 子项 | 列表页形态 | 子页面内控件 | 操作方式 |
|------|----------|------------|---------|
| 省电模式 | toggle_row | (点击后展开同页内容) Toggle "省电模式"(false) + Toggle "显示电量百分比"(true) + Toggle "无线反向充电"(false) | 直接在列表页点 Toggle |

### 生物识别和密码 — 子页面结构

| 子项 | 列表页形态 | 子页面内控件 | 操作方式 |
|------|----------|------------|---------|
| 指纹 | card (Column, 上下排列) | 需先设置锁屏密码，进入后显示"设置锁屏数字密码"页面 | 查询+设置锁屏密码可自动化；录入指纹需物理传感器 |
| 人脸识别 | card (Column, 上下排列) | 同指纹，需先设置锁屏密码 | 查询可自动化；录入需物理传感器 |
| 锁屏密码 | nav_item | 进入密码设置流程 | **可自动化** (TextInput + uitest text) |

**指纹/人脸识别卡片结构** (注意: 非左右排列，是上下排列):
```
Column text='指纹, 未录入' bounds=[678,333][1272,648] clickable=true
  Text text='指纹' bounds=[714,515][799,564]     (标题，上方)
  Text text='未录入' bounds=[714,570][823,612]    (状态值，下方，非右侧)
```
- **⚠ 不能用 `read_text_value_raw`** (该函数查找右侧文本，此处值在下方)
- **查询方法**: 找 Column text 含'指纹'，检查是否含'已录入'/'未录入'

### 隐私和安全 — 子页面结构

| 子项 | 列表页形态 | 子页面内控件 | 操作方式 |
|------|----------|------------|---------|
| 应用锁 | text_value | Toggle "机主注视显示通知内容"(false) + "开始使用应用锁"按钮 + "应用退出后上锁"/"仅锁屏后上锁"选项 | 需先设置锁屏密码，然后点"开始使用" |
| 隐私空间 | text_value | 子页面: 标题 + 描述文本 + "开启"按钮。开启流程: 确认主空间密码 → 设置隐私空间密码(须不同) → 确认 | 查询+开启可自动化；关闭未自动化 |
| 防窥保护 | text_value | text_value "防窥保护"(right="需设置人脸识别") | 需先设置人脸识别 |
| 超级隐私模式 | text_value | Toggle "超级隐私模式" (checked=false) | 点 Toggle 直接切换 |
| 密码保险箱 | text_value | 仅描述文本 + "设置锁屏密码" | 需先设置锁屏密码 |
| 智能填充 | text_value | Toggle "智能填充"(true) + Toggle "多设备同步"(false) + Toggle "将在同华为账号下同步数据"(false) + text_value "华为账号"/"联系人" | 点 Toggle 直接切换 |
| 文件保密柜 | text_value | 需进一步探索 | — |

### 系统 — 补充子页面结构

系统导航子页面 (系统 > 系统导航) 结构:
- "返回" 说明文本: "从屏幕左/右侧向内滑动，返回上一级" (无 Toggle)
- "导航条" 分区标题
- Toggle 1: "点击导航条返回" (checked 互斥)
- Toggle 2: "长按触发小艺对话" (checked 互斥, 当前激活=true)
- "更多设置" nav_item
- Toggle 3: "三键导航" (checked=false 表示手势导航, true 表示三键导航)

3 个 Toggle 无文字标签, 通过 `read_status_toggle_row(layout, '三键导航')` 匹配坐标最近的 Toggle.
`query_navigation_mode()` 返回 '手势导航'(三键导航 off) 或 '三键导航'(三键导航 on).

### 关怀和无障碍 — 补充子页面结构

| 子项 | 列表页形态 | 子页面内控件 | 操作方式 |
|------|----------|------------|---------|
| 声音修复 | text_value | Toggle "小艺通话"(false) + Toggle "声音修复"(false) + Toggle "点击打开应用"(false) | 点 Toggle 切换 |
| 助听设备 | text_value | 按钮列表（音频调节/声音修复/助听设备/闪烁提醒） | 导航到各子项 |
| 闪烁提醒 | (在助听设备子页面内) | 需从助听设备进入 | — |
| 屏幕触控 | (在交互控制分区) | 需从关怀和无障碍第 3 屏进入 | — |
| 无障碍快捷键 | text_value (right="屏幕朗读") | 需从关怀和无障碍第 3 屏进入 | — |
| 屏幕朗读 > 更多设置 | nav_item | 子页面内含: 屏幕朗读提示水印/语音设置/智能识别/解锁提示/锁屏提示/触控模式/触控振动反馈/触控音效反馈/隐藏屏幕内容/朗读表格或网格行列/单击操作模式 | 导航到各子项 |
| 屏幕朗读 > 更多设置 > 语音设置 | nav_item | Slider "语速"(text如"10000.000000") + "重置"按钮 + "默认语速"/"加快语速"文本 + Slider "音调" + "重置"按钮 | 拖动/点击 Slider |

### 多设备协同 — 补充子页面结构

| 子项 | 列表页形态 | 子页面内控件 | 操作方式 |
|------|----------|------------|---------|
| 超级终端 | text_value ("已开启") | 无 Toggle，仅描述文本 | 状态在列表页读取 |
| 无线投屏 | text_value ("已开启") | Toggle "无线投屏"(true) + "停止搜索"按钮 | 点 Toggle 切换 |

### 生物识别和密码 — 补充子页面结构

| 子项 | 列表页形态 | 子页面内控件 | 操作方式 |
|------|----------|------------|---------|
| 人脸识别 | text_value ("未录入") | 无 Toggle，需先设置锁屏密码 | 需先设置锁屏数字密码 |
| 指纹 | text_value ("未录入") | 无 Toggle，需先设置锁屏密码 | 需先设置锁屏密码 |

### 声音和振动 — 子页面结构

| 子项 | 列表页形态 | 子页面内控件 | 操作方式 |
|------|----------|------------|---------|
| 来电铃声 | nav_item | 双卡时有"卡 1"/"卡 2"tab + Radio 铃声列表（默认铃声含"(默认)"标记，checked=true 表示选中）+ "振动"/"选择铃声"/"本地音乐"/"在线铃声"/"视频铃声"/"无铃声"选项 | 点击 Radio 选项切换 |
| 信息铃声 | text_value | 铃声选择页（同来电铃声结构），默认"跃动 (默认)" | 点击选项切换 |
| 通知铃声 | text_value | 铃声选择页（同来电铃声结构），默认"昂扬 (默认)" | 点击选项切换 |

**来电铃声默认铃声**: "经典华为旋律 (默认)"（双卡时各卡可能有不同默认铃声，卡2默认"纯净华为旋律 (默认)"）
**信息铃声默认**: "跃动 (默认)"
**通知铃声默认**: "昂扬 (默认)"
**选中状态**: Radio 组件 `checked=true`
**双卡场景**: 双卡时有"卡 1"/"卡 2"tab，需分别切换查看/设置（仅来电铃声）
**闹钟铃声**: 不在「设置」中，时钟 App (com.huawei.hmos.clock) 使用自定义渲染，uitest 无法捕获布局，不支持查询

**场景**: 用户要"打开放大手势"

```
1. 设置 > 关怀和无障碍（导航到列表页）
2. 找到"放大手势"text_value 项，右侧显示"已关闭"
3. 点击"放大手势"进入子页面
4. 子页面有 Toggle "放大手势" (checked=false)
5. 点击 Toggle → checked 变为 true
6. 返回列表页，右侧文本变为"已开启"
```

对应脚本策略:
```python
# 1. 导航到列表页
layout = navigate_to_page('关怀和无障碍')
# 2. 读取状态（text_value 形态）
status = read_text_value_status(layout, '放大手势')
# 3. 如果需要切换，点击进入子页面
click_by_text(layout, '放大手势')
sub_layout = dump_layout()
# 4. 在子页面找同名 Toggle 并切换
toggle = find_toggle_by_text(sub_layout, '放大手势')
click_toggle(toggle)
# 5. 返回验证
go_back()
layout = dump_layout()
new_status = read_text_value_status(layout, '放大手势')
```

---

## 五、控件类型与状态判断方式

| 控件类型 | JSON 中的 type | 状态属性 | 取值 | 示例 |
|----------|---------------|----------|------|------|
| 开关 | Toggle / Switch | `checked` | "true"/"false" | 蓝牙开关、省电模式 |
| 滑块 | Slider | `value` | 数字字符串 | 音量、亮度 |
| 文本值 | Text | `text` | 任意文本 | "已开启"/"已关闭"/"100%" |
| 按钮文本 | Text (in Row) | `text` | 按钮文字 | "配对"/"确定"/"取消" |

### 状态判断策略优先级

1. **Toggle 组件**: 直接读 `checked` 属性 → 最可靠
2. **Toggle 自身含目标文本**: `attr(toggle, 'text')` 包含目标文本
3. **Toggle 在目标文本附近**: 按坐标距离找最近的 Toggle
4. **文本值**: 读 `text` 属性 (如"已开启"/"已关闭"/"100%")
5. **Slider 值**: 读 `value` 属性

---

## 六、控件形态分类（决定如何读取状态和执行操作）

设置页面中的每个菜单项呈现为以下 **6 种形态**之一。形态决定了状态读取方式和操作方式，生成脚本时必须根据形态选择正确的策略。

### 形态总览

```
┌─────────────────────────────────────────────────────────────────┐
│                    6 种控件形态                                  │
├──────────────┬──────────┬──────────────┬───────────────────────┤
│   形态名称    │ 识别特征  │  状态读取    │  操作方式              │
├──────────────┼──────────┼──────────────┼───────────────────────┤
│ toggle_row   │ Text旁有 │ Toggle的     │ 点击Toggle切换         │
│ (Toggle行)   │ Toggle   │ checked属性  │                       │
├──────────────┼──────────┼──────────────┼───────────────────────┤
│ button_card  │ 卡片内有 │ 按钮文本:    │ 点击"立即开启"/        │
│ (按钮卡片)   │ Button   │ "立即开启"   │ "立即关闭"按钮         │
│              │          │ =off         │                       │
├──────────────┼──────────┼──────────────┼───────────────────────┤
│ text_value   │ Text右侧 │ 右侧Text的   │ 点击进入子页面操作     │
│ (右侧文本行)  │ 有Text   │ text内容     │                       │
├──────────────┼──────────┼──────────────┼───────────────────────┤
│ slider_row   │ Text附近 │ Slider的     │ 拖动滑块或            │
│ (Slider行)   │ 有Slider │ value属性    │ 点击+/-区域            │
├──────────────┼──────────┼──────────────┼───────────────────────┤
│ nav_item     │ 可点击的 │ 需进入子页面 │ 点击进入子页面         │
│ (导航项)     │ 无状态   │ 查看         │                       │
├──────────────┼──────────┼──────────────┼───────────────────────┤
│ section_     │ desc含   │ —            │ —                     │
│ header(标题) │ "标题"   │              │                       │
└──────────────┴──────────┴──────────────┴───────────────────────┘
```

### 形态 1: toggle_row（Toggle 行）

**结构**: 一个 Text 组件（标签名）+ 同行的 Toggle 组件（开关）

**JSON 示例**:
```
Row [60,669][1260,813] clickable=true
├── Text "蓝牙" [84,713][205,769]
└── Toggle [1128,711][1236,771] checked=true
```

**状态读取**: `attr(toggle, 'checked')` → "true"=开, "false"=关
**操作**: 点击 Toggle 组件的中心坐标
**识别方法**: 在 Text 附近（y差<80, x差<1200）找 Toggle

**实际示例**:

| 页面 | 子项 | checked 值 |
|------|------|-----------|
| 星闪和蓝牙 | 星闪 | true |
| 星闪和蓝牙 | 蓝牙 | true |
| 移动网络 | 飞行模式 | false |
| 情景模式 | 推荐开启与关闭 | false |
| 情景模式 | 重要信息提醒 | false |
| 电池 | 省电模式 | false |
| 电池 | 显示电量百分比 | true |
| 电池 | 无线反向充电 | false |
| 显示和亮度 | 自动调节 | true |
| 显示和亮度 | 注视屏幕不熄屏 | false |
| 声音和振动 | 开机铃声 | true |
| 系统 | 防误触模式 | (需滑动到第2屏) |

---

### 形态 2: button_card（按钮卡片）

**结构**: 一个较大的卡片区域，包含 Text（模式名）+ Text（描述）+ Button（"立即开启"/"立即关闭"）

**JSON 示例**:
```
Column/Flex (卡片容器)
├── Text "免打扰" [342,834][978,930]
├── Text "减少打扰保持专注" [342,936][978,993]
└── Button "立即开启" [342,1038][978,1158] clickable=true
```

**状态读取**: Button 的 text → "立即开启"=关, "立即关闭"=开
**操作**: 点击 Button 组件
**识别方法**: 在 Text 附近（y差<300）找 type=Button 的组件

**实际示例**:

| 页面 | 子项 | 按钮文本 | 状态 |
|------|------|---------|------|
| 情景模式 | 免打扰 | "立即开启" | off |
| 情景模式 | 睡眠模式 | "立即开启" | off |

**关键注意**: 
- 按钮文本会随状态变化: 开启时变"立即关闭"，关闭时变"立即开启"
- 切换后按钮文本立即变化，可用于验证操作结果

---

### 形态 3: text_value（右侧文本行）

**结构**: 一个 Text 组件（标签名）+ 同行右侧另一个 Text 组件（状态值）

**JSON 示例**:
```
Row [60,xxx][1260,xxx] clickable=true
├── Text "WLAN" [84,xxx][xxx,xxx]
└── Text "Huawei-Guest" [xxx,xxx][1260,xxx]
```

**状态读取**: 找同行右侧（x更大, y差<60）的 Text 组件，读其 text
**操作**: 点击行进入子页面
**识别方法**: 在 Text 右侧（x差>50, y差<60）找另一个 Text

**实际示例**:

| 页面 | 子项 | 右侧文本 | 含义 |
|------|------|---------|------|
| 设置首页 | WLAN | "Huawei-Guest" | 当前连接的WiFi名 |
| 设置首页 | 星闪和蓝牙 | "已开启" | 蓝牙已开启 |
| 声音和振动 | 信息铃声 | "跃动" | 当前铃声名 |
| 声音和振动 | 通知铃声 | "昂扬" | 当前铃声名 |
| 声音和振动 | 音量键默认控制 | "媒体音量" | 当前设置 |
| 显示和亮度 | 深色模式 | "已关闭" | 深色模式未开启 |
| 显示和亮度 | 护眼模式 | "已关闭" | 护眼模式未开启 |
| 显示和亮度 | 休眠 | "10 分钟后" | 休眠时间 |
| 情景模式 | 免打扰(条件) | "已关闭" | 条件开启未激活 |
| 情景模式 | 联系人 | "仅允许收藏联系人" | 免打扰联系人范围 |
| 情景模式 | 深色模式(关联) | "不关联" | 不与情景模式关联 |

**状态值常见文本**:
- "已开启" / "已关闭" → 开关类状态
- "未连接" / "已连接" → 连接类状态
- "未选择" → 选择类状态
- 具体值（WiFi名、铃声名、时间） → 值类状态

---

### 形态 4: slider_row（Slider 行）

**结构**: 一个 Text 组件（标签名）+ 附近的 Slider 组件（滑块）

**JSON 示例**:
```
Row [60,xxx][1260,xxx]
├── Text "铃声 (来电、信息、通知)"
└── Slider [48,269][1272,389] text="81.000000" id="slider_ringTone_volume"
```

**状态读取**: `attr(slider, 'text')` 或 `attr(slider, 'originalText')` → 浮点数字符串
- **注意**: 值在 `text`/`originalText` 属性中，**不是** `value` 属性！
- 值范围: 0-100（浮点数，如 "0.000000", "81.000000"）
- Slider 还有 `id` 属性可用于精确查找（如 `slider_ringTone_volume`）

**操作**: 
- **点击设值**: 在 Slider 轨道上点击目标位置
  - `target_x = bounds[0] + (bounds[2] - bounds[0]) * desired_value / 100`
  - `target_y = (bounds[1] + bounds[3]) / 2`
- **拖动调值**: 从当前滑块位置拖动到目标位置
  - `uitest uiInput swipe x1 y1 x2 y2`
- **无 +/- 按钮**: Slider 旁没有加减按钮，只能通过轨道点击或拖动

**识别方法**: 在 Text 附近（y差<200）找 type=Slider 的组件

**Slider ID 对照表**:

| Slider ID | 对应项 | 页面 |
|-----------|--------|------|
| `slider_ringTone_volume` | 铃声(来电/信息/通知) | 声音和振动 |
| `slider_alarm_volume` | 闹钟 | 声音和振动 |
| `slider_media_volume` | 媒体(音乐/视频/游戏) | 声音和振动 |
| `slider_call_volume` | 通话 | 声音和振动 |
| `slider_vassistant_volume` | 小艺 | 声音和振动 |

**实际示例**:

| 页面 | 子项 | text 值 | 范围 |
|------|------|---------|------|
| 声音和振动 | 铃声 (来电、信息、通知) | "0.000000" | 0-100 |
| 声音和振动 | 闹钟 | "81.000000" | 0-100 |
| 声音和振动 | 媒体 (音乐、视频、游戏) | "0.000000" | 0-100 |
| 声音和振动 | 通话 | "81.000000" | 0-100 |
| 声音和振动 | 小艺 | "67.000000" | 0-100 |

**设值脚本示例**:
```python
def set_slider_value(slider_node, target_value):
    bounds_str = attr(slider_node, 'bounds', '')
    nums = re.findall(r'\d+', bounds_str)
    left, top, right, bottom = int(nums[0]), int(nums[1]), int(nums[2]), int(nums[3])
    # 计算目标 x 坐标
    target_x = int(left + (right - left) * target_value / 100)
    target_y = (top + bottom) // 2
    click_at(target_x, target_y)
    time.sleep(1)
    # 验证
    layout = dump_layout()
    # 重新查找 Slider 读 text 值
```

---

### 形态 5: nav_item（导航项）

**结构**: 一个 Text 组件（标签名），本身或父级 clickable=true，无 Toggle/Button/Slider/右侧文本

**JSON 示例**:
```
Row [60,xxx][1260,xxx] clickable=true
└── Text "移动数据"
```

**状态读取**: 无直接状态，需进入子页面查看
**操作**: 点击进入子页面
**识别方法**: Text 本身 clickable=true，或在可点击父级范围内，且附近无 Toggle/Button/Slider/右侧文本

**实际示例**:

| 页面 | 子项 |
|------|------|
| 移动网络 | 移动数据, SIM卡管理, 个人热点, 流量管理, 网络加速, 国际上网服务, VPN |
| 电池 | 电池健康 |
| 显示和亮度 | 字体大小和界面缩放, 色彩调节与色温, 高级设置 |
| 声音和振动 | 来电铃声, 信息铃声, 通知铃声 |
| 星闪和蓝牙 | 设备名称, 已配对设备列表, 其他设备列表 |

---

### 形态 6: section_header（分区标题）

**结构**: 一个 Text 组件，description 包含"标题"，不可点击

**JSON 示例**:
```
Text "已配对设备" [84,1028][1236,1077] description="标题"
```

**识别方法**: `attr(node, 'description')` 包含"标题"

**实际示例**: "已配对设备", "其他设备", "声音模式", "音量", "屏幕", "高级", "条件开启"

---

### 形态自动识别算法（用于脚本中）

```python
def detect_form(text_node, layout):
    """判断一个 Text 组件的控件形态"""
    center = parse_center(attr(text_node, 'bounds'))
    if not center:
        return 'plain_text'
    cx, cy = center

    # 6. 分区标题
    if '标题' in attr(text_node, 'description', ''):
        return 'section_header'

    # 1. Toggle 行: 附近有 Toggle
    for tg in toggles:
        tc = parse_center(attr(tg, 'bounds'))
        if tc and abs(tc[1]-cy) < 80 and abs(tc[0]-cx) < 1200:
            return 'toggle_row'

    # 2. 按钮卡片: 附近有 Button (y差<300)
    for btn in buttons:
        bc = parse_center(attr(btn, 'bounds'))
        if bc and abs(bc[1]-cy) < 300 and abs(bc[1]-cy) > 20:
            return 'button_card'

    # 3. 右侧文本: 右侧有另一个 Text
    for other in all_texts:
        if other is text_node: continue
        oc = parse_center(attr(other, 'bounds'))
        if oc and abs(oc[1]-cy) < 60 and oc[0] > cx + 50:
            return 'text_value'

    # 4. Slider 行: 附近有 Slider
    for sl in sliders:
        sc = parse_center(attr(sl, 'bounds'))
        if sc and abs(sc[1]-cy) < 200:
            return 'slider_row'

    # 5. 导航项: 可点击
    if attr(text_node, 'clickable') == 'true':
        return 'nav_item'
    # 检查父级是否可点击
    for c in clickables:
        fb = parse_full(attr(c, 'bounds'))
        if fb and fb[0]<=cx<=fb[2] and fb[1]<=cy<=fb[3]:
            return 'nav_item'

    return 'plain_text'
```

---

### 各形态对应的脚本策略速查

| 形态 | 查状态 | 开/关操作 | 查值 | 设值 |
|------|--------|----------|------|------|
| toggle_row | 读 `checked` | 点 Toggle 坐标 | — | — |
| button_card | 读 Button text | 点 Button 坐标 | — | — |
| text_value | 读右侧 Text | 需进子页面 | 右侧文本 | 需进子页面 |
| slider_row | — | — | 读 `value` | 拖动/点击 Slider |
| nav_item | 需进子页面 | 需进子页面 | 需进子页面 | 需进子页面 |
| button_selected | — | 点 selected=false 的 Button | 读 selected=true 的 Button 内 Text | — |
| section_header | — | — | — | — |

---

## 七、弹窗与交互流程

### 5.1 会触发弹窗的操作

| 场景 | 弹窗内容 | 需点击按钮 | 避坑 |
|------|---------|-----------|------|
| 蓝牙配对新设备 | "与 xxx 配对?" + PIN码 | `配对` | `find_by_text('配对')` 会匹配"已配对设备" → 用 `find_button()` 排除 |
| 蓝牙配对失败 | "配对失败" | `确定` | |
| 蓝牙配对超时 | "配对超时" | `确定` | |
| 取消蓝牙配对确认 | "确定取消配对?" | `确定` | |
| 权限请求 | "允许 xxx 访问?" | `允许` / `拒绝` | |
| 恢复出厂设置 | "确定恢复出厂设置?" | `确定` / `取消` | 高危操作！脚本应默认取消 |
| SIM 卡 PIN 验证 | "请输入 PIN 码" | 输入框 + `确定` | |
| 关闭开发者模式 | "关闭开发者模式?" | `确定` / `取消` | |
| 关闭飞行模式时确认 | (如有) | `确定` | 部分版本无弹窗 |

### 5.2 不会触发弹窗的操作（直接生效）

| 操作 | 形态 | 变化方式 | 验证方法 |
|------|------|---------|---------|
| 开关 WiFi | toggle_row | Toggle checked 变化 | 重新 dump 读 checked |
| 开关蓝牙 | toggle_row | Toggle checked 变化 | 重新 dump 读 checked |
| 开关飞行模式 | toggle_row | Toggle checked 变化 | 重新 dump 读 checked |
| 开关省电模式 | toggle_row | Toggle checked 变化 | 重新 dump 读 checked |
| 开关放大手势 | toggle_row (子页面) | Toggle checked 变化 | 返回列表页读右侧文本 |
| 开关深色模式 | toggle_row (子页面) | Toggle checked 变化 | 返回列表页读右侧文本 |
| 开关护眼模式 | toggle_row (子页面) | Toggle checked 变化 | 返回列表页读右侧文本 |
| 开关 NFC | toggle_row | Toggle checked 变化 | 重新 dump 读 checked |
| 开关免打扰 | button_card | 按钮文本变化 | 读按钮文本 "立即开启"→"立即关闭" |
| 开关显示电量百分比 | toggle_row | Toggle checked 变化 | 重新 dump 读 checked |
| 音量调节 | slider_row | Slider value 变化 | 重新 dump 读 value |

**关键规律**: `toggle_row` 和 `button_card` 形态的操作通常**不会触发弹窗**，直接生效。

**例外**: 部分 `toggle_row` 关闭时会弹出确认对话框:

| 设置项 | 弹窗内容 | 确认按钮 | 处理方法 |
|--------|---------|---------|---------|
| WLAN 下自动下载 (关闭时) | "关闭 WLAN 下自动下载" / "关闭后，设备将无法在 WLAN 下自动下载。确定关闭？" | "关闭" | `click_by_text(layout, '关闭')` |

### 5.3 会触发选择器的操作

| 操作 | 选择器内容 | 选择方式 |
|------|-----------|---------|
| 修改显示模式 | "浅色" / "深色" | 点击选项 |
| 修改休眠时间 | "15秒" / "30秒" / "1分钟" / "2分钟" / "5分钟" / "10分钟" | 点击选项 |
| 修改屏幕刷新率 | "智能" / "60Hz" / "90Hz" / ... | 点击选项 |
| 修改声音模式 | "响铃" / "振动" / "静音" | 点击选项 |
| 修改来电铃声 | 跳转铃声选择页 | 导航操作 |
| 修改音量键默认控制 | "媒体音量" / "铃声音量" | 点击选项 |

**选择器 JSON 结构**:
```
MenuItem "15 秒, 15 秒" [576,713][1224,857] clickable=true
├── Row
│   └── Text "15 秒"
└── Row (选中标记)
MenuItem "30 秒, 30 秒" [576,857][1224,1002] clickable=true
├── Row
│   └── Text "30 秒"
...
```

**选择器关键属性**:
- 选项类型: `MenuItem`（不是 `Text`）
- `clickable=true`：直接可点击
- `text` 格式: `"值, 值"`（重复，如 `"15 秒, 15 秒"`）
- 内部 Text 组件的 text 是干净的（如 `"15 秒"`）
- **无"确定"按钮**：点击选项后自动选中并关闭面板
- 选项排列: 从上到下，每个选项约 145px 高

**选择器交互方式**:
```python
# 1. 点击触发选择器的项 (如"休眠")
click_by_text(layout, '休眠')
time.sleep(1.5)
# 2. dump 选择器面板
selector_layout = dump_layout()
# 3. 找 MenuItem 选项
options = find_components(selector_layout, lambda c: attr(c,'type') == 'MenuItem')
# 4. 点击目标选项
for opt in options:
    if '30 秒' in get_text(opt):
        c = parse_bounds(attr(opt, 'bounds'))
        click_at(c[0], c[1])
        break
# 5. 面板自动关闭，无需点"确定"
```

**取消选择器**: 按 Back 键 或 点击选择器面板外部区域

### 5.4 弹窗处理要点

1. 按钮文本用**精确匹配或短文本过滤**，避免子串匹配到非按钮文本
2. 轮询等待时**每种按钮只点一次**，避免重复点击同一弹窗
3. 点击按钮后等 **2s** 让弹窗关闭再继续操作
4. `toggle_row` 和 `button_card` 操作**无需等待弹窗**，直接验证状态变化
5. `text_value` 操作**需进入子页面**，在子页面操作后返回验证

### 5.5 操作后验证策略

| 形态 | 操作后验证方式 | 等待时间 |
|------|--------------|---------|
| toggle_row | 重新 dump → 读 checked | 1s |
| button_card | 重新 dump → 读按钮文本 | 1s |
| text_value (子页面 Toggle) | 返回列表页 → 重新 dump → 读右侧文本 | 2s (返回+等待) |
| slider_row | 重新 dump → 读 value | 1s |
| 选择器 | 重新 dump → 读右侧文本 | 1.5s |

---

## 八、滑动需求汇总表

> 部分页面子项较多，需要多次滑动才能看到目标项。
> 以下为每个页面需要的滑动屏数（1 屏 = 1 次 swipe_up）。

| 页面 | 滑动屏数 | 需要滑动的关键子项 |
|------|---------|-------------------|
| WLAN | 4 | WiFi 列表可很长 |
| 星闪和蓝牙 | 2 | 第 2 屏有设备列表 |
| 移动网络 | 1 | — |
| 卫星网络 | 2 | — |
| 多设备协同 | 1 | — |
| 桌面、外屏和个性化 | 2 | — |
| 显示和亮度 | 2 | 第 2 屏有 Toggle |
| 声音和振动 | 3 | 第 2 屏有音量 Slider, 第 3 屏有 Toggle |
| 通知和状态栏 | 4 | 第 2-4 屏是各应用通知 Toggle |
| 情景模式 | 2 | 第 1 屏有免打扰/睡眠模式卡片 |
| 系统 | 4 | 第 3 屏有开发者选项 |
| 应用和元服务 | 4 | 第 2-4 屏是应用列表 |
| 健康使用设备 | 2 | — |
| 关怀和无障碍 | 4 | 第 2-4 屏有各项 |
| 存储 | 4 | 第 2-4 屏是应用占用列表 |
| 电池 | 4 | 第 2 屏有 Toggle |
| 生物识别和密码 | 2 | — |
| 隐私和安全 | 4 | 第 2-4 屏有各项 |
| 小艺 | 2 | — |
| 畅连通信 | 2 | — |

**特殊页面 — 更新选项**: 无法通过常规入口导航 (路径为 关于本机 > 软件更新 > 更新选项)，使用 `search_setting()` 搜索直达。

### 搜索直达方法

当设置项导航层级过深或不在常规入口时，可通过设置首页搜索框搜索并跳转:

```
search_setting(keyword, result_text)
```

流程: `restart_settings()` → 点击搜索框 (660, 387) → 找 TextInput → `uitest uiInput text <keyword>` → 等待 3s → `click_by_text(layout, result_text)` → 返回目标页 layout

**注意事项**:
- 搜索结果文本可能与输入不同（如 "WLAN下自动下载" → 结果 "WLAN 下自动下载" 带空格）
- `result_text` 必须用搜索结果中的实际文本，不是输入的关键词
- 搜索结果还显示路径提示（如 "关于本机 > 软件更新 > 更新选项"），可帮助确认目标

**脚本策略**: 如果在第一屏未找到目标项，最多滑动 4 次查找。每次滑动后 dumpLayout 重新检测。

---

## 九、安全认证门

> 部分设置项需要先完成认证（设置密码/录入生物特征）才能操作。
> 脚本在操作这些项时，可能遇到"需设置锁屏密码"等提示而卡住。

### 需要前置认证的设置项

| 设置项 | 页面 | 前置条件 | 子页面表现 | 解决方式 |
|--------|------|---------|-----------|---------|
| 应用锁 | 隐私和安全 | 需设置锁屏密码 | "开始使用应用锁"按钮，无 Toggle | 先确保已设密码，再点"开始使用" |
| 隐私空间 | 隐私和安全 | 需设置单独的锁屏密码 | 仅描述文本，无 Toggle | 需用户手动设置 |
| 防窥保护 | 隐私和安全 | 需设置人脸识别 | text_value 显示"需设置人脸识别" | 需先在生物识别中录入人脸 |
| 密码保险箱 | 隐私和安全 | 需设置锁屏密码 | "设置锁屏密码"按钮 | 先确保已设密码 |
| 人脸识别 | 生物识别和密码 | 需设置锁屏数字密码 | "设置锁屏数字密码"导航项 | 先设置锁屏密码 |
| 指纹 | 生物识别和密码 | 需设置锁屏密码 | 需先设置密码 | 先设置锁屏密码 |
| 文件保密柜 | 隐私和安全 | 需设置密码 | — | 需用户手动设置 |

### 不需要前置认证的设置项（可直接操作）

| 设置项 | 页面 | 子页面 Toggle | 说明 |
|--------|------|-------------|------|
| 超级隐私模式 | 隐私和安全 | Toggle "超级隐私模式" (false) | 直接切换 |
| 智能填充 | 隐私和安全 | Toggle "智能填充" (true) | 直接切换 |
| 声音修复 | 关怀和无障碍 | Toggle "声音修复" (false) | 直接切换 |
| 无线投屏 | 多设备协同 | Toggle "无线投屏" (true) | 直接切换 |
| 放大手势 | 关怀和无障碍 | Toggle "放大手势" (false) | 直接切换 |
| 屏幕朗读 | 关怀和无障碍 | Toggle "屏幕朗读" (false) | 直接切换 |
| 高对比度文字 | 关怀和无障碍 | Toggle "高对比度文字" (false) | 直接切换 |
| 颜色反转 | 关怀和无障碍 | Toggle "颜色反转" (false) | 直接切换 |
| 色彩校正 | 关怀和无障碍 | Toggle "色彩校正" (false) | 直接切换 |
| 智感握姿 | 系统 | Toggle "智感握姿" (true) | 直接切换 |
| 智感支付 | 系统 | Toggle "智感支付" (false) | 直接切换 |

### 脚本处理策略

1. **操作前检查**: 如果目标项在"需前置认证"列表中，脚本应先检查前置条件
2. **检测提示文本**: 子页面出现"需设置"/"设置锁屏密码"等文本 → 说明未满足前置条件
3. **提示用户**: 脚本应输出提示："请先设置锁屏密码/人脸识别后再运行此脚本"
4. **不要尝试自动设置密码**: 密码设置涉及安全验证，不应自动化

---

## 十、通用交互模式（脚本生成前必读）

> **目的**: 本章将所有设置操作抽象为可复用的交互模式。生成新脚本前，先匹配模式，再查页面结构（第三章），两者结合即可直接生成，避免调试。
>
> **使用方法**:
> 1. 识别目标操作的类型（开关？查询？输入文本？连接设备？选择选项？）
> 2. 在「10.2 交互模式索引」中找到匹配的模式
> 3. 按模式流程 + 第三章页面结构 → 直接编写 API 函数
> 4. 检查「10.3 弹窗处理」是否有已知弹窗
> 5. 检查「10.6 避坑清单」是否有已知陷阱

### 10.1 导航方法（3 种）

#### 方法 A: 常规导航 `navigate_to_page(entry, scroll)`

```
restart_settings() → dump_layout → find_by_text(入口) → click → 等待 2.5s → dump_layout
（未找到则滑动 scroll 屏重试）
```

**适用**: 设置 > 二级页面（大多数设置项）
**参数**: `entry`=入口文本, `scroll`=滑动屏数（查第八章）

#### 方法 B: 多级导航（手动逐级点击）

```python
layout = navigate_to_page('一级入口', scroll)
click_by_text(layout, '二级项', 2.5)    # 每级等待 2.5s
layout = dump_layout()
click_by_text(layout, '三级项', 2.5)    # 第三级
layout = dump_layout()
# ...更多级
```

**适用**: 语速设置（4级）、来电铃声（3级）、个人热点配置（3级）、系统导航（3级）、SIM卡管理（3级）
**关键**: 每级点击后必须 `dump_layout()` 获取新页面，不能复用旧 layout
**滑动**: 某级入口可能在下方，需先 `swipe_up()` 再查找

#### 方法 C: 搜索直达 `search_setting(keyword, result_text)`

```
restart_settings() → click_at(660, 387) [搜索框] → 找 TextInput → click_at 激活 →
uitest uiInput text <keyword> → 等待 3s → click_by_text(result_text) → dump_layout
```

**适用**: 导航层级 ≥3 级且入口不在常规菜单、或页面不在设置 App 常规入口
**已知实例**: WLAN 下自动下载（关于本机 > 软件更新 > 更新选项，3级）
**关键**: `result_text` 必须用搜索结果中的实际文本（可能带空格），不是输入的关键词

---

### 10.2 交互模式索引

| 模式 | 操作类型 | 触发条件 | 核心流程 | 已知实例 |
|------|---------|---------|---------|---------|
| A | 开关切换 | toggle_row | 读 checked → 点 Toggle → 重 dump 验证 | WLAN、蓝牙、省电模式 |
| B | 卡片按钮切换 | button_card | 读按钮文本 → 点 Button → 重 dump 读文本 | 勿扰模式 |
| C | 子页面开关 | text_value | 点击项 → 子页面 Toggle → 返回 → 读右侧文本 | 放大手势 |
| D | Slider 设值 | slider_row | 读 text 属性 → 按比例点轨道 → 重 dump 验证 | 语速、屏幕亮度 |
| E | 文本输入弹窗 | 点击 text_value 项 | 弹窗 TextInput → 输入文本 → 点确定 | 热点名称/密码 |
| F | 确认弹窗 | 关闭某些开关 | 点 Toggle → 弹窗 → 点确认按钮 | WLAN下自动下载 |
| G | Radio 选择 | Radio 列表 | 找 checked=true → 点目标 Radio → 验证 | 来电铃声 |
| H | MenuItem 选择器 | 点击触发选择器 | 找 MenuItem → 点目标选项 → 自动关闭 | 休眠时间 |
| I | 自动动作 | 已保存/开放网络 | 点击 → 系统自动处理 → 等待验证 | WiFi已保存连接 |
| J | 连接+配对弹窗 | 蓝牙设备 | 点设备 → 轮询配对弹窗 → 点配对 → 轮询连接 | 蓝牙连接 |
| K | 入口存在性 | "存在即开启" | 滑动查找入口 → 存在=True | 开发者模式 |
| L | button_selected | 双选 Button | 找 selected=true 的 Button → 读内嵌 Text | 默认数据卡 |

#### 模式 A: toggle_row 开关切换

```
1. navigate_to_page(入口, scroll) → layout
2. read_status_toggle_row(layout, 目标文本) → 'on'/'off'
3. 若 status == desired: return (True, status)  # 已是目标状态
4. _toggle_toggle_row(layout, 目标文本, desired):
   - find_by_text_nearest 找目标 Text
   - find_toggles 找所有 Toggle
   - 匹配: abs(toggle_y - text_y) < 80 且 abs(toggle_x - text_x) < 1200
   - click_at(toggle_center)
5. time.sleep(1) → dump_layout()
6. read_status_toggle_row(new_layout, 目标文本) → 验证
```

**坐标匹配阈值**: y 差 < 80px, x 差 < 1200px
**验证**: 重新 dump 读 `checked` 属性
**弹窗**: 通常无（例外见模式 F）

#### 模式 B: button_card 卡片按钮切换

```
1. navigate_to_page(入口, scroll)
2. read_status_button_card(layout, 目标文本):
   - find_by_text_nearest 找目标 Text
   - find_buttons 找 Button
   - 匹配: 20 < abs(btn_y - text_y) < 300
   - 按钮文本含 "立即开启" → off, "立即关闭" → on
3. 若 status == desired: return
4. _toggle_button_card: 点击对应 Button
5. time.sleep(1) → dump → 验证按钮文本变化
```

**坐标匹配阈值**: y 差 20-300px（不能太近也不能太远）
**验证**: 重新 dump 读按钮文本

#### 模式 C: text_value 子页面开关

```
1. navigate_to_page(入口, scroll)
2. read_status_text_value(layout, 目标文本):
   - find_by_text_nearest 找目标 Text
   - 在右侧 (x更大, y差<60px) 找另一个 Text
   - 含 "已开启" → on, "已关闭" → off
   - 非状态文本 (如描述) → continue 跳过, 继续找
3. 若 status == desired: return
4. _toggle_text_value:
   a. click_by_text(layout, 目标文本) → 进入子页面
   b. dump_layout() → sub_layout
   c. find_by_text_nearest(sub_layout, third_level_toggle) → 找子页面 Toggle
   d. click_at(toggle_center)
   e. go_back() → 返回列表页
5. dump_layout() → read_status_text_value 验证右侧文本
```

**坐标匹配阈值**: y 差 < 60px, x 差 > 50px（右侧）
**验证**: 返回列表页读右侧文本 "已开启"/"已关闭"
**关键**: `third_level_toggle` 参数 = 子页面内 Toggle 的文本（通常与列表项同名）
**描述文本跳过**: `read_status_text_value` 遇到非 "已开启/已关闭" 的文本时 `continue`，不返回 unknown

#### 模式 D: slider_row 设值

```
1. 导航到含 Slider 的页面（可能多级）
2. read_status_slider(layout, 目标文本):
   - find_by_text_nearest 找目标 Text
   - find_sliders 找 Slider
   - 匹配: abs(slider_y - text_y) < 200
   - 返回 attr(slider, 'text') 或 attr(slider, 'originalText')
3. set_slider(layout, 目标文本, value):
   - value: 0-100 百分比
   - target_x = slider_left + (slider_right - slider_left) * value / 100
   - click_at(target_x, slider_center_y)
4. dump → 验证 slider text 属性变化
```

**关键**: Slider 的值在 `text`/`originalText` 属性中，**不是** `value`！
**验证**: 重新 dump 读 `text` 属性

#### 模式 E: 文本输入弹窗

```
1. 导航到目标页面
2. click_by_text(layout, 目标项文本, 2.5) → 弹出对话框
3. dump_layout() → 弹窗 layout
4. find_components(layout, type=='TextInput') → 找输入框
5. 获取 TextInput center 坐标
6. 输入文本 (两种方式):
   方式1 (推荐, 用于空输入框):
     click_at(center) → hdc_shell('uitest', 'uiInput', 'text', 新文本)
   方式2 (用于已有内容的输入框, 替换):
     input_text(center_x, center_y, 新文本)  # 长按→全选→输入
7. dump_layout()
8. click_by_text(layout, '确定', 2.0) → 确认
9. dump → 验证右侧文本是否更新
```

**适用**: 热点名称、热点密码、WiFi 密码
**关键**: 
- 弹窗内 TextInput 可直接用 `uitest uiInput text` 输入（方式1），无需长按全选
- `input_text()`（方式2）用于需要替换已有内容的场景（长按→全选→输入）
- 确认按钮通常是 "确定" 或 "连接"

#### 模式 F: 确认弹窗处理

```
1. 执行 toggle 操作 (模式 A/B/C)
2. time.sleep(1) → dump_layout()
3. 检查弹窗: click_by_text(layout, 确认按钮文本, 2.0)
4. 若点击成功 (弹窗存在): time.sleep(1) → dump_layout()
5. 验证最终状态
```

**已知确认弹窗**:

| 设置项 | 弹窗标题 | 确认按钮 | 取消按钮 |
|--------|---------|---------|---------|
| WLAN 下自动下载 (关闭) | "关闭 WLAN 下自动下载" | "关闭" | "取消" |

**处理逻辑**: toggle 后 dump，尝试 `click_by_text(layout, 确认按钮)`。无弹窗时返回 False（正常继续），有弹窗时点击确认。

#### 模式 G: Radio 选择

```
1. 导航到含 Radio 的页面（可能多级）
2. (可选) 检测双卡: find_by_text(layout, '卡 1') and '卡 2'
3. (可选) 切换 tab: click_by_text(layout, '卡 1', 1.5) → dump
4. find_components(layout, type=='Radio') → 所有 Radio
5. 遍历 Radio:
   - attr(radio, 'checked') == 'true' → 当前选中
   - get_text(radio) 含 "(默认)" → 默认选项
6. 点击目标 Radio: click_at(radio_center)
7. dump → 验证 checked=true
```

**适用**: 来电铃声、信息铃声
**双卡处理**: 有 "卡 1"/"卡 2" tab 时需分别操作
**默认标记**: 默认铃声 Text 含 "(默认)" 后缀

#### 模式 H: MenuItem 选择器

```
1. 导航到目标页面
2. click_by_text(layout, 触发文本, 1.5) → 弹出选择器面板
3. time.sleep(1.5) → dump_layout()
4. find_components(layout, type=='MenuItem') → 所有选项
5. 遍历找目标: if 目标文本 in get_text(item)
6. click_at(item_center) → 选中, 面板自动关闭
7. (无需点确定)
```

**适用**: 休眠时间、显示模式、屏幕刷新率、声音模式
**关键**: 选项类型是 `MenuItem`，**不是** `Text`！
**取消选择器**: `go_back()` 或点击面板外区域

#### 模式 I: 自动动作（点击即完成）

```
1. 导航到目标页面
2. 滑动查找目标项
3. click_by_text(layout, 目标文本) → 系统自动处理 (无弹窗)
4. time.sleep(5) → dump_layout()
5. 验证: 检查目标项旁是否出现成功状态文本
```

**适用**: WiFi 已保存网络连接（点击→自动连接→验证"已连接"）
**关键**: 点击后无弹窗无 TextInput，不需要额外操作，只需等待+验证
**与模式 E 的区别**: 模式 E 有弹窗需输入，模式 I 无弹窗自动完成

#### 模式 J: 连接+配对弹窗（蓝牙）

```
1. 导航到蓝牙页面, 确保蓝牙已开启
2. 等待设备列表加载 (5s + dump)
3. 滑动查找目标设备
4. 检查是否已连接 (坐标匹配 '已连接' 文本)
5. 点击设备 → 触发配对
6. 轮询处理弹窗 (最多 10 次, 每次 1s):
   - find_button(layout, '配对') → 点击
   - find_button(layout, '确定') / '知道了' → 点击 (错误提示)
7. 轮询等待连接 (最多 15 次, 每次 2s):
   - 检查设备旁 '已连接' 文本
   - 处理任何弹窗
```

**关键**: 
- 用 `find_button()` 而非 `find_by_text()` 找"配对"按钮（避免匹配"已配对设备"）
- `find_button()` 排除含"设备"且长度>5的文本
- 配对弹窗可能延迟出现，需轮询

#### 模式 K: 入口存在性检查

```
1. navigate_to_page(入口, scroll)
2. 滑动查找目标项 (最多 scroll+1 屏):
   - find_by_text(layout, target) → 找到=True
   - swipe_up() → 下一屏
3. 返回: 入口存在 → True, 不存在 → False
```

**适用**: 开发者模式（"开发者选项"入口可见=已开启）
**语义**: "存在即开启"，不需要读 Toggle 状态

#### 模式 L: button_selected 双选按钮

```
1. 导航到目标页面（可能多级）
2. find_by_text_nearest(layout, 标签文本) → 找左侧标签
3. find_buttons(layout) → 找所有 Button
4. 匹配: abs(btn_y - label_y) < 80 且 btn_x > label_x (右侧)
5. 检查 attr(btn, 'selected') == 'true' → 当前选中
6. 找 Button 内嵌 Text: 在 btn bounds 范围内找 Text 组件
7. 返回 selected=true 的 Button 内 Text 内容
```

**适用**: 默认数据卡（"默认移动数据" → "卡 1"/"卡 2"）
**关键**: Button 的 `text` 属性为空，实际文本在内嵌 `Text` 子组件中

---

### 10.3 弹窗类型与处理

#### 弹窗 1: 确认对话框

**结构**: 标题 Text + 描述 Text + "取消" Button + 确认 Button
**处理**: `click_by_text(layout, 确认按钮文本, 2.0)`
**已知实例**:

| 设置项 | 确认按钮 | 触发条件 |
|--------|---------|---------|
| WLAN 下自动下载 | "关闭" | 关闭时 |
| 恢复出厂设置 | "确定" | 高危！脚本应默认取消 |
| 关闭开发者模式 | "确定" | 关闭时 |
| 取消蓝牙配对 | "确定" | 确认取消 |

#### 弹窗 2: 配对确认对话框（蓝牙）

**结构**: "与 xxx 配对?" + PIN 码 + "配对" / "取消" Button
**处理**: `find_button(layout, '配对')` → `click_at(center)`
**关键**: 用 `find_button()` 不用 `find_by_text()`，避免匹配"已配对设备"

#### 弹窗 3: 提示框（信息）

**结构**: 错误/提示 Text + "确定" / "知道了" Button
**处理**: 遍历 `['确定', '知道了']` 用 `find_button()` 查找
**已知实例**: 蓝牙配对失败、配对超时

#### 弹窗 4: 文本输入对话框

**结构**: 标题 Text + TextInput + "确定" / "取消" Button
**处理**:
```python
inputs = find_components(layout, lambda c: attr(c, 'type') == 'TextInput')
center = parse_bounds(attr(inputs[0], 'bounds'))
click_at(center[0], center[1], 0.5)
hdc_shell('uitest', 'uiInput', 'text', 新文本)
click_by_text(layout, '确定', 2.0)
```
**已知实例**: 热点名称、热点密码、WiFi 密码

#### 弹窗 5: WiFi 连接弹窗（密码输入）

**结构**: 
- 标题: WiFi 名称
- TextInput: hint="密码"
- "隐私" / "使用随机 MAC" 选项
- "高级选项" 可展开
- "连接" 按钮 (Text in Button, clickable=false)
- "安全键盘" 标识

**处理**:
```python
# 找 TextInput
ti = find_components(layout, lambda c: attr(c, 'type') == 'TextInput')[0]
center = parse_bounds(attr(ti, 'bounds'))
click_at(center[0], center[1], 0.5)
hdc_shell('uitest', 'uiInput', 'text', password)
time.sleep(1)
click_by_text(layout, '连接', 5.0)  # "连接" Text 在 Button 内
```

**WiFi 点击后的三种分支**:

| 场景 | 页面特征 | 处理 |
|------|---------|------|
| 已连接 | 有"断开连接"文本 | 返回已连接 |
| 已保存/开放网络 | 无 TextInput, 无弹窗 | 等待自动连接 (模式 I) |
| 新加密网络 | 有 TextInput (hint=密码) | 输入密码+点连接 (模式 E) |

---

### 10.4 验证方法速查

| 操作类型 | 验证方法 | 等待时间 | 代码 |
|---------|---------|---------|------|
| toggle_row 切换 | 重新 dump 读 `checked` | 1s | `read_status_toggle_row(new_layout, target)` |
| button_card 切换 | 重新 dump 读按钮文本 | 1s | `read_status_button_card(new_layout, target)` |
| text_value 切换 | 返回列表页读右侧文本 | 1s + go_back | `read_status_text_value(new_layout, target)` |
| slider 设值 | 重新 dump 读 `text` 属性 | 1s | `read_status_slider(new_layout, target)` |
| Radio 选择 | 重新 dump 读 `checked=true` | 1s | `find_components(..., type=='Radio')` |
| MenuItem 选择 | 面板自动关闭, 读右侧文本 | 1.5s | `read_text_value_raw(new_layout, target)` |
| 文本输入 | 读右侧文本是否更新 | 1s | `read_text_value_raw(new_layout, target)` |
| WiFi 连接 | 检查 SSID 旁"已连接" | 5s | 坐标匹配 "已连接" Text |
| 蓝牙连接 | 检查设备旁"已连接" | 2s×15次 | 轮询坐标匹配 |
| 入口存在性 | `find_by_text` 是否找到 | 即时 | `find_by_text(layout, target)` |
| button_selected | 读 `selected=true` 的 Button | 即时 | 遍历 Button 检查 `selected` |

**连接状态验证通用方法**:
```python
def verify_connected(layout, target_name):
    """检查目标名称旁是否有'已连接'文本"""
    comps = find_by_text_nearest(layout, target_name)
    all_texts = find_components(layout, lambda c: attr(c, 'type') == 'Text')
    for comp in comps:
        center = parse_bounds(attr(comp, 'bounds'))
        if not center: continue
        for t in all_texts:
            tc = parse_bounds(attr(t, 'bounds'))
            if tc and abs(tc[1] - center[1]) < 100 and tc[0] > center[0] - 50:
                if '已连接' in get_text(t):
                    return True
    return False
```

---

### 10.5 坐标匹配阈值速查

不同控件形态使用不同的坐标匹配阈值来判断组件关联（如 Text 与 Toggle 是否在同一行）:

| 形态 | y 差阈值 | x 差阈值 | 说明 |
|------|---------|---------|------|
| toggle_row | < 80px | < 1200px | 同行 Toggle，x 范围宽 |
| button_card | 20-300px | 无限制 | 按钮在卡片下方，不能太近 |
| text_value (读状态) | < 60px | > 50px (右侧) | 右侧同行文本 |
| text_value (连接验证) | < 100px | > -50px | 连接状态文本 |
| slider_row | < 200px | 无限制 | Slider 可能在 Text 下方 |
| button_selected | < 80px | > 0 (右侧) | 右侧 Button |

---

### 10.6 避坑清单

| # | 陷阱 | 原因 | 解决方案 | 影响函数 |
|---|------|------|---------|---------|
| 1 | 搜索"星闪"命中标题"星闪和蓝牙" | `find_by_text` 子串匹配 | 用 `find_by_text_nearest()` 按长度差排序 | 所有 `read_status_*`/`click_by_text` |
| 2 | 点击 Text 无反应 | Text `clickable=false` | `click_by_text()` 自动找可点击父级 | `click_by_text` |
| 3 | `slider.value` 读不到值 | 值在 `text`/`originalText` 属性 | 用 `attr(sl, 'text', attr(sl, 'originalText', ''))` | `read_status_slider` |
| 4 | 选择器选项找不到 | 选项类型是 `MenuItem` 不是 `Text` | `find_components(..., type=='MenuItem')` | — |
| 5 | `comp.get('text')` 返回 None | 属性在 `attributes` 字典中 | 用 `attr(node, key)` 函数 | 所有属性读取 |
| 6 | 返回键无效 | 用了 `systemInput` 命令 | `uitest uiInput keyEvent Back` | `go_back` |
| 7 | `find_by_text('配对')` 匹配"已配对设备" | 子串匹配 | 用 `find_button()` 排除含"设备"且长度>5的文本 | 蓝牙配对 |
| 8 | 电子书模式返回 `unknown(描述)` | 描述文本在状态文本之前 | `read_status_text_value` 遇非状态文本时 `continue` 跳过 | `read_status_text_value` |
| 9 | 蓝牙设备列表未加载 | 扫描需要时间 | 等待 5s + dump，轮询最多 10 次 | `_open_bluetooth_page` |
| 10 | WiFi 密码框已有内容 | `inputText` 在光标处插入 | 用 `input_text()` (长按→全选→输入) 或先清空 | `input_text` |
| 11 | `uitest uiInput inputText` 不清空 | 在光标处插入，不替换 | 用 `uitest uiInput text`（替换模式）或长按全选后输入 | `input_text` |
| 12 | `HDC` 变量为 None | `from hdc_utils import *` 导入时为 None | 用 `hdc_shell()` 函数（引用模块级变量） | `hdc_shell` |
| 13 | 搜索结果文本带空格 | 输入"WLAN下自动下载"但结果是"WLAN 下自动下载" | `result_text` 用搜索结果实际文本 | `search_setting` |
| 14 | WiFi 已保存网络点击无弹窗 | 系统自动连接，不弹密码框 | 检查无 TextInput 后直接等待验证（模式 I） | `connect_wlan` |
| 15 | PowerShell 中文乱码 | GBK 编码 | `sys.stdout.reconfigure(encoding='utf-8', errors='replace')` | CLI 脚本 |
| 16 | `navigate_to_page` 用 `scroll=` 关键字 | 参数名是 `scroll_screens` | 用位置参数: `navigate_to_page('入口', 4)` | `navigate_to_page` |

---

### 10.7 等待时间标准

| 场景 | 等待时间 | 原因 |
|------|---------|------|
| `aa start` 冷启动 | 3s | 应用启动 |
| 点击进入子页面 | 2.5s (NAV_WAIT) | 页面跳转动画 |
| `dumpLayout` 后 | 1s (DUMP_WAIT) | 文件写入 |
| 滑动后 | 1.5-2s | 列表刷新 |
| toggle 操作后 | 1s | 状态切换 |
| 蓝牙设备列表加载 | 5s | 扫描 |
| 蓝牙配对弹窗轮询 | 1s × 10次 | 弹窗延迟 |
| 蓝牙连接完成轮询 | 2s × 15次 | 连接耗时 |
| 搜索输入后 | 3s | 搜索结果加载 |
| WiFi 连接 | 5s | 网络连接 |
| WiFi 弹窗确认后 | 1s | 弹窗关闭 |

---

### 10.8 文本输入技术

HarmonyOS `uitest` 提供两种文本输入命令:

| 命令 | 行为 | 适用场景 |
|------|------|---------|
| `uitest uiInput text <文本>` | **替换**当前选中内容，无选中则插入 | 空输入框、已全选的输入框 |
| `uitest uiInput inputText <文本>` | 在光标处**插入**，不清空 | 不推荐（容易追加而非替换） |

**推荐流程**:

1. **空输入框** (如刚弹出的密码框): 点击激活 → `uitest uiInput text <文本>`
2. **已有内容的输入框** (如修改热点名称): `input_text(x, y, 文本)` = 长按 → "全选" → `uitest uiInput text <文本>`

**长按全选流程** (`input_text` 函数):
```
1. uitest uiInput longClick <x> <y>  → 显示上下文菜单
2. time.sleep(1.5)
3. dump_layout → click_by_text('全选')  → 选中全部文本
4. uitest uiInput text <新文本>  → 替换选中文本
```

**Ctrl+A (keyEvent 113 29) 在 HarmonyOS 中无效**，必须用长按→全选方式。

---

### 10.9 组件搜索策略

| 搜索需求 | 推荐函数 | 说明 |
|---------|---------|------|
| 按文本找组件 | `find_by_text_nearest` | 按长度差排序，避免子串碰撞 |
| 按文本找（无碰撞风险） | `find_by_text` | 子串匹配 |
| 找所有 Toggle | `find_toggles` | type 含 toggle/switch |
| 找所有 Button | `find_buttons` | type == Button |
| 找所有 Slider | `find_sliders` | type == slider |
| 找所有 MenuItem | `find_menu_items` | type == MenuItem |
| 找所有 Radio | `find_components(..., type=='Radio')` | — |
| 找所有 TextInput | `find_components(..., type=='TextInput')` | — |
| 找所有 Text | `find_components(..., type=='Text')` | — |
| 自定义条件 | `find_components(node, predicate)` | 递归搜索 |

**属性读取**: 统一用 `attr(node, key, default='')` 函数，不要用 `node.get('text')`
**文本读取**: 统一用 `get_text(node)` 函数（内部调用 `attr(node, 'text')` 或 `attr(node, 'originalText')`）

---

### 10.10 脚本生成检查清单

生成新脚本前，确认以下信息是否齐全:

- [ ] **导航路径**: 入口文本 + 滑动屏数（查第三章 + 第八章）
- [ ] **控件形态**: toggle_row / button_card / text_value / slider_row / nav_item / button_selected（查第六章）
- [ ] **交互模式**: 匹配本章 10.2 的哪个模式？
- [ ] **弹窗**: 操作是否触发弹窗？（查 10.3）
- [ ] **验证方法**: 操作后如何验证？（查 10.4）
- [ ] **已知陷阱**: 目标文本是否有子串碰撞风险？（查 10.6）
- [ ] **安全认证**: 是否需要前置认证？（查第九章）
- [ ] **等待时间**: 是否需要额外等待？（查 10.7）

**缺失信息时的处理**:
1. 先查本章是否有通用模式可套用
2. 若模式已知但页面结构未知 → 做针对性探索（只探索缺失部分）
3. 若模式未知 → 探索完整流程并补充到本章

---

## 十一、跨设置项依赖关系

> 一个设置的变化可能影响其他设置项的可用性或状态。
> 脚本在操作后验证时，需考虑这些依赖关系。

### 依赖关系表

| 触发操作 | 影响项 | 影响表现 | 脚本对策 |
|---------|--------|---------|---------|
| 开启飞行模式 | WLAN Toggle | 变为不可用 (clickable=false, enabled=false) | 操作 WLAN 前先检查飞行模式是否开启 |
| 开启飞行模式 | 蓝牙 Toggle | 变为不可用 | 操作蓝牙前先检查飞行模式 |
| 开启飞行模式 | 移动网络 Toggle | 变为不可用 | — |
| 开启飞行模式 | 卫星网络 | 变为不可用 | — |
| 关闭 WLAN | WLAN 安全检测 Toggle | 变为不可用 | — |
| 关闭蓝牙 | 已配对设备列表 | 列表消失或设备显示"未连接" | — |
| 开启省电模式 | 后台同步 | 可能关闭 | — |
| 开启省电模式 | 邮箱等应用后台刷新 | 可能受限 | — |
| 开启深色模式 | 多设备协同 > 关联深色模式 | 状态可能变化 | — |
| 开启关怀模式 | 整个设置页面 UI | 布局可能变化，字体放大 | 关怀模式开启后需重新采集页面结构 |
| 关闭开发者模式 | 系统页面"开发者选项"入口 | 入口消失 | 检测入口存在性判断开发者模式状态 |
| 设置锁屏密码 | 指纹/人脸识别 | 解锁可用 | 指纹/人脸识别依赖锁屏密码 |
| 开启免打扰 | 通知和状态栏 | 通知被静默 | — |

### 脚本中的依赖检查模板

```python
# 操作前检查: 确保飞行模式未开启
def check_flight_mode_off(layout):
    toggle = find_toggle_near(layout, '飞行模式')
    if toggle and attr(toggle, 'checked') == 'true':
        print("[WARN] 飞行模式已开启，WLAN/蓝牙不可用")
        return False
    return True

# 操作后验证: 考虑依赖影响
# 例: 开启 WLAN 后，检查 WLAN 安全检测是否恢复可用
```

---

## 十二、页面加载时间差异

> 不同页面加载速度不同，dumpLayout 时机需要匹配页面加载时间。
> 过早 dump 会得到不完整的页面内容。

### 页面加载时间表

| 页面 | 加载特点 | 点击后建议等待 | 滑动后建议等待 |
|------|---------|--------------|--------------|
| WLAN | WiFi 扫描动态加载，列表持续更新 | 3-5s | 2s |
| 星闪和蓝牙 | 蓝牙设备扫描，列表持续更新 | 3-5s | 2s |
| 存储 | 计算存储占用，百分比可能延迟更新 | 2-3s | 1.5s |
| 电池 | 读取电量使用记录 | 2s | 1.5s |
| 通知和状态栏 | 加载应用列表 | 2s | 1.5s |
| 应用和元服务 | 加载应用列表 | 2s | 1.5s |
| 多设备协同 | 检测附近设备 | 2s | 1.5s |
| 系统 | 即时加载 | 1.5s | 1s |
| 显示和亮度 | 即时加载 | 1.5s | 1s |
| 声音和振动 | 即时加载 | 1.5s | 1s |
| 其他大多数页面 | 即时加载 | 1.5-2s | 1s |

### 脚本中的等待策略

```python
# 通用导航等待
NAV_WAIT = 2.5  # 默认等待
# 特殊页面加载等待
PAGE_LOAD_WAIT = {
    'WLAN': 4.0,
    '星闪和蓝牙': 4.0,
    '存储': 3.0,
    '电池': 2.5,
    '通知和状态栏': 2.5,
    '应用和元服务': 2.5,
}
# 使用
wait = PAGE_LOAD_WAIT.get(page_name, NAV_WAIT)
```

### 动态内容页面注意事项

- **WLAN/蓝牙设备列表**: 设备会动态出现/消失，dumpLayout 结果可能不同
- **存储百分比**: 刚进入页面时可能显示旧值，1-2s 后更新
- **电池电量**: 实时变化，不影响结构但影响数值

---

## 十三、已知避坑清单

| # | 问题 | 原因 | 解决方案 |
|---|------|------|----------|
| 1 | `aa start` 报 "unknown option" | 参数格式因版本而异 | 先跑 `aa start --help` 确认语法 |
| 2 | 包名错误 | `com.huawei.hmossettings` 少了点 | 正确: `com.huawei.hmos.settings` |
| 3 | `dumpLayout` 文件拉取失败 | 文件名带时间戳 | 从 stdout 解析 `saved to:` 路径 |
| 4 | 所有 `comp.get('text')` 返回 None | 属性在 `attributes` 字典里 | 用 `attr(comp, key)` 函数 |
| 5 | `find_by_text('配对')` 点错位置 | 匹配到"已配对设备" | 用 `find_button()` 排除含"设备"的长文本 |
| 6 | 点击设备名无反应 | Text `clickable=false` | 找父级 Row 的可点击区域 |
| 7 | 页面刚打开找不到设备 | 扫描未完成 | 等 5s 再搜索 |
| 8 | 轮询时反复点同一弹窗 | 每次轮询都重新匹配 | 用 `clicked_buttons` 集合去重 |
| 9 | 返回键无效 | 用了 `systemInput` | 正确: `uitest uiInput keyEvent Back` |
| 10 | 入口文本不匹配 | "蓝牙"实际是"星闪和蓝牙" | 参考本知识库的入口文本 |
| 11 | Slider 值读不到 | 用了 `value` 属性 | 值在 `text`/`originalText` 属性中 |
| 12 | 选择器选项找不到 | 只找 `Text` 组件 | 选项类型是 `MenuItem`，不是 `Text` |
| 13 | 子页面 Toggle 找不到 | 在列表页找 Toggle | text_value 项需进入子页面，Toggle 在子页面内 |
| 14 | 安全设置项卡住 | 无前置密码直接操作 | 检查安全认证门表，提示用户先设密码 |
| 15 | 页面内容不完整 | dumpLayout 过早 | 按页面加载时间表设置等待时间 |
| 16 | 飞行模式下操作失败 | WLAN/蓝牙不可用 | 先检查飞行模式状态 |
| 17 | 查询返回 `unknown` | `find_by_text` 子串匹配命中页面标题 | 用 `find_by_text_nearest()` 按文本长度差排序 |

---

### 文本子串碰撞（find_by_text 陷阱）

**问题**: `find_by_text` 是子串匹配，搜索 `'星闪'` 会同时匹配 Toggle 标签 `"星闪"` 和页面标题 `"星闪和蓝牙"`。标题在布局 JSON 中排在前面，`comps[0]` 取到标题，标题坐标远离 Toggle，导致返回 `unknown`。

**判定条件**: 目标文本（target）是页面标题或其他长文本的子串。

**已知碰撞案例**:

| 页面标题 | 目标文本 | 形态 | 碰撞类型 |
|---------|---------|------|---------|
| 星闪和蓝牙 | 星闪 | toggle_row | 目标是标题子串 |
| 星闪和蓝牙 | 蓝牙 | toggle_row | 目标是标题子串 |
| 显示和亮度 | 亮度 | slider_row | 目标是标题子串 |
| 通知和状态栏 | 状态栏 | nav_item | 目标是标题子串 |

**解决方案**（已在代码中实现）:

`hdc_utils.py` 提供 `find_by_text_nearest(node, text)`，将匹配结果按 `abs(len(文本) - len(目标))` 升序排序，优先尝试文本长度最接近的组件。所有 `read_status_*` 和 `_toggle_*` 函数已改用此函数并遍历匹配结果。

**新增设置项时的检查清单**:
1. 检查目标文本是否是页面标题的子串（查本表或知识库第三章入口文本）
2. 若是碰撞案例，确认 `hdc_utils.py` 中对应形态的函数已使用 `find_by_text_nearest`
3. 若发现新的碰撞案例，补充到本表的「已知碰撞案例」中

---

## 十四、异常与边界场景处理

### Toggle 不可用（灰色/禁用）

**检测方式**: `attr(toggle, 'enabled') == 'false'` 或 `attr(toggle, 'clickable') == 'false'`

**常见原因**: 飞行模式开启时 WLAN/蓝牙 Toggle 禁用；WLAN 关闭时安全检测 Toggle 禁用

**脚本对策**:
```python
if attr(toggle, 'enabled') == 'false':
    print(f"[WARN] {name} 当前不可用（可能被其他设置限制）")
    return 'unavailable'
```

### 无 SIM 卡场景

- 移动网络页面: "移动数据"和"SIM 卡管理"可能不显示或显示"无 SIM 卡"
- 来电铃声: 可能没有"卡 1"/"卡 2"区分
- 卫星网络: 可能显示"无可用卫星"

### 双卡 vs 单卡

- 来电铃声: 双卡时分为"卡 1"和"卡 2"独立设置
- 移动网络: 显示两个 SIM 卡管理入口
- 脚本需根据实际页面内容动态适配，不能硬编码卡数

### 设置应用崩溃/页面加载失败

**表现**: dumpLayout 返回空 JSON 或只有状态栏

**对策**:
```python
layout = dump_layout()
texts = find_components(layout, lambda c: attr(c, 'type') == 'Text' and len(get_text(c)) > 1)
if len(texts) < 3:
    print("[WARN] 页面可能未加载，重启设置...")
    restart_settings()
    layout = dump_layout()
```

### 关怀模式开启后的 UI 变化

- 关怀模式会改变整个系统的 UI 布局
- 设置页面的字体、间距、布局可能完全不同
- 脚本在关怀模式开启状态下可能找不到预期的组件
- **建议**: 脚本启动时检查关怀模式状态，如果开启则提示用户先关闭

### 设备未连接

**检测**: `hdc list targets` 返回 `[Empty]`

**对策**: 脚本启动时检查设备连接状态，未连接则退出并提示

### 语言环境变化

- 所有文本匹配基于中文环境
- 如果设备语言切换为英文，所有 `find_by_text` 调用将失效
- **限制**: 当前知识库仅支持中文系统语言

---

## 十五、非设置页面操作（控制中心等）

> 除了设置应用，部分开关可以通过控制中心更快捷地操作。

### 控制中心（下拉面板）

**打开方式**: 从屏幕顶部右侧下滑

**打开控制中心的脚本方式**:
```python
# 从屏幕右上角下滑到屏幕中部（动态坐标，跨设备兼容）
w, h = get_screen_size()
hdc_shell('uitest', 'uiInput', 'swipe', str(w - 50), '50', str(w - 50), str(int(h * 0.5)))
time.sleep(2)
```

**JSON 结构**: 控制中心使用 `NewToggleBaseComponent` 组件，每个开关包含：
- `Stack` id=`transition_toggle<名称>`，clickable=true（图标容器）
- `Canvas` id=`Ctrl.NewToggleBaseComponent_Image_<名称>`（图标渲染，clickable=false）
- `Text` id=`Ctrl.NewToggleBaseComponent_Text_<名称>`（开关名称）

**⚠️ 重要限制 — 控制中心开关状态不可查询**:
- `checked`、`selected` 属性对**所有**控制中心组件始终为 `false`，无论开关实际状态
- `backgroundColor` 始终为 `#00000000`
- `dumpLayout -a`（扩展属性）同样无法区分开启/关闭状态
- 图标使用 Canvas 绘制，状态仅体现在图标视觉颜色上（蓝色=开启，灰色=关闭）
- `param get`、`settings`、`wm` 等系统命令在该设备上不可用（errNum 1002 或命令不存在）
- **结论**：控制中心开关只能执行点击切换操作，无法通过布局信息查询当前状态
- 如需查询状态，应通过设置 App 中对应设置项查询

**可操作的开关**:

| 开关 | 控件类型 | 操作方式 | 可查询状态 |
|------|---------|---------|-----------|
| WLAN | Toggle/Button | 点击切换 | ❌ 控制中心不可查 |
| 蓝牙 | Toggle/Button | 点击切换 | ❌ 控制中心不可查 |
| 飞行模式 | Toggle/Button | 点击切换 | ❌ 控制中心不可查 |
| 免打扰 | Toggle/Button | 点击切换 | ❌ 控制中心不可查 |
| 旋转锁定 | Toggle/Button | 点击切换 | ❌ 控制中心不可查 |
| 亮度 | Slider | 拖动调整 | — |
| 媒体音量 | Slider | 拖动调整 | — |
| 省电模式 | Toggle/Button | 点击切换 | ❌ 控制中心不可查 |
| NFC | Toggle/Button | 点击切换 | ❌ 控制中心不可查 |
| 热点 | Toggle/Button | 点击切换 | ❌ 控制中心不可查 |
| 投屏 | Button | 点击打开选择器 | — |

> **注意**: 上表中"可查询状态"指通过控制中心 dumpLayout 查询。如需查询这些开关的状态，请通过设置 App 对应设置项查询。

**优势**: 控制中心操作只需 1 步（下拉 + 点击），而设置应用需要 2-3 步导航

**劣势**: 
- **开关状态不可查询**：所有控制中心组件的 `checked`/`selected` 始终为 `false`，`dumpLayout -a` 也无效
- 控制中心布局可能因设备/版本不同而变化
- 部分设置项（如放大手势、深色模式）不在控制中心

### 通知面板

**打开方式**: 从屏幕顶部左侧下滑

**用途**: 查看通知，清除通知

### 快捷设置

**打开方式**: 控制中心展开后点击编辑按钮

**用途**: 自定义控制中心显示的开关

### 脚本选择建议

| 场景 | 推荐路径 | 原因 |
|------|---------|------|
| 开关 WLAN/蓝牙/飞行模式 | 控制中心 | 1 步完成（仅切换，不可查状态） |
| 开关免打扰 | 控制中心或设置 | 都可以（设置可查状态） |
| 查询开关状态 | 设置应用 | **控制中心 Toggle 的 checked/selected 始终为 false，不可查询** |
| 开关放大手势/深色模式 | 设置应用 | 控制中心无此选项 |
| 调节音量 | 控制中心 | 有 Slider |
| 操作需要弹窗确认的功能 | 设置应用 | 控制中心可能不触发弹窗 |
