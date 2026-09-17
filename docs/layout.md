# 文件映射与命名约定

本仓库是 chezmoi 的源目录（`~/.local/share/chezmoi`）。chezmoi 通过文件名前缀编码目标路径与属性，
`chezmoi apply` 时按规则渲染到 `$HOME`。

## chezmoi 命名约定速查

| 前缀 | 含义 | 本仓库示例 |
| --- | --- | --- |
| `dot_` | 目标名以 `.` 开头（隐藏目录/文件） | `dot_zshrc` → `~/.zshrc` |
| `private_` | 目标仅所有者可访问：文件 0600、目录 0700 | `private_dot_ssh/private_config` → `~/.ssh/config` (0600) |
| `symlink_` | 目标是符号链接，**文件内容即链接指向的路径** | `symlink_docker.fish` 内容为一行 OrbStack 路径 |
| （无前缀） | 原样同名复制 | `fish_plugins` → `~/.config/fish/fish_plugins` |

前缀可叠加，如 `private_dot_config` = 隐藏目录 + 该目录本身权限 0700，`private_dot_ssh` 同理。

> 注：`private_` 前缀只作用于它直接修饰的那一级——目录得 0700、文件得 0600，目录内未再带前缀的子项保持默认 0644。
> 实测（stat）：`~/.config`、`~/.config/fish`、`~/.pi`、`~/.pi/agent` 均为 0700，而其内部文件（`config.fish`、
> `~/.pi/agent/*.json` 等）均为 0644；仅文件本身带前缀的 `~/.ssh/config` 为 0600（`~/.codex/config.toml` 源文件同为
> `private_` 0600，但已被 `.chezmoiignore` 排除不再部署，见下文 Codex 行）。

## 完整映射表

### Shell 与 Git

| 源文件 | 目标路径 | 说明 |
| --- | --- | --- |
| `symlink_dot_zshrc.tmpl` | `~/.zshrc` → `~/.config/zsh/.zshrc` | 模板符号链接（内容为 `{{ .chezmoi.homeDir }}/.config/zsh/.zshrc`，XDG 收敛，兼容 ~/.zshrc 路径） |
| `symlink_dot_zimrc.tmpl` | `~/.zimrc` → `~/.config/zsh/.zimrc` | 同上（Zim 读取 ~/.zimrc 符号链接，真实文件在 ~/.config/zsh） |
| `private_dot_config/zsh/dot_zshrc` | `~/.config/zsh/.zshrc` | Zsh 入口：Zim 引导、PATH、工具 eval（zoxide/mise/starship/fzf/brew）、模块加载入口（aliases→fzf→sdk）—— 真实文件，symlink 目标 |
| `private_dot_config/zsh/dot_zimrc` | `~/.config/zsh/.zimrc` | Zim 模块清单（仅供 zimfw 读取，非 shell 启动时 source）—— 真实文件 |
| `dot_gitconfig` | `~/.gitconfig` | 用户/代理（github.com 走 socks5h://127.0.0.1:5376，socks5h 由代理端解析 DNS）/LFS/push 行为；`core.excludesfile = ~/.gitignore_global`（`~` 由 git 原生展开，无用户名硬编码）。旧版 `.chezmoiignore` 中按源名书写的 `dot_gitconfig` 行从不匹配任何目标、未生效，现该行已删除，本文件正常随 `apply` 部署 |
| `dot_gitignore_global` | `~/.gitignore_global` | 全局忽略（.DS_Store、IDE、日志等） |

### SSH

| 源文件 | 目标路径 | 说明 |
| --- | --- | --- |
| `private_dot_ssh/private_config` | `~/.ssh/config` (0600) | OrbStack `Include ~/.orbstack/ssh/config` 置顶 + `Host github.com` 走 `ssh.github.com:443` + SOCKS5 自适应（`nc -z 127.0.0.1:5376` 探测，有则 `-X 5 -x 127.0.0.1:5376` 否则直连） |

### ~/.config/zsh/（XDG 收敛：入口 + 三模块）

