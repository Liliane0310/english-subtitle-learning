#!/usr/bin/env bash
# subtitle-note skill 一键安装（macOS / Linux）
# 用法:
#   curl -fsSL https://raw.githubusercontent.com/<user>/<repo>/main/install.sh | bash
#   bash install.sh [user/repo]        # 本地模式：仓库 clone 下来后直接运行
set -euo pipefail

REPO="${1:-<user>/english-subtitle-learning}"   # TODO: 建仓后把 <user> 改成你的 GitHub 用户名
SKILL_NAME="subtitle-note"
TARGET="${HOME}/.zcode/skills/${SKILL_NAME}"

# 本地模式：脚本所在目录就带着 skill/，直接用，不联网
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || true)"
SRC=""
if [ -n "$SCRIPT_DIR" ] && [ -d "${SCRIPT_DIR}/skill" ]; then
  SRC="${SCRIPT_DIR}/skill"
  echo "==> 使用本地仓库 ${SCRIPT_DIR}"
else
  TMP="$(mktemp -d)"
  trap 'rm -rf "$TMP"' EXIT
  echo "==> 下载 ${REPO} ..."
  curl -fsSL "https://codeload.github.com/${REPO}/tar.gz/refs/heads/main" | tar -xz -C "$TMP"
  SRC="${TMP}/$(basename "$REPO")-main/skill"
  [ -d "$SRC" ] || { echo "下载失败：未找到 skill/（检查仓库名与默认分支是否为 main）" >&2; exit 1; }
fi

mkdir -p "$(dirname "$TARGET")"
rm -rf "$TARGET"
cp -R "$SRC" "$TARGET"

echo "==> 已安装到 ${TARGET}"
if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
  echo "!! 提醒：生成笔记还需要 Python 3（脚本仅用标准库，无第三方依赖）"
fi
cat <<EOF

安装完成。新开一个会话，对 AI 说：
  「字幕笔记」「预习笔记」「把这集字幕整理成笔记」
或直接给剧名与季集 / 字幕文件即可触发。

卸载：rm -rf ${TARGET}
更新：重新运行本脚本即可（覆盖安装）
EOF
