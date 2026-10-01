# subtitle-note skill 一键安装（Windows PowerShell）
# 用法:
#   irm https://raw.githubusercontent.com/<user>/<repo>/main/install.ps1 | iex
#   .\install.ps1 [user/repo]          # 本地模式：仓库 clone 下来后直接运行
$ErrorActionPreference = "Stop"

$repo   = if ($args.Count -gt 0) { $args[0] } else { "<user>/english-subtitle-learning" }   # TODO: 建仓后改 <user>
$name   = "subtitle-note"
$target = Join-Path $HOME ".zcode\skills\$name"

# 本地模式：脚本所在目录就带着 skill/，直接用，不联网
$src = $null
if ($PSScriptRoot -and (Test-Path (Join-Path $PSScriptRoot "skill"))) {
  $src = Join-Path $PSScriptRoot "skill"
  Write-Host "==> 使用本地仓库 $PSScriptRoot"
}
else {
  $tmp = Join-Path $env:TEMP "subtitle-note-$(Get-Random)"
  Write-Host "==> 下载 $repo ..."
  $zip = Join-Path $tmp "repo.zip"
  New-Item -ItemType Directory -Force $tmp | Out-Null
  Invoke-WebRequest "https://codeload.github.com/$repo/zip/refs/heads/main" -OutFile $zip
  Expand-Archive $zip $tmp -Force
  $src = Get-ChildItem $tmp -Directory | Where-Object { Test-Path (Join-Path $_.FullName "skill") } |
         Select-Object -First 1 -ExpandProperty FullName
  $src = Join-Path $src "skill"
  if (-not (Test-Path $src)) { throw "下载失败：未找到 skill/（检查仓库名与默认分支是否为 main）" }
  $script:keepTmp = $tmp
}

New-Item -ItemType Directory -Force (Split-Path $target) | Out-Null
if (Test-Path $target) { Remove-Item -Recurse -Force $target }
Copy-Item -Recurse $src $target
if ($keepTmp) { Remove-Item -Recurse -Force $keepTmp }

Write-Host "==> 已安装到 $target"
Write-Host ""
Write-Host "安装完成。新开一个会话，对 AI 说："
Write-Host "  「字幕笔记」「预习笔记」「把这集字幕整理成笔记」"
Write-Host "或直接给剧名与季集 / 字幕文件即可触发。"
Write-Host ""
Write-Host "卸载：删除 $target"
Write-Host "更新：重新运行本脚本即可（覆盖安装）"
Write-Host "提醒：生成笔记还需要 Python 3（脚本仅用标准库，无第三方依赖）"