| 源文件 | 目标路径 | 说明 |
| --- | --- | --- |
| `private_dot_config/zsh/dot_zshrc` | `~/.config/zsh/.zshrc` | Zsh 入口：Zim 引导、PATH、工具 eval（zoxide/mise/starship/fzf/brew）、模块加载入口（aliases→fzf→sdk）—— 与 `symlink_dot_zshrc.tmpl` 配合 |
| `private_dot_config/zsh/dot_zimrc` | `~/.config/zsh/.zimrc` | Zim 模块清单（仅供 zimfw 读取，非 shell 启动时 source）—— 与 `symlink_dot_zimrc.tmpl` 配合 |
| `private_dot_config/zsh/aliases.zsh` | `~/.config/zsh/aliases.zsh` | 别名与通用函数（`update-all`、`auto-update`、`y`、`ruff_auto` 等）；`update-all` 为关联数组 6 目标 `brew`/`sdk`/`rustup`/`tldr`/`uv`/`mise`，支持传参过滤、失败计数与耗时统计；`auto-update` 为兼容旧习惯的一键入口（可选 `onproxy` 切代理后直接委托 `update-all`，覆盖目标一致，均含 `mise`）；新增 `chezc/chezdf/chezap` 三别名 |
| `private_dot_config/zsh/fzf.zsh` | `~/.config/zsh/fzf.zsh` | fzf 前缀探测/缓存、全局选项、Ctrl-R/T/Alt-C 及 `frg`/`fkill`/`ftm`/`fl*` 函数 |
| `private_dot_config/zsh/sdk.zsh` | `~/.config/zsh/sdk.zsh` | SDK 环境与补全（pnpm/SDKMAN(可选)/Android NDK/Python(uv)/Go/Rust/Docker/kubectl+kubecolor） |
| `private_dot_config/zsh/dot_gitignore` | `~/.config/zsh/.gitignore` | 忽略运行时产物（`*.zwc`、`.fzf_prefix_cache`、`.DS_Store`） |
| `private_dot_config/zsh/README.md` | —（不部署） | 模块内部文档（加载顺序契约、函数速查）；由 `**/README.md` 排除，仅仓库内查阅 |

### 终端与提示符

| 源文件 | 目标路径 | 说明 |
| --- | --- | --- |
| `private_dot_config/ghostty/config` | `~/.config/ghostty/config` | Ghostty 主终端配置（JetBrainsMono Nerd Font Mono，`command = /opt/homebrew/bin/fish -l` 启动登录 Fish，Catppuccin Mocha 主题；`zsh -l` / `tmux` 方案注释保留） |
| `private_dot_config/alacritty/alacritty.toml` | `~/.config/alacritty/alacritty.toml` | Alacritty 备用配置（活跃配色为 Catppuccin Mocha，Dracula 调色板整块注释保留为模板；`shell = fish -c "tmux new -A -s main"` 经 Fish 进 tmux） |
| `private_dot_config/kitty/kitty.local.conf` | `~/.config/kitty/kitty.local.conf` | kitty 增量个人配置（字体/光标/Catppuccin Mocha/快捷键，`shell = fish`）；kitty 不会自动读取本文件，需在 kitty 首次生成的 `~/.config/kitty/kitty.conf` 末尾手工添加 `include kitty.local.conf` 引入（仓库有意不含 kitty.conf） |
| `dot_tmux.conf` | `~/.tmux.conf` | tmux 配置：`default-shell = /opt/homebrew/bin/fish`（登录语义，不设 default-command）、tpm 插件（yank/sensible/open/cpu/battery）、Catppuccin Mocha 状态栏、鼠标与 100k 历史 |
| （starship.toml 不在仓库） | `~/.config/starship.toml`（机器本地） | Starship 提示符配置未入库（已于 0ad1efc 移除）；zsh/fish 两侧仅负责 `starship init`，跨机迁移需自行拷贝该文件 |

### 编辑器与开发工具

| 源文件 | 目标路径 | 说明 |
| --- | --- | --- |
| `private_dot_config/nvim/**` | `~/.config/nvim/**` | LazyVim 配置（`init.lua` + `lua/config/*` + `lua/plugins/*`，含 `lazy-lock.json` 锁定 43 个插件、`lazyvim.json`（extras 清单当前为空，extras 实际由 `lua/config/lazy.lua` import 引入）、`stylua.toml`） |
| `private_dot_config/nvim/README.md` | —（不部署） | LazyVim 上游模板自带；由 `**/README.md` 排除，仅仓库内查阅（历史排除模式误写为 `**/REAMDME.md` 未生效，已修复） |
| `private_dot_config/nvim/LICENSE` | —（不部署） | 上游 LazyVim starter 原件（Apache-2.0，与根 LICENSE 同哈希）；由 `**/LICENSE` 排除 |
| `private_dot_config/nvim/dot_gitignore` | `~/.config/nvim/.gitignore` | 忽略插件数据等运行时目录 |
| `private_dot_config/mise/config.toml` | `~/.config/mise/config.toml` | mise 工具链声明（工具与版本见 `private_dot_config/mise/config.toml`） |
| `private_dot_claude/settings.json` | `~/.claude/settings.json` (0644) | Claude Code 设置（statusLine（bun 动态解析）、插件开关、环境变量、沙箱；`private_` 前缀作用于父目录，目录 0700、文件保持默认 0644） |
| `dot_codex/private_config.toml` | —（不部署，被 `.chezmoiignore` 的 `.codex/config.toml` 排除） | cc-switch 机器本地配置的参考快照（provider、hooks/projects trust 由各机 cc-switch 注入维护；仓库版本仅参考，实际生效值以各机 `~/.codex/config.toml` 为准） |

