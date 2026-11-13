#!/usr/bin/env python3
"""Prepare the local OpenClaw config and bind one Lark bot at a time."""

import getpass
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
STATE = ROOT / ".state"
CONFIG = STATE / "openclaw.json"
ROLES = {
    "codex": ("Codex · 主开发", "openai/gpt-6-astra", "high"),
    "claude": ("Claude · 审查测试", "claude-cli/claude-opus-5-5", "medium"),
    "deepseek": ("DeepSeek · 咨询巡检", "deepseek/deepseek-v4-pro", "high"),
}


def save(path, content):
    with tempfile.NamedTemporaryFile(mode="w", dir=STATE, delete=False) as draft:
        draft.write(content)
    os.replace(draft.name, path)


def initialize():
    STATE.mkdir(mode=0o700, exist_ok=True)
    if CONFIG.exists():
        return
    agents = {}
    bindings = []
    for role, (name, model, effort) in ROLES.items():
        workspace = ROOT / "workspaces" / role
        workspace.mkdir(parents=True, exist_ok=True)
        agents[role] = {
            "name": name, "workspace": str(workspace),
            "model": model, "thinkingDefault": effort,
        }
        bindings.append({"agentId": role, "match": {"channel": "feishu", "accountId": role}})
    config = {
        "gateway": {"mode": "local", "bind": "loopback", "port": 18792,
                    "auth": {"mode": "token", "token": secrets.token_hex(32)}},
        "agents": {"ownership": "explicit", "defaults": {"systemAgent": {"agentId": "codex"}},
                   "entries": agents},
        "bindings": bindings,
        "channels": {"feishu": {"enabled": False, "domain": "lark",
                                 "connectionMode": "websocket", "requireMention": True,
                                 "dmPolicy": "disabled", "groupPolicy": "allowlist",
                                 "accounts": {}}},
        "cron": {"enabled": False},
    }
    save(CONFIG, json.dumps(config, ensure_ascii=False, indent=2) + "\n")


def bind(role):
    config = json.loads(CONFIG.read_text())
    channel = config["channels"]["feishu"]
    cli = [str(ROOT / ".tools/bin/lark-cli"), "--profile", f"team-{role}"]
    profile = json.loads(subprocess.check_output(cli + ["config", "show"]))
    chats = json.loads(subprocess.check_output(cli + ["im", "+chat-list", "--as", "bot"]))["data"]
    groups = [chat for chat in chats.get("chats") or [] if chat.get("owner_id", "").startswith("ou_")]
    if not groups:
        sys.exit("请先在 Lark 测试群中添加这个机器人，再重跑此命令。")
    for index, chat in enumerate(groups, 1):
        print(f"{index}. {chat['name']}")
    selection = input("选群编号：").strip()
    if not selection.isdecimal() or not 1 <= int(selection) <= len(groups):
        sys.exit("群编号无效。")
    group = groups[int(selection) - 1]
    expected = {item for account in channel["accounts"].values() for item in account["groupAllowFrom"]}
    if expected and expected != {group["chat_id"]}:
        sys.exit("请选择与其他机器人相同的群。")
    print(f"在 Lark 后台打开应用 {profile['appId']} 的凭证页。")
    secret = getpass.getpass("粘贴 App Secret（屏幕不显示）：").strip()
    request = Request(
        "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal",
        json.dumps({"app_id": profile["appId"], "app_secret": secret}).encode(),
        {"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=10) as response:
        result = json.load(response)
    if not result.get("tenant_access_token"):
        sys.exit(f"Lark 凭据验证失败，错误码 {result.get('code')}。")
    channel["accounts"][role] = {
        "appId": profile["appId"], "appSecret": secret, "name": ROLES[role][0],
        "enabled": role != "claude", "groupAllowFrom": [group["chat_id"]],
        "groupSenderAllowFrom": [group["owner_id"]],
    }
    channel["enabled"] = True
    channel["defaultAccount"] = "codex" if "codex" in channel["accounts"] else role
    save(CONFIG, json.dumps(config, ensure_ascii=False, indent=2) + "\n")
    print("已保存。Claude 默认暂停，需要时再启用。")


def main():
    if len(sys.argv) != 2:
        sys.exit("用法：python3 setup.py init|codex|claude|deepseek|deepseek-key")
    action = sys.argv[1]
    if action == "init":
        initialize()
    elif action in ROLES:
        bind(action)
    elif action == "deepseek-key":
        key = getpass.getpass("粘贴 DeepSeek API Key（屏幕不显示）：").strip()
        if not key or not all(c.isascii() and (c.isalnum() or c in "-_") for c in key):
            sys.exit("API Key 格式无效。")
        save(STATE / ".env", f"DEEPSEEK_API_KEY={key}\n")
    else:
        sys.exit("未知操作。")


if __name__ == "__main__":
    main()
