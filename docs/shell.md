# Shell 栈：Zsh / Zim / Starship / Fish

## 启动链路

交互式 zsh 启动时按以下顺序执行（`~/.zshrc` 经 `symlink_dot_zshrc.tmpl` 指向 `~/.config/zsh/.zshrc`，源码为 `private_dot_config/zsh/dot_zshrc`）。顺序即语义——同名定义后加载者生效，例如 `k` 别名由 `sdk.zsh` 按需定义，因此 `aliases.zsh` 有意不定义 `k`。

1. **Zim 引导**：缺失时下载 zimfw，随后 `zimfw init` 生成并加载 `~/.zim/init.zsh`（含补全、高亮、自动建议等）。
2. **PATH 注入**：前置 `~/bin`、Homebrew、`/usr/local/bin`、`~/.local/bin` 等，并按目录存在性守卫注入 cargo/rustup 路径。
3. **工具初始化**：`zoxide` / `mise` / `starship` 按 `command -v` 守卫顺序 `eval` 初始化，未安装静默跳过；`brew shellenv` 由 Zim 的 `zimfw/homebrew` 模块在 init.zsh 阶段注入（早于 rustup 守卫，避免重复 eval）；`fzf` 键位绑定唯一收敛于 `fzf.zsh`（`~/.zshrc` 不再重复）。
4. **三模块加载**：依次 `source` `aliases.zsh`（导出 `$EDITOR`/`$VISUAL`）→ `fzf.zsh`（依赖 `$EDITOR` 的 Ctrl-G 绑定）→ `sdk.zsh`（惰性加载 SDKMAN、缓存补全等）。
5. **SDK 环境**：`sdk.zsh` 无条件加载，内部逐项守卫（SDKMAN 惰性、kubectl/docker 补全缓存）。

完整命令与守卫细节以 `private_dot_config/zsh/dot_zshrc` 与三模块源文件为准，模块契约详见 [`private_dot_config/zsh/README.md`](../private_dot_config/zsh/README.md)。

> **环境变量说明**：`private_dot_config/zsh/dot_zshrc` 顶部的 `export LANG=zh_CN.UTF-8` 生效，与 Ghostty 的 `LANG=zh_CN.UTF-8` 一致，统一中文 UTF-8 locale。`$EDITOR`/`$VISUAL` 由 `aliases.zsh` 导出。

## Zim 模块清单（private_dot_config/zsh/dot_zimrc）

Zim 模块由 `private_dot_config/zsh/dot_zimrc`（经 `symlink_dot_zimrc.tmpl` 部署为 `~/.zimrc` → `~/.config/zsh/.zimrc`）定义，按环境、提示符、补全、收尾四组组织，通过 `zimfw` 加载。核心包括基础环境（`environment`/`utility` 等）、提示符信息（`duration-info`/`git-info`/`prompt-pwd`/`asciiship`）以及补全链（Homebrew 自适应路径、`zsh-completions`、`completion`、`fzf-tab`）。收尾模块为语法高亮、历史子串搜索与自动建议。`asciiship` 实际被 Starship 覆盖，保留仅作信息源。完整清单、加载顺序与注释掉的未启用模块以 `dot_zimrc` 源码为唯一权威。

> 已设置 `ZSH_AUTOSUGGEST_MANUAL_REBIND=1` 以提升末尾模块性能；历史的 `ZSH_HIGHLIGHT_HIGHLIGHTERS` 配置因子模块未启用而删除。

## Starship 提示符（机器本地 starship.toml）

Starship 由 zsh（`eval "$(starship init zsh)"`）与 fish（`config.fish` 内 `starship init fish`）双侧初始化；提示符配置 `starship.toml` **不在仓库内**（已于 0ad1efc 移除），实际位于机器本地 `~/.config/starship.toml`（Catppuccin Mocha 单行 powerline 布局）。跨机迁移需自行拷贝该文件；仓库侧仅保证 starship 二进制与初始化路径可用。

## fzf 集成要点（fzf.zsh）

`private_dot_config/zsh/fzf.zsh` 统一管理 fzf 初始化、全局选项与交互函数，详见源文件与 [`private_dot_config/zsh/README.md`](../private_dot_config/zsh/README.md)。

### 前缀探测与缓存

fzf 前缀按平台自适应探测（Apple Silicon `/opt/homebrew` → Intel `/usr/local` → `~/.fzf` → `/usr`），结果缓存至 `~/.fzf_prefix_cache` 并支持自愈重探；探测后按需追加至 `$PATH`，随后带守卫地 `eval "$(fzf --zsh)"` 初始化键位与补全。该 `eval` 是全链路中 fzf 键位的唯一初始化点。具体测试条件与缓存文件名以 `fzf.zsh` 与 `private_dot_config/zsh/dot_gitignore` 为准。

