# 测试脚本生成 Skill

## 目的

这个 Skill 用于根据一段测试用例描述文件，生成对应的 Python 测试脚本。

它面向“测试一个 agent”的场景，测试用例通常包含三部分：

- `preset`：预置条件，例如创建一个上午 7 点的闹钟
- `action`：执行动作，例如“给我创建一个下午 3 点的闹钟”
- `checks.state_based`：状态校验，例如成功创建了一个下午 3 点的闹钟

其中：

- `preset` 可以通过命令完成
- `action` 需要调用接口发送给被测 agent
- `state_based` 需要通过 API 读取状态并断言
- `get_alarm` 的具体返回值格式由你后续补充

---

## 输入格式

本 Skill 使用 JSON 作为测试用例描述文件格式。

### 示例

```json
{
  "name": "create_afternoon_alarm",
  "description": "验证已有上午7点闹钟时，用户要求创建下午3点闹钟后状态正确",
  "preset": [
    {
      "type": "command",
      "description": "创建一个上午7点的闹钟",
      "input": {
        "time": "07:00",
        "period": "AM"
      }
    }
  ],
  "action": {
    "type": "agent_message",
    "text": "给我创建一个下午3点的闹钟"
  },
  "checks": {
    "state_based": [
      {
        "description": "成功创建了一个下午3点的闹钟",
        "api": "get_alarm",
        "expected": {
          "time": "15:00",
          "exists": true
        }
      }
    ]
  }
}