> `~/.config/gh/config.yml` 与 `hosts.yml` 由 `gh auth login` 在目标机生成，含凭据，**不入库**（见下文“不在仓库内的重要文件”）。

### Fish（辅助）

| 源文件 | 目标路径 | 说明 |
| --- | --- | --- |
| `private_dot_config/private_fish/config.fish` | `~/.config/fish/config.fish` (0644) | 交互配置：interactive 时 `starship init fish`（所在目录 `private_fish/` 本身为 0700） |
| `.../private_completions/symlink_docker.fish` | `~/.config/fish/completions/docker.fish` | 符号链接 → OrbStack 内置补全 |
| `.../private_completions/symlink_kubectl.fish` | `~/.config/fish/completions/kubectl.fish` | 同上 |
| `.../private_completions/symlink_orbctl.fish` | `~/.config/fish/completions/orbctl.fish` | 同上 |
| `.../fish_plugins` | `~/.config/fish/fish_plugins` | Fisher 插件清单（13 个：fzf.fish、forgit、bass、done、autopair、sponge、puffer-fish 等） |
| `.../private_conf.d/00_env.fish`、`00_aliases.fish`、`01_dev.fish`、`01_rev.fish` | `~/.config/fish/conf.d/` | 四件套：`00_env.fish`（PATH 收敛/LANG/EDITOR/HOMEBREW_*/kubecolor 补全/GOPATH）+ `00_aliases.fish`（别名与函数、update-all）+ `01_dev.fish`（开发工具）+ `01_rev.fish`（逆向/杂项）；fish 侧 fzf 键位由 fisher 插件 patrickf1/fzf.fish 运行时生成 conf.d/fzf.fish，不入库 |
| `.../private_functions/*`、`.../private_completions/*` | `~/.config/fish/functions/`、`~/.config/fish/completions/` | fzf.fish / fisher 插件函数与补全（`.keep` 占位与 `symlink_docker/kubectl/orbctl.fish` 三条 OrbStack 符号链接随源部署） |
| `.../themes/.keep` | —（`.keep` 仅保留空目录，不部署） | 主题目录占位 |
| `.../private_fish_variables` | —（已加入 `.chezmoiignore`，不部署） | fish Universal Variables 机器本地状态 |

> Fish 是 Ghostty 的登录 shell（`command = /opt/homebrew/bin/fish -l`）；Alacritty 经 `shell = fish -c "tmux new -A -s main"` 进入 tmux；tmux `default-shell` 同为 Fish。Zsh 栈（XDG 收敛 + Zim 三模块）完整保留为次选入口。Starship 提示符双侧复用；fisher 管理的 14 插件与 OrbStack docker/kubectl/orbctl 补全随源部署。

### pi coding agent（四件套 + workflows）

| 源文件 | 目标路径 | 说明 |
| --- | --- | --- |
| `private_dot_pi/private_agent/settings.json` | `~/.pi/agent/settings.json` (0644) | pi coding agent 主题、扩展包、默认 provider/tools/model、代理配置 |
| `private_dot_pi/private_agent/sandbox.json` | `~/.pi/agent/sandbox.json` (0644) | 文件系统与网络沙箱策略（读写 deny 规则、网络策略） |
| `private_dot_pi/private_agent/landstrip.json` | `~/.pi/agent/landstrip.json` (0644) | 子代理与任务权限配置 |
| `private_dot_pi/private_agent/extensions/pi-permission-system/config.json` | `~/.pi/agent/extensions/pi-permission-system/config.json` (0644) | 工具级权限矩阵（允许优先：默认 allow，敏感路径/高危命令 deny） |
| `private_dot_pi/workflows/settings.json` | `~/.pi/workflows/settings.json` (0644) | workflow 运行时配置（并发、进度面板） |

> 权限实测（stat）：`private_dot_pi`/`private_agent` 目录前缀使 `~/.pi`、`~/.pi/agent` 为 0700，其内文件（含 `extensions/**`）均为 0644；
> `workflows/` 目录无 `private_` 前缀，`~/.pi/workflows` 为 0755。