### 文件/目录列表命令

`FZF_DEFAULT_COMMAND` / `FZF_ALT_C_COMMAND` / `FZF_CTRL_T_COMMAND` 的实际命令（含 `fd` 主力与 `rg` 兜底、排除列表）均在 `fzf.zsh` 中定义，通过 `exclude_list` 变量展开。以源文件 `private_dot_config/zsh/fzf.zsh` 为唯一权威。

### 全局键位与选项

`FZF_DEFAULT_OPTS`（布局、颜色、全部键位绑定）集中在 `fzf.zsh` 中定义——**键位绑定直接写在源文件里，以 `fzf.zsh` 源码为准**，本节不再逐字抄录。要点：

- 编辑器打开键位原为 `ctrl-o`，现改为 `ctrl-g`（`ctrl-g:execute($EDITOR {} &> /dev/tty)`，`$EDITOR` 由 `aliases.zsh` 导出）；
- 原 `ctrl-e:execute(code {} &> /dev/tty)` 的 VS Code 打开绑定已**注释**（仅保留注释行，不再生效）；
- 保留 Tab/Shift-Tab 默认多选切换行为，不重绑定为纯移动。

专项 `FZF_CTRL_R_OPTS` / `FZF_CTRL_T_OPTS` / `FZF_ALT_C_OPTS`（排序、预览、提示语等）亦在同文件中定义，以源文件为准。

### 交互函数

`fzf.zsh` 提供 `frg`（内容搜索预览并跳转）、`fkill`/`find_large_files`/`ftm`（进程/大文件/tmux 会话）以及 `flf`/`flkill`/`flnet`/`fluser`（`lsof` 浏览）等交互函数，函数列表与依赖见源文件 `private_dot_config/zsh/fzf.zsh`。预览共享 `LSOF_PREVIEW` 片段，详见源文件。

### 包管理更新函数（aliases.zsh）

`auto-update` 与 `update-all` 定义于 `private_dot_config/zsh/aliases.zsh`，前者为兼容旧习惯的一键入口（可选 `onproxy` 后委托后者），后者为关联数组驱动的批量更新（支持参数过滤、失败计数与耗时统计）。覆盖目标、任务定义与彩色输出细节均以 `aliases.zsh` 源文件为准，详见 [dev-tools.md](dev-tools.md) 与源文件。

### fzf-tab

`Aloxaf/fzf-tab` 由 `private_dot_config/zsh/dot_zimrc` 经 zimfw 加载，`fzf.zsh` 仅保留 `zstyle` 配置（补全排序、描述格式、颜色、`fzf-preview`、`fzf-flags` 等）。完整 `zstyle` 列表以 `fzf.zsh` 为唯一权威。

## Fish 的角色

Fish 是 Ghostty 的登录 shell：Ghostty 以 `command = /opt/homebrew/bin/fish -l` 启动（`zsh -l` / `tmux` 方案注释保留）；Alacritty 经 `shell = { program = "/opt/homebrew/bin/fish", args = ["-c", "tmux new -A -s main"] }` 进入 tmux；kitty 以 `shell = /opt/homebrew/bin/fish --login --interactive` 固定；tmux `default-shell` 亦为 Fish——四终端（Ghostty/Alacritty/kitty/tmux）均为 Fish。Zsh 栈（XDG 收敛 + Zim 三模块）完整保留为次选入口（`~/.zshrc` 经 symlink 指向 `~/.config/zsh/.zshrc`）。仓库中 `private_dot_config/private_fish/`（chezmoi `private_` 前缀，部署后为 `~/.config/fish/`）提供：`config.fish` 在 interactive 时初始化 Starship 与 zoxide，`fish_plugins`（13 插件）经 fisher 管理 fzf.fish 等插件，`conf.d` 四文件（00_env/00_aliases/01_dev/01_rev）承载环境与函数（fish 侧 fzf 键位由 fisher 插件 patrickf1/fzf.fish 运行时生成 conf.d/fzf.fish，不入库），`symlink_` 保留 OrbStack 的 docker/kubectl/orbctl 补全。Fish 侧已初始化 Starship、zoxide（`config.fish` 的 `zoxide init fish` 与 fzf_zoxide 插件）与 fzf 键位，未接入 mise/brew 等 zsh 栈（mise 仅 zsh 侧 activate），详见 `private_dot_config/private_fish/` 源目录与 [layout.md](layout.md)。
