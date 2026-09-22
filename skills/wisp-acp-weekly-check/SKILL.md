---
name: wisp-acp-weekly-check
description: Check whether the ACP adapters actually configured in Wisp Science match their latest official stable releases, report installed versions and update status, and maintain a weekly Windows check. Use for Wisp ACP version checks or weekly update monitoring; this does not update adapters or check Wisp application releases.
---

# Wisp ACP 每周版本检查

检查 Wisp 实际配置的 ACP 适配器，比较本机磁盘安装版本与官方 npm `latest`，用中文报告最新、有更新、预发布、旧包需迁移或无法验证。用户要求定期检查时，可在 Windows 注册每周任务；示例默认每周一 09:00，Asia/Shanghai。检查不包含升级操作。

## 执行检查

运行本技能的 [scripts/check_acp.py](scripts/check_acp.py)，使用可用的 Python 3.10+，无需第三方依赖：

```powershell
& '<python.exe 的绝对路径>' '<本技能目录>\scripts\check_acp.py' --output-dir '<报告输出目录>'
```

- 默认只读 `%APPDATA%\science.wisp-science\wisp-science\wisp.sqlite` 中 `settings.acp_agent_profiles`；可用 `--database` 指定其他 Wisp 数据库。不要读取认证字段或聊天记录，不要写 Wisp 数据库。
- 每次重新读取已配置的 ACP。脚本支持能通过绝对命令路径对应到官方 npm 包的 Windows `.cmd` 包装器、直接包入口以及带绝对脚本参数的 `node.exe`。
- 已核实的包：`@agentclientprotocol/codex-acp`、`@agentclientprotocol/claude-agent-acp`；旧 `@zed-industries/codex-acp` 标记需迁移。不要把不同包名直接比较版本。
- 相对命令、动态 `npx`/`npm exec`、自定义包装器或其他适配器无法可靠定位时，报告无法验证，再通过 Wisp **Settings -> Models -> ACP Agents** 和官方文档确认来源。不要执行未知启动命令或用 `npx -y ... --version` 探测；它可能下载软件或改变缓存。
- 联网查询使用 `https://registry.npmjs.org/<包名>/latest`。网络失败、包不存在、设置改变或版本不可解析均不得报告为最新。预发布版本与稳定版分开报告。
- `latest.md` 和 `latest.json` 为最近一次结果，每次还保留带时间戳的历史报告。退出码 0 表示检查完成（包括发现更新）；2 表示存在无法验证的项目。

汇报检查时间、ACP 名称、实际启动路径、安装版本、官方 latest、结论和来源。已安装版本只代表磁盘上的包，不保证正在运行的 Wisp 会话已重新加载。不要用全局 `codex --version` 代替适配器版本；Wisp 应用、ACP 协议、适配器、底层 CLI 分别管理。

## 每周自动检查

Skill 是操作指引，本身不会按时运行。在 Windows 上可用计划任务调用同一脚本，并把结果写到用户指定的报告目录。

需要创建、修复或按用户要求调整每周检查时，运行 [scripts/register-weekly-task.ps1](scripts/register-weekly-task.ps1)，传入持久 Python 安装的绝对路径和报告目录。任务名为 `Wisp-ACP-Weekly-Check`。不要依赖临时虚拟环境；如果解释器路径失效，先修复再报告调度正常。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File '<本技能目录>\scripts\register-weekly-task.ps1' -PythonPath '<python.exe 的绝对路径>' -OutputDir '<报告输出目录>'
```

注册后检查任务的 Actions、Triggers、当前用户身份和 NextRunTime，启动一次并核对新报告与 LastTaskResult。只有实际注册且验证成功才说已开启每周检查。不要在每次手工检查时重复注册任务。

任务以当前用户登录会话静默运行，无需 Wisp 打开；电脑关机或用户未登录期间无法检查，使用系统的错过后尽快运行设置。时间按 Windows 本机时区解释；当前注册脚本要求 `China Standard Time`，不匹配时应停止且不修改任务。报告保存在本机，不承诺聊天推送。用户要求停止时，只禁用/删除此专属任务并保留报告。

## 官方核实来源

- [Wisp ACP 配置文档](https://github.com/xuzhougeng/wisp-science/blob/main/docs/acp-agents.md)：实际启动命令与参数、ACP 与 Wisp 内置模型的区别。
- [Codex ACP 官方仓库](https://github.com/agentclientprotocol/codex-acp)：包身份、底层 Codex 依赖及发布说明。
- [Claude ACP 官方仓库](https://github.com/agentclientprotocol/claude-agent-acp)：Claude 适配器的发布来源。
- [旧 Codex ACP 迁移声明](https://github.com/zed-industries/codex-acp)：迁移到当前包名。
- [npm view](https://docs.npmjs.com/cli/v11/commands/npm-view/) 与 [npx](https://docs.npmjs.com/cli/v11/commands/npx/)：元数据读取与动态包执行的区别。

脚本未支持的安装方式先查官方资料再处理；不要把本次观察到的版本写成永久最新版本。
