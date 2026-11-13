# 用一台 Mac，把三个 AI 接进同一个 Lark 群

**在手机上 @ Codex 写代码、@ Claude 做审查、@ DeepSeek 梳理问题。** 三个机器人各用自己的身份回复，由你的 Apple Silicon Mac 运行 OpenClaw。

`macOS arm64` · `Lark 国际版` · `中文教程`

**安装只需一条命令。** 下载本仓库并解压，在终端进入该目录后运行：

```sh
chmod +x install.sh openclaw-local && ./install.sh
```

安装后按下文完成 **Lark 扫码 → 三个机器人入群 → 本机授权 → 手机发第一条 @ 消息**。你需要 Apple Silicon Mac、Python 3、可创建应用的 Lark 账号和相应的模型权限。Claude 可按需启用，安装后即可先验收 Codex 和 DeepSeek。

**验证范围**：安装器已在干净的临时目录完成实装和配置校验。三机器人群聊曾在原型环境中验证，新安装包的扫码与群聊仍需使用自己的账号按下文验收。

## 1. 安装

上面的命令在项目内安装官方 Node 24.21.0、Lark CLI 1.0.100、OpenClaw 2026.11.3 及其飞书、Codex、DeepSeek 插件。建议直接用官方 Node，部分桌面应用内置的 Node 受 macOS 签名限制，无法加载 OpenClaw 的原生组件。若启动时端口冲突，可运行 `./openclaw-local config set gateway.port 18793 --strict-json`。

## 2. 扫码建三个机器人，再加进同一个群

逐条执行。每次打开终端给出的链接，用同一个 Lark 账号扫码、确认创建，等终端完成后再跑下一条。

```sh
.tools/bin/lark-cli config init --new --brand lark --name team-codex
.tools/bin/lark-cli config init --new --brand lark --name team-claude
.tools/bin/lark-cli config init --new --brand lark --name team-deepseek
```

用这个账号创建测试群。打开群设置里的「添加机器人」，把三个应用加进去。机器人同名时，先到开放平台用应用 ID 找到对应应用，在「凭证与基础信息」给应用起不同名字，按后台要求发布版本。

若 @ 后没有事件，到各自应用的「事件与回调」确认使用长连接并订阅「接收消息」`im.message.receive_v1`。检查机器人能力、群聊 @ 消息权限 `im:message.group_at_msg:readonly` 和机器人发消息权限 `im:message:send_as_bot`。修改后按后台提示发布版本。[Lark 频道设置](https://docs.openclaw.ai/channels/feishu/setup)

## 3. 绑定同一个测试群

逐条执行，每次选择同一个群。脚本会从机器人能看到的群中读取群 ID 和群主在该应用下的身份。到 Lark 开发者后台打开提示的应用，在「凭证与基础信息」复制 **App Secret**，只粘贴到本机终端提示。脚本验证后才保存。默认仅响应所选群内由群主发出的 @ 消息。

```sh
python3 setup.py codex
python3 setup.py claude
python3 setup.py deepseek
```

## 4. 登录模型

在启动网关之前执行 Codex 登录，按浏览器提示授权，等终端确认成功。网关运行期间需要先停止才能写入登录。

```sh
./openclaw-local models auth login --provider openai --method oauth --agent codex
python3 setup.py deepseek-key
```

第二条命令会提示输入 DeepSeek 开放平台创建的 API Key。Claude 可先保持暂停。需要启用时，先安装官方 Claude Code，将 `claude` 放在终端 PATH，运行 `claude auth login` 完成登录，再执行：

```sh
./openclaw-local config set channels.feishu.accounts.claude.enabled true --strict-json
```

暂停时把 `true` 改成 `false`。这会关闭项目的 Claude 群聊入口，个人复习仍可使用 Claude。订阅余量百分比需要在 Claude 用量界面确认。默认模型为 Codex GPT-6 Astra 高、Claude Opus 5.5 中、DeepSeek V4 Pro 高。模型权限取决于各自账号。[Codex 登录](https://docs.openclaw.ai/providers/openai/authentication) · [Claude Code 安装](https://code.claude.com/docs/en/setup) · [DeepSeek 接入](https://docs.openclaw.ai/providers/deepseek)

## 5. 启动和验收

```sh
./openclaw-local gateway run
```

保持这个终端窗口打开。另开一个终端进入同一目录，运行 `./openclaw-local channels status --probe`。手机进群，依次用 @ 菜单选中每个已启用的机器人，在同一条消息里写「只回复 连接测试通过」。核对回复身份。Claude 暂停期间只验收 Codex 和 DeepSeek。停止网关时在启动窗口按 Ctrl+C。

这份安装包提供三个独立聊天入口。项目间的任务交接、后台常驻和定时日报需另外配置。上传 GitHub 时只使用本目录的源文件。所有运行状态和密钥在被 Git 忽略的 `.state/`，安装依赖在 `.tools/`，模型工作文件在 `workspaces/`。Lark CLI 的扫码登录保存在用户自己的本机配置。
