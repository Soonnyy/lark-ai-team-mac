#!/bin/sh
set -eu
umask 077
cd "$(dirname -- "$0")"
case "$(uname -s):$(uname -m)" in
  Darwin:arm64) ;;
  *) printf '%s\n' '此安装器面向 Apple Silicon Mac。' >&2; exit 1 ;;
esac
command -v python3 >/dev/null
node_version=24.21.0
openclaw_version=2026.11.3
lark_version=1.0.100
mkdir -p .tools/bin .state
temp=$(mktemp -d)
trap 'rm -rf "$temp"' EXIT
download() {
  base=$1 archive=$2 checksums=$3
  curl -fsSL --retry 2 "$base/$archive" -o "$temp/$archive"
  curl -fsSL --retry 2 "$base/$checksums" -o "$temp/checksums"
  (cd "$temp" && awk -v name="$archive" '$2 == name {print}' checksums | shasum -a 256 -c -)
}
node_archive="node-v$node_version-darwin-arm64"
if [ ! -x ".tools/$node_archive/bin/node" ]; then
  download "https://nodejs.org/dist/v$node_version" "$node_archive.tar.gz" SHASUMS256.txt
  tar -xzf "$temp/$node_archive.tar.gz" -C .tools
fi
ln -sfn "../$node_archive/bin/node" .tools/bin/node
ln -sfn "../$node_archive/bin/npm" .tools/bin/npm
if [ ! -x .tools/bin/lark-cli ]; then
  lark_archive="lark-cli-$lark_version-darwin-arm64.tar.gz"
  download "https://github.com/larksuite/cli/releases/download/v$lark_version" "$lark_archive" checksums.txt
  tar -xzf "$temp/$lark_archive" -C "$temp"
  install -m 755 "$(find "$temp" -type f -name lark-cli -print | head -1)" .tools/bin/lark-cli
fi
export PATH="$(pwd)/.tools/bin:$PATH"
if [ ! -x .tools/runtime/node_modules/.bin/openclaw ]; then
  npm install --prefix .tools/runtime --no-audit --no-fund "openclaw@$openclaw_version"
fi
python3 setup.py init
for plugin in feishu codex deepseek-provider; do
  ./openclaw-local plugins install "@openclaw/$plugin@$openclaw_version"
done
./openclaw-local config validate
printf '%s\n' '安装完成。按 README 从扫码建机器人继续。'
