# Shell 栈：Zsh / Zim / Starship / Fish

## 启动链路

交互式 zsh 启动时按以下顺序执行（`~/.zshrc` 经 `symlink_dot_zshrc.tmpl` 指向 `~/.config/zsh/.zshrc`，源码为 `dot_config/zsh/dot_zshrc`）。顺序即语义——同名定义后加载者生效，例如 `k` 别名由 `sdk.zsh` 按需定义，因此 `aliases.zsh` 有意不定义 `k`。

1. **Zim 引导**：缺失时下载 zimfw，随后 `zimfw init` 生成并加载 `~/.zim/init.zsh`（含补全、高亮、自动建议等）。
2. **PATH 注入**：前置 `~/bin`、Homebrew、`/usr/local/bin`、`~/.local/bin` 等，并按目录存在性守卫注入 cargo/rustup 路径。
3. **工具初始化**：`zoxide` / `mise` / `starship` 按 `command -v` 守卫顺序 `eval` 初始化，未安装静默跳过；`brew shellenv` 由 Zim 的 `zimfw/homebrew` 模块在 init.zsh 阶段注入（早于 rustup 守卫，避免重复 eval）；`fzf` 键位绑定唯一收敛于 `fzf.zsh`（`~/.zshrc` 不再重复）。
4. **三模块加载**：依次 `source` `aliases.zsh`（导出 `$EDITOR`/`$VISUAL`）→ `fzf.zsh`（依赖 `$EDITOR` 的 Ctrl-G 绑定）→ `sdk.zsh`（惰性加载 SDKMAN、缓存补全等）。
5. **SDK 环境**：`sdk.zsh` 无条件加载，内部逐项守卫（SDKMAN 惰性、kubectl/docker 补全缓存）。SDKMAN 初始化失败不再递归，重 source 不替换已初始化函数。补全缓存按真实路径/stat 身份失效；每工具内建 flock 覆盖检查、发布与加载，compiled artifact 以最终源码名生成。

完整命令与守卫细节以 `dot_config/zsh/dot_zshrc` 与三模块源文件为准，模块契约详见 [`dot_config/zsh/README.md`](../dot_config/zsh/README.md)。

> **环境变量说明**：`dot_config/zsh/dot_zshrc` 顶部的 `export LANG=zh_CN.UTF-8` 生效，与 Ghostty 的 `LANG=zh_CN.UTF-8` 一致，统一中文 UTF-8 locale。`$EDITOR`/`$VISUAL` 由 `aliases.zsh` 导出。

## Zim 模块清单（dot_config/zsh/dot_zimrc）

Zim 模块由 `dot_config/zsh/dot_zimrc`（经 `symlink_dot_zimrc.tmpl` 部署为 `~/.zimrc` → `~/.config/zsh/.zimrc`）定义，按环境、提示符、补全、收尾四组组织，通过 `zimfw` 加载。核心包括基础环境（`environment`/`utility` 等）、提示符信息（`duration-info`/`git-info`/`prompt-pwd`/`asciiship`）以及补全链（Homebrew 自适应路径、`zsh-completions`、`completion`、`fzf-tab`）。收尾模块为语法高亮、历史子串搜索与自动建议。`asciiship` 实际被 Starship 覆盖，保留仅作信息源。完整清单、加载顺序与注释掉的未启用模块以 `dot_zimrc` 源码为唯一权威。

> 已设置 `ZSH_AUTOSUGGEST_MANUAL_REBIND=1` 以提升末尾模块性能；历史的 `ZSH_HIGHLIGHT_HIGHLIGHTERS` 配置因子模块未启用而删除。

## Starship 提示符（机器本地 starship.toml）

Starship 由 zsh（`eval "$(starship init zsh)"`）与 fish（`config.fish` 内 `starship init fish`）双侧初始化；提示符配置 `starship.toml` **不在仓库内**（已于 0ad1efc 移除），实际位于机器本地 `~/.config/starship.toml`（Catppuccin Mocha 单行 powerline 布局）。跨机迁移需自行拷贝该文件；仓库侧仅保证 starship 二进制与初始化路径可用。

## fzf 集成要点（fzf.zsh）

`dot_config/zsh/fzf.zsh` 统一管理 fzf 初始化、全局选项与交互函数，详见源文件与 [`dot_config/zsh/README.md`](../dot_config/zsh/README.md)。

