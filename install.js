#!/usr/bin/env node
// subtitle-note skill 一键安装（任意有 Node + Git 的平台）
// 用法: npx github:<user>/<repo>   或   node install.js [user/repo]
"use strict";
const { execSync } = require("child_process");
const { cpSync, rmSync, mkdirSync } = require("fs");
const path = require("path");
const os = require("os");

const repo = process.argv[2] || "<user>/english-subtitle-learning"; // TODO: 建仓后改 <user>
const target = path.join(os.homedir(), ".zcode", "skills", "subtitle-note");
const tmp = path.join(os.tmpdir(), `subtitle-note-install-${Date.now()}`);

console.log(`==> git clone https://github.com/${repo}.git`);
execSync(`git clone --depth 1 "https://github.com/${repo}.git" "${tmp}"`, { stdio: "inherit" });

const src = path.join(tmp, "skill");
if (!require("fs").existsSync(src)) {
  rmSync(tmp, { recursive: true, force: true });
  console.error("下载失败：仓库中未找到 skill/");
  process.exit(1);
}
mkdirSync(path.dirname(target), { recursive: true });
rmSync(target, { recursive: true, force: true });
cpSync(src, target, { recursive: true });
rmSync(tmp, { recursive: true, force: true });

console.log(`==> 已安装到 ${target}`);
console.log("");
console.log("安装完成。新开一个会话，对 AI 说：");
console.log("  「字幕笔记」「预习笔记」「把这集字幕整理成笔记」");
console.log("或直接给剧名与季集 / 字幕文件即可触发。");
console.log("");
console.log(`卸载：删除 ${target}`);
console.log("更新：重新运行本命令即可（覆盖安装）");
