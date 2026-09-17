# zsh 配置仓库

个人 zsh 配置模块集合。目标环境：**macOS (Apple Silicon) + Homebrew (`/opt/homebrew`) + zsh 5.9**。

本仓库包含按模块拆分的配置文件；入口文件为 `private_dot_config/zsh/dot_zshrc`（部署为 `~/.config/zsh/.zshrc`，经 `symlink_dot_zshrc.tmpl` 在 `~/.zshrc` 建立符号链接兼容）。**各源码文件头部与内联注释为单一事实来源（SSOT）**，本文仅作高层索引与契约说明，不复述字段值与代码清单。

## 模块总览

| 文件 | 职责 | 指针 |
| --- | --- | --- |
| `aliases.zsh` | 通用别名与函数 | 详见文件头部 `Description/Usage` 与各节内联注释 |
| `fzf.zsh` | fzf 与 fzf-tab 配置 | 详见文件头部与第 1–5 节注释；含 Ctrl-G 等键位 |
| `sdk.zsh` | SDK 环境与补全 | 详见文件头部与各 SDK 小节注释；含 SDKMAN 惰性加载、补全缓存等 |

> 具体别名、函数与选项以源码为准，不在此逐项展开，避免与源码重复。

### 加载顺序契约（重要）

`~/.config/zsh/.zshrc`（兼容路径 `~/.zshrc`）按 **compinit（Zim 框架）→ `aliases.zsh` → `fzf.zsh` → `sdk.zsh`** 的顺序 source 本仓库文件。**顺序即语义**，重排会静默改变行为：

- `aliases.zsh` 必须先于 `fzf.zsh`（后者 Ctrl-G 绑定在 source 时展开 `$EDITOR`）；
- `sdk.zsh` 必须在 compinit 之后且最后加载（内含 `compdef` 注册，需 compinit 已完成；`k` 别名仅在此定义，`aliases.zsh` 有意不重复）。

精确的 `source` 语句与守卫说明见 `private_dot_config/zsh/dot_zshrc` 底部加载块与各文件头部的 `Usage` 注释，本文不复述代码清单。

## 关键设计约定

### 编辑器契约

`EDITOR`/`VISUAL` 的定义位置、值与导出方式以 `aliases.zsh` 源码为准（当前为 `nvim`，环境变量而非 alias，供 git/crontab/fzf 等读取）。`fzf.zsh` 的 `FZF_DEFAULT_OPTS` 中 `ctrl-g:execute($EDITOR {} &> /dev/tty)` 在 source 时展开该变量，故 `aliases.zsh` 必须先于 `fzf.zsh` 加载。不要将 `export EDITOR=...` 改为 `alias`。详见两文件的相关注释。

### 前缀缓存

fzf 安装前缀的探测顺序、缓存文件位置（`~/.fzf_prefix_cache`）及自愈逻辑（仅当 `$FZF_PREFIX/bin/fzf` 可执行时信任缓存）见 `fzf.zsh` 第 1 节注释与代码，不在此复述路径列表。

### 内联注释的兼容性

`FZF_DEFAULT_OPTS` 等多行值中的行内 `#` 注释已在本机 fzf **0.74.3** 实测可正常解析；升级或更换 fzf 后如遇解析异常，优先检查 `fzf.zsh` 第 3 节全局选项。

## 函数速查

高层索引，实现与参数细节以对应源码与内联注释为准：

| 函数 | 所在文件 | 用途 |
| --- | --- | --- |
| `auto-update` | aliases.zsh | 一键全量更新入口（可选 `onproxy` 后委托 `update-all`） |
| `onproxy` / `ofproxy` | aliases.zsh | 开启/关闭终端代理环境变量 |
| `update-all [targets...]` | aliases.zsh | 声明式批量更新，支持参数过滤与耗时/失败统计 |
| `ruff_auto [dir]` | aliases.zsh | ruff 自动修复并格式化 |
| `y [args]` | aliases.zsh | yazi 包装：退出后 cd 到最后浏览目录 |
| `jdx [args]` / `scr [args]` | aliases.zsh | 后台启动 jadx-gui / scrcpy |
| `frg [pattern]` | fzf.zsh | rg+fzf 搜内容，回车在 nvim 定位打开 |
| `fkill [signal]` | fzf.zsh | fzf 选进程并 kill |
| `find_large_files [size]` | fzf.zsh | 列出大文件（默认 100M） |
| `ftm [session]` | fzf.zsh | fzf 选择/创建 tmux 会话 |
| `flf` / `flkill` / `flnet` / `fluser` | fzf.zsh | lsof+fzf 浏览/杀进程/网络/按用户过滤 |