### 前缀探测与缓存

fzf 前缀按平台自适应探测（Apple Silicon `/opt/homebrew` → Intel `/usr/local` → `~/.fzf` → `/usr`），结果缓存至 `~/.cache/zsh/fzf_prefix` 并支持自愈重探；探测后按需追加至 `$PATH`，随后带守卫地 `eval "$(fzf --zsh)"` 初始化键位与补全。该 `eval` 是全链路中 fzf 键位的唯一初始化点。具体测试条件与缓存文件名以 `fzf.zsh` 为准。

### 文件/目录列表命令

`FZF_DEFAULT_COMMAND` / `FZF_ALT_C_COMMAND` / `FZF_CTRL_T_COMMAND` 的实际命令（含 `fd` 主力与 `rg` 兜底、排除列表）均在 `fzf.zsh` 中定义，通过 `exclude_list` 变量展开。以源文件 `dot_config/zsh/fzf.zsh` 为唯一权威。

### 全局键位与选项

`FZF_DEFAULT_OPTS`（布局、颜色、全部键位绑定）集中在 `fzf.zsh` 中定义——**键位绑定直接写在源文件里，以 `fzf.zsh` 源码为准**，本节不再逐字抄录。要点：

- 编辑器打开键位原为 `ctrl-o`，现改为 `ctrl-g`（`ctrl-g:execute($EDITOR -- {} >/dev/tty 2>&1)`，`$EDITOR` 由 `aliases.zsh` 导出）；
- 原 `ctrl-e:execute(code {} &> /dev/tty)` 的 VS Code 打开绑定已**注释**（仅保留注释行，不再生效）；
- 保留 Tab/Shift-Tab 默认多选切换行为，不重绑定为纯移动。

专项 `FZF_CTRL_R_OPTS` / `FZF_CTRL_T_OPTS` / `FZF_ALT_C_OPTS`（排序、预览、提示语等）亦在同文件中定义，以源文件为准。

### 交互函数

`fzf.zsh` 提供 `frg`（内容搜索预览并跳转）、`fkill`/`find_large_files`/`ftm`（进程/大文件/tmux 会话）以及 `flf`/`flkill`/`flnet`/`fluser`（`lsof` 浏览）等交互函数，函数列表与依赖见源文件 `dot_config/zsh/fzf.zsh`。预览共享 `LSOF_PREVIEW` 片段（直接使用 fzf 的 PID 字段，不再启动 awk）。`fkill`/`flkill` 在发信号前校验全部正整数 PID 并去重；`frg` 拒绝非正整数行号，避免文件名中的冒号变成 Neovim `+Ex` 命令，含冒号文件名仍不支持可靠导航。详见源文件。

### 包管理更新函数（aliases.zsh）

`auto-update` 与 `update-all` 定义于 `dot_config/zsh/aliases.zsh`，前者为兼容旧习惯的一键入口（可选 `onproxy` 后委托后者），后者为关联数组驱动的批量更新（支持参数过滤、失败计数与耗时统计）。覆盖目标、任务定义与彩色输出细节均以 `aliases.zsh` 源文件为准，详见 [dev-tools.md](dev-tools.md) 与源文件。

### fzf-tab

`Aloxaf/fzf-tab` 由 `dot_config/zsh/dot_zimrc` 经 zimfw 加载，`fzf.zsh` 仅保留 `zstyle` 配置（补全排序、描述格式、颜色、`fzf-preview`、`fzf-flags` 等）。完整 `zstyle` 列表以 `fzf.zsh` 为唯一权威。普通 fzf 动作使用 `sh -c`；fzf-tab 的 CLI flags 单独覆盖为 `zsh -f -c`，因为其预览初始化包含 Zsh 专属语法。

## Fish 的角色