## .chezmoiignore —— 排除部分源文件不参与部署

根目录的 `.chezmoiignore` 本身**不会**被 `chezmoi apply` 到 `$HOME`
（chezmoi 对该文件名特殊处理），作用是在源目录中**排除**部分文件不参与渲染（按目标名匹配）。完整排除列表以 `.chezmoiignore` 源文件为唯一权威，涵盖本地覆盖与备份（`*.local`/`*.bak`）、仓库文档（`README.md`/`LICENSE`/`docs/`）、敏感词（`**/*token*`/`**/*secret*`/`**/*credential*`，`**/` 前缀使其覆盖嵌套目录）、构建产物（`node_modules/` 等）与 fish 机器本地状态等。

效果：`chezmoi diff` / `chezmoi apply` 自动跳过上述模式匹配的目标，避免污染家目录。

✅ 历史失配已修复（2026-08 收口）：旧版按**源名**书写了 `**/dot_git` / `**/dot_DS_Store` / `dot_gitconfig`
（模式按目标名匹配，从不命中 `.git` / `.DS_Store` / `.gitconfig`，均未生效），且 `**/README.md`
误拼为 `**/REAMDME.md`——现全部改写为目标名形式、删除无效行 `dot_gitconfig` 并追加 `**/LICENSE`。
`dot_gitconfig` → `~/.gitconfig` 恢复其本来的正常部署语义；`chezmoi managed`
目标数由 59 降至 55（不再包含嵌套 README×2、`nvim/LICENSE`）。后续去重又删除了被更宽模式
覆盖或已无对应文件的冗余行（根级 `README.md` / `LICENSE`、`docs/**`、`**/.git`、`*client_secret*`、
两条 `**.md` 与已不存在的 `REPO-INSIGHT.md`），`managed` 目标数保持 55 不变（核心 targets 不变），其后 fish 配置扩容实测曾达 81（纳入 `.config/fish/fish_variables` 后为 82，详见布局映射）；2026-09 zsh XDG 收敛（`dot_zshrc/dot_zimrc` → `private_dot_config/zsh/dot_*` + 2 条 `symlink_*.tmpl`）后核心再度上升；2026-09-04 `model-tiers.json` 入库，2026-09-07 又随提交 `3018345` 删除（`private_dot_pi/workflows/` 仅余 `settings.json`），同日 `private_dot_config/nvim/dot_neoconf.json` 亦删除，总计相应减二；2026-09-09 删 conf.d/fzf.fish、2026-09-15 增 kitty.local.conf、本次删 private_completions/sdk.fish（+1 kitty −1 sdk，总数不变），应为 85（核心 50 + fish 35，按目标路径是否以 `.config/fish` 开头划分，以重新实测为准）。

## 仓库特性说明

- **极简模板**：仅有的 `*.tmpl` 是 `symlink_dot_zshrc.tmpl` / `symlink_dot_zimrc.tmpl`（各一行 `{{ .chezmoi.homeDir }}/.config/zsh/...`，将 `~/.zshrc` 收敛至 XDG）—— 其余全部为静态文件，无 `.chezmoidata.*` 数据、无 `run_*` 脚本。所有机器 `chezmoi apply` 拿到同一套内容；如需进一步按机器差异化，可在现有模板基础上扩展。
- **运行时产物不入库**：`~/.config/zsh/.gitignore` 和 `~/.config/nvim/.gitignore`
  分别忽略 `*.zwc`、`.fzf_prefix_cache` 及插件数据目录。
- **仅服务于仓库管理、不部署的文件**：根目录的 `.gitignore` 与 `.chezmoiignore` 被 chezmoi 默认忽略（源目录中点开头文件不参与 apply）；根级 `README.md`、`LICENSE`、`docs/`（本文档所在）以及全部嵌套 `README.md` / `LICENSE`（如 `zsh/README.md`、`nvim/README.md`、`nvim/LICENSE`）被 `.chezmoiignore` 排除。
- **不在仓库内的重要文件**：
  - `~/.config/gh/hosts.yml` / `config.yml`——由 `gh auth login` 生成，含凭据，切勿加入仓库；
  - `~/.zim/`——由 zimfw 自动管理（`~/.config/zsh/.zimrc` 仅为其配置，`~/.zimrc` 为符号链接）；
  - `~/.ssh/` 除 `config` 外的密钥——不在仓库内，`.chezmoiignore` 的 `**/*secret*`/`**/*token*` 等模式可防止误入库；
  - Neovim 插件本体（`~/.local/share/nvim/`）——由 lazy.nvim 按 `lazy-lock.json` 安装。