> `auto-update` 为薄包装，`update-all` 为关联数组驱动的声明式实现；二者分工与行为差异见源码注释与 `docs/shell.md`。破坏性命令 `uv_resync` 见注意事项，不在此表展开。

## 依赖清单

### 环境变量

关键变量（`LANG`、`EDITOR`/`VISUAL`、`GOPROXY`/`GOPATH`/`GOBIN`、`ANDROID_NDK_HOME`、`FZF_PREFIX`/`FZF_PREFIX_CACHE`、`PATH` 增量等）的精确值、定义位置与守卫条件（目录存在性 + 去重、重复 source 幂等）以 `dot_zshrc` / `aliases.zsh` / `fzf.zsh` / `sdk.zsh` 源码为准，本文不建字段-值表以避免与源码重复。

### 启动必需（缺失会导致功能缺失）

- `fzf`（有 `command -v` 守卫；缺失则失去 Ctrl-R/Ctrl-T/Alt-C 等绑定及 `frg`/`fkill`/`ftm`/`fl*`）
- `fzf-tab` 插件（由 `private_dot_config/zsh/dot_zimrc` 的 `zmodule Aloxaf/fzf-tab` 经 zimfw 加载；缺失则补全菜单失去 fzf 化）
- zsh 补全系统 `compinit`（由 `dot_zshrc` 的 Zim 框架最先完成；`sdk.zsh` 的 `compdef` 依赖它）

### 有守卫的可选组件（未安装时静默跳过）

`pnpm`（tabtab 补全）、SDKMAN（惰性加载，详见 `sdk.zsh` 注释）、`docker`/`kubectl`+`kubecolor`（补全缓存于 `~/.cache/zsh/` 并 `zcompile`，二进制更新自动重建；`k` 别名带守卫）、krew、`~/.cargo/env`。`update-all` 的 6 目标 `brew`/`sdk`/`rustup`/`tldr`/`uv`/`mise` 逐项 `command -v` 守卫，未安装跳过、失败汇总并返回非零；其中 `brew` 任务依赖 `brew tap buo/homebrew-cask-upgrade`（提供 `brew cu`），新机器上未 tap 时该任务会在 `brew cu` 处失败。详见 `sdk.zsh` 与 `aliases.zsh` 源码。

### 运行时工具（对应别名/函数调用时才需要）

`fd`（主力，缺省回退 `rg`）、`bat`、`lsd`、`nvim`、`code`、`htop`、`fastfetch`、`tmux`、`yazi`、`gh`、`lazygit`、`claude`、`opencode`、`ruff`、`uv`、`rustup`、`tldr`、`mise`、`nproc`（coreutils）、`wget`、`jadx-gui`、`scrcpy`。`java` 仅经 `update-all` 的 `sdk` 任务间接使用。已移除的死引用可从更早的独立 `zsh-config` 仓库历史找回；本仓库从未有过 `baseline` 标签，勿凭空创建。

## 注意事项

1. **破坏性命令**：`uv_resync` 会先删除 `~/.venv` 与 `~/uv.lock` 再执行 `uv sync`（目标为家目录路径而非当前项目），使用前请确认。定义见 `aliases.zsh`。
2. **`~/.config/zsh/.zshrc`（即仓库内 `private_dot_config/zsh/dot_zshrc`，兼容 `~/.zshrc` 符号链接）已收敛单一初始化点**：fzf 键位/补全仅在 `fzf.zsh` 内带守卫地 `eval "$(fzf --zsh)"` 一次，`dot_zshrc` 不再重复 eval；`sdk.zsh` 为无条件 `source` 但内部逐项守卫。详见 `dot_zshrc` 注释。
3. **强绑定的个人路径与镜像**：`GOPATH`、`GOPROXY`、清华 pip 镜像别名、`ANDROID_NDK_HOME` 等以 `sdk.zsh`/`aliases.zsh` 源码为准。
4. **被别名替换的原生命令**：`cat→bat`、`ls→lsd`、`top→htop`、`rm/cp/mv→-i` 等见 `aliases.zsh`；脚本中需原生行为时用 `command cat` 等形式。

## 修改与验收流程

1. 改完后逐文件跑语法检查（实测 `zsh -n` 多文件传参时只解析首个）：`for f in aliases.zsh fzf.zsh sdk.zsh dot_zshrc dot_zimrc; do zsh -n "$f" || exit 1; done`（或 `zsh -n ~/.config/zsh/.zshrc`）
2. 干净启动验证无报错：`zsh -ic 'exit'`
3. 抽查关键定义：`zsh -ic 'type k df du; echo $EDITOR; echo $LANG'`
4. 提交：小步提交，说明动机；重大重构前先打 tag 以便回退（本仓库历史上并无 `baseline` 标签，不要创建同名标签造成混淆）。