Fish 是 Ghostty 的登录 shell：Ghostty 以 `command = /opt/homebrew/bin/fish -l` 启动（`zsh -l` / `tmux` 方案注释保留）；Alacritty 经 `shell = { program = "/opt/homebrew/bin/fish", args = ["-c", "tmux new -A -s main"] }` 进入 tmux；kitty 以 `shell = /opt/homebrew/bin/fish --login --interactive` 固定（kitty 主配置为机器本地维护，仓库仅保留 kitty.local.conf 作参考、不参与部署）；tmux `default-shell` 亦为 Fish——四终端（Ghostty/Alacritty/kitty/tmux）均为 Fish。Zsh 栈（XDG 收敛 + Zim 三模块）完整保留为次选入口（`~/.zshrc` 经 symlink 指向 `~/.config/zsh/.zshrc`）。仓库中 `dot_config/fish/`（部署后为 `~/.config/fish/`）提供：`config.fish` 在 interactive 时初始化 Starship 与 zoxide，`fish_plugins`（13 插件）声明插件清单，fisher 将插件安装于 `~/.config/fish/fisher`（`fisher_path`，退出 chezmoi 管理域），`config.fish` 把其 functions/completions/conf.d 注入搜索路径；`conf.d` 六文件分层（00_env/01_activate/10_sys/20_dev/21_k8s/22_rev）承载环境与别名，可调用大函数（update-all、onproxy、y、serve 等 18 个）在仓库 `functions/` 惰性加载（首次调用才 source），`completions/` 含 kubecolor 补全与 OrbStack docker/kubectl/orbctl symlink 补全。Fish 侧已初始化 Starship、zoxide（`config.fish` 的 `zoxide init fish` 与 fzf_zoxide 插件）与 fzf 键位（fzf.fish 插件经 fisher_path 生效，不写入仓库 functions/）；mise 已双侧接入（zsh 侧 `dot_zshrc` 的 `eval "$(mise activate zsh)"` + fish 侧 `conf.d/01_activate.fish` 守卫激活）；SDKMAN 惰性桩两侧对齐（zsh 原生接管式；fish 经 edc/bass 转发 bash init，导出变量差量回传），详见 `dot_config/fish/` 源目录与 [layout.md](layout.md)。

## 双侧对齐契约与已知不对称（有意保留）

安全与环境契约已双侧对齐：`rm/cp/mv -i` 护栏、可移植时间戳别名、`LANG`/`EDITOR`/`VISUAL` 继承守卫、`HOMEBREW_NO_*` 静默标志、代理回环豁免（`no_proxy`/`NO_PROXY`）、k8s 快捷别名集、`ws`/`wp` 目录跳转、`du -h -d 2` profile、`wget -c`、编辑器别名（`v/vi/vim/nv/nvi`）、`format`（biome）、update-all 记账（attempted/skipped/failed）与 `rustup` 目标名互认（fish 侧接受 `rustup`≈`rust`）。行为改变型别名两侧同为交互 shell 专属（zsh 经 `.zshrc` 交互加载语义，fish 经 `status is-interactive` 门控）。

以下不对称为有意保留（port 与否以使用场景为准，勿机械同步）：

| 不对称项 | zsh 侧 | fish 侧 | 说明 |
| --- | --- | --- | --- |
| 工具快捷别名 | 无 | `go*`（gob/goi/gom/gomt/gor/got）、`mvn*`、`pip*`、`pnp*`、`cb/cc/ccl/cr/ct/cu`、`redis-cli`、`mongo-local` 等 22 个 | fish 是四终端主力交互 shell，日常快捷别名集中在此；zsh 为维护中的次选入口 |
| AI 入口命名 | `cla_cfg` / `clp_cfg` | `claconfig` / `clpconfig` | 同义不同名，各自历史习惯 |
| `lt` / `finder` / `iterm*` / `fishsource` / 剪贴板 `cb*` | 无 | 有 | fish 侧专属 |
| `k` 定义点 | `sdk.zsh` 函数包装（kubecolor→kubectl + compdef） | `21_k8s.fish` 别名直指 kubecolor | 两侧等价，机制随 shell 惯例 |
| update-all stderr | 捕获 + 失败末 5 行摘要（`2>!` mktemp） | 实时透传 | fish 无 NO_CLOBBER/mktemp 模板约束 |
| Rust 目标名 | 仅 `rustup` | `rust`（另接受 `rustup`） | fish 保持短名，兼容 zsh 肌肉记忆 |
| fzf 环境/键位 | `fzf.zsh` 前缀探测 + `fzf --zsh` | fisher 插件 `patrickf1/fzf.fish` | 各随生态惯例，`FZF_DEFAULT_*` 子集 fish 侧不设 |
