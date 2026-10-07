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

前缀可叠加，如 `private_dot_ssh` = 隐藏目录 + 该目录本身权限 0700。

> 注：`private_` 前缀只作用于它直接修饰的那一级——目录得 0700、文件得 0600，目录内未再带前缀的子项保持默认 0644。
> `dot_config`、`fish` 无 `private_` 前缀，目标为默认权限 0755；`private_dot_ssh` 声明对应目标目录为 0700；未加 `private_` 的子文件默认 0644。`dot_pi/agent` 没有私有前缀，默认目录属性为 0755、文件为 0644，不能据历史 `stat` 推断当前部署权限。`~/.ssh/config` 的源文件本身带前缀，目标为 0600；Codex 参考文件不部署（由 `.chezmoiignore` 的 `.codex/config.toml` 按目标名排除）。

## 完整映射表

### Shell 与 Git

| 源文件 | 目标路径 | 说明 |
| --- | --- | --- |
| `symlink_dot_zshrc.tmpl` | `~/.zshrc` → `~/.config/zsh/.zshrc` | 模板符号链接（内容为 `{{ .chezmoi.homeDir }}/.config/zsh/.zshrc`，XDG 收敛，兼容 ~/.zshrc 路径） |
| `symlink_dot_zimrc.tmpl` | `~/.zimrc` → `~/.config/zsh/.zimrc` | 同上（Zim 读取 ~/.zimrc 符号链接，真实文件在 ~/.config/zsh） |
| `dot_config/zsh/dot_zshrc` | `~/.config/zsh/.zshrc` | Zsh 入口：Zim 引导、PATH、工具 eval（zoxide/mise/starship/fzf/brew）、模块加载入口（aliases→fzf→sdk）—— 真实文件，symlink 目标 |
| `dot_config/zsh/dot_zimrc` | `~/.config/zsh/.zimrc` | Zim 模块清单（仅供 zimfw 读取，非 shell 启动时 source）—— 真实文件 |
| `dot_gitconfig` | `~/.gitconfig` | 用户/代理（github.com 走 socks5h://127.0.0.1:5376，socks5h 由代理端解析 DNS）/LFS/push 行为；`core.excludesfile = ~/.gitignore_global`（`~` 由 git 原生展开，无用户名硬编码）。旧版 `.chezmoiignore` 中按源名书写的 `dot_gitconfig` 行从不匹配任何目标、未生效，现该行已删除，本文件正常随 `apply` 部署 |
| `dot_gitignore_global` | `~/.gitignore_global` | 全局忽略（.DS_Store、IDE、日志等） |

### SSH

| 源文件 | 目标路径 | 说明 |
| --- | --- | --- |
| `private_dot_ssh/private_config` | `~/.ssh/config` (0600) | OrbStack `Include ~/.orbstack/ssh/config` 置顶 + `Host github.com` 走 `ssh.github.com:443` + SOCKS5 自适应（`nc -z 127.0.0.1:5376` 探测，有则 `-X 5 -x 127.0.0.1:5376` 否则直连） |
| `private_dot_ssh/private_sockets/.keep` | `~/.ssh/sockets/` (0700) | ControlPath socket 目录占位（.keep 本身不部署，仅目录属性生效） |
| `private_dot_ssh/private_agent/.keep` | `~/.ssh/agent/` (0700) | 预留占位目录 |

### ~/.config/zsh/（XDG 收敛：入口 + 三模块）

| 源文件 | 目标路径 | 说明 |
| --- | --- | --- |
| `dot_config/zsh/dot_zshrc` | `~/.config/zsh/.zshrc` | Zsh 入口：Zim 引导、PATH、工具 eval（zoxide/mise/starship/fzf/brew）、模块加载入口（aliases→fzf→sdk）—— 与 `symlink_dot_zshrc.tmpl` 配合 |
| `dot_config/zsh/dot_zimrc` | `~/.config/zsh/.zimrc` | Zim 模块清单（仅供 zimfw 读取，非 shell 启动时 source）—— 与 `symlink_dot_zimrc.tmpl` 配合 |
| `dot_config/zsh/aliases.zsh` | `~/.config/zsh/aliases.zsh` | 别名与通用函数（`update-all`、`auto-update`、`y`、`ruff_auto` 等）；`update-all` 为关联数组 7 目标 `brew`/`sdk`/`rustup`/`tldr`/`uv`/`mise`/`pi`，支持传参过滤、失败计数与耗时统计；`auto-update` 为兼容旧习惯的一键入口（可选 `onproxy` 切代理后直接委托 `update-all`，覆盖目标一致，均含 `mise`）；新增 `chezc/chezdf/chezap` 三别名 |
| `dot_config/zsh/fzf.zsh` | `~/.config/zsh/fzf.zsh` | fzf 前缀探测/缓存、全局选项、Ctrl-R/T/Alt-C 及 `frg`/`fkill`/`ftm`/`fl*` 函数 |
| `dot_config/zsh/sdk.zsh` | `~/.config/zsh/sdk.zsh` | SDK 环境与补全（pnpm/SDKMAN(可选)/Android NDK/Python(uv)/Go/Rust/Docker/kubectl+kubecolor） |
| `dot_config/zsh/README.md` | —（不部署） | 模块内部文档（加载顺序契约、函数速查）；由 `**/*.md` 排除，仅仓库内查阅 |

### 终端与提示符

| 源文件 | 目标路径 | 说明 |
| --- | --- | --- |
| `dot_config/ghostty/config` | `~/.config/ghostty/config` | Ghostty 主终端配置（JetBrainsMonoNL Nerd Font Mono，`command = /opt/homebrew/bin/fish -l` 启动登录 Fish，Catppuccin Mocha 主题；`zsh -l` / `tmux` 方案注释保留） |
| `dot_config/alacritty/alacritty.toml` | `~/.config/alacritty/alacritty.toml` | Alacritty 备用配置（活跃配色为 Catppuccin Mocha，Dracula 调色板整块注释保留为模板；`shell = fish -c "tmux new -A -s main"` 经 Fish 进 tmux） |
| `dot_config/kitty/kitty.local.conf` | —（不部署，机器本地维护） | kitty 增量个人配置（字体/光标/Catppuccin Mocha/快捷键，`shell = fish`）仅入库作参考，不随 apply 部署（被 `.chezmoiignore` 的 `**/*.local.*` 排除，`chezmoi ignored` 含 `.config/kitty/kitty.local.conf`）；目标机 `~/.config/kitty/kitty.local.conf` 各机本地维护，在 kitty 首次生成的 `~/.config/kitty/kitty.conf` 末尾手工添加 `include kitty.local.conf` 引入（仓库有意不含 kitty.conf） |
| `dot_tmux.conf` | `~/.tmux.conf` | tmux 配置：`default-shell` 经 if-shell 回退链设定（Homebrew fish → `/usr/bin/fish` → `/bin/bash`，无 fish 环境自动回退；不设 default-command，保持登录语义）、tpm 插件（yank/sensible/open/cpu/battery）、Catppuccin Mocha 状态栏、鼠标与 100k 历史 |
| （starship.toml 不在仓库） | `~/.config/starship.toml`（机器本地） | Starship 提示符配置未入库（已于 0ad1efc 移除）；zsh/fish 两侧仅负责 `starship init`，跨机迁移需自行拷贝该文件 |

### 编辑器与开发工具

| 源文件 | 目标路径 | 说明 |
| --- | --- | --- |
| `dot_config/nvim/**` | `~/.config/nvim/**` | LazyVim 配置（`init.lua` + `lua/config/*` + `lua/plugins/*`、`lazyvim.json`（extras 声明的事实来源）、本地 colorscheme/Mason/Sidekick 插件 specs、`stylua.toml`；`lazy-lock.json` 已停止跟踪（3c3d65f），运行时生成不入库） |
| `dot_config/nvim/README.md` | —（不部署） | LazyVim 上游模板自带；由 `**/*.md` 排除，仅仓库内查阅（历史排除模式误写为 `**/REAMDME.md` 未生效，已修复） |
| `dot_config/mise/config.toml` | `~/.config/mise/config.toml` | mise 工具链声明（工具与版本见 `dot_config/mise/config.toml`） |
| （`private_dot_claude` 已移出仓库） | `~/.claude/settings.json`（各机本地维护） | Claude Code 设置已不入库（参照 .codex 模式：源已移出仓库，由各机本地维护；`.chezmoiignore` 的 `.claude/settings.json` 行为防御性保留） |
| `dot_codex/config.toml` | —（不部署，被 `.chezmoiignore` 的 `.codex/config.toml` 排除） | cc-switch 机器本地配置的参考快照（provider、hooks/projects trust 由各机 cc-switch 注入维护；仓库版本仅参考，实际生效值以各机 `~/.codex/config.toml` 为准） |

> `~/.config/gh/config.yml` 与 `hosts.yml` 由 `gh auth login` 在目标机生成，含凭据，**不入库**（见下文“不在仓库内的重要文件”）。

### Fish（辅助）

| 源文件 | 目标路径 | 说明 |
| --- | --- | --- |
| `dot_config/fish/config.fish` | `~/.config/fish/config.fish` (0644) | 交互配置：interactive 时 `starship init fish`（所在目录 `fish/` 无 `private_` 前缀，为默认权限 0755） |
| `.../completions/symlink_docker.fish` | `~/.config/fish/completions/docker.fish` | 符号链接 → OrbStack 内置补全 |
| `.../completions/symlink_kubectl.fish` | `~/.config/fish/completions/kubectl.fish` | 同上 |
| `.../completions/symlink_orbctl.fish` | `~/.config/fish/completions/orbctl.fish` | 同上 |
| `.../fish_plugins` | `~/.config/fish/fish_plugins` | Fisher 插件清单（13 个：fzf.fish、forgit、bass、done、autopair、sponge、puffer-fish 等） |
| `.../conf.d/`（`00_env` / `01_activate` / `10_sys` / `20_dev` / `21_k8s` / `22_rev`） | `~/.config/fish/conf.d/` | 六文件分层：编号表达加载阶段（0x 环境/激活 → 1x 系统基础 → 2x 领域）。`00_env.fish`（PATH 收敛/LANG/EDITOR/HOMEBREW_*/GOPATH）+ `01_activate.fish`（`type -q mise` 守卫激活，与 zsh 侧 `dot_zshrc` 的 activate 对应；另含 SDKMAN 惰性桩——经 edc/bass 转发 bash init，与 zsh 侧 `sdk.zsh` 同契约，未安装不定义）+ `10_sys.fish`（系统增强别名/导航/时间戳）+ `20_dev.fish`（开发工具）+ `21_k8s.fish`（k8s 别名）+ `22_rev.fish`（逆向）；fish 侧 fzf 键位由 fisher 插件 patrickf1/fzf.fish 提供（安装于 `~/.config/fish/fisher` = fisher_path，退出 chezmoi 管理域，config.fish 注入其 functions/completions/conf.d，不入库） |
| `.../functions/*`、`.../completions/*` | `~/.config/fish/functions/`、`~/.config/fish/completions/` | `functions/` 18 个惰性加载函数（update-all/auto-update、onproxy/ofproxy、y、serve、netcheck、makes/xargsp/__half_cpu_count、bak/timer/decide、find-large/dus/filestats/recent/tree-size；首次调用才 source，`__` 前缀 helper 被补全隐藏）；`completions/` 含 `kubecolor.fish`（complete --wraps kubectl）与三条 OrbStack 符号链接；fisher 插件仍安装于 `~/.config/fish/fisher` = fisher_path，退出 chezmoi 管理域，不写入仓库 |
| `.../themes/.keep` | —（`.keep` 仅保留空目录，不部署） | 主题目录占位 |
| `.../fish_variables` | —（已加入 `.chezmoiignore`，不部署） | fish Universal Variables 机器本地状态 |

> Fish 是 Ghostty 的登录 shell（`command = /opt/homebrew/bin/fish -l`）；Alacritty 经 `shell = fish -c "tmux new -A -s main"` 进入 tmux；tmux `default-shell` 同为 Fish（含 if-shell 回退链，无 fish 环境自动回退）。Zsh 栈（XDG 收敛 + Zim 三模块）完整保留为次选入口。Starship 提示符双侧复用；源部署 Fisher 的 13 插件**清单**与三条 OrbStack 补全链接，插件本体由 Fisher 在目标机安装。

### pi coding agent（三文件 allowlist）

| 源文件 | 目标路径 | 说明 |
| --- | --- | --- |
| `dot_pi/agent/settings.json` | `~/.pi/agent/settings.json` (0644) | 扩展包、默认 provider/tools/model 等 |
| `dot_pi/agent/pi-goal.json` | `~/.pi/agent/pi-goal.json` (0644) | Goal 扩展设置 |
| `dot_pi/workflows/settings.json` | `~/.pi/workflows/settings.json` (0644) | `ultracode` 触发与工作流并发/预算/进度等 |

> 上述目录无 `private_` 前缀，默认目标属性为 0755。仓库不含沙箱或工具权限矩阵；安全边界与忽略规则限制见 [dev-tools.md](dev-tools.md)。

## .chezmoiignore —— 排除部分源文件不参与部署

根目录的 `.chezmoiignore` 本身**不会**被 `chezmoi apply` 到 `$HOME`
（chezmoi 对该文件名特殊处理），作用是在源目录中**排除**部分文件不参与渲染（按目标名匹配）。完整排除列表以 `.chezmoiignore` 源文件为唯一权威，涵盖本地覆盖与备份（`*.local`/`*.bak`）、仓库文档（`README.md`/`LICENSE`/`docs/`）、敏感词（`**/*token*`/`**/*secret*`/`**/*credential*`/`**/auth.json*`/`**/hosts.yml`，`**/` 前缀使其覆盖嵌套目录）、构建产物（`node_modules/` 等）与 fish 机器本地状态等。

效果：`chezmoi diff` / `chezmoi apply` 自动跳过上述模式匹配的目标，避免污染家目录。

历史上的源名/目标名混淆与 README 拼写失配已修复。现在请以 `chezmoi managed` / `chezmoi ignored` 的实时输出为准：条目包含目录和脚本，不能把历史总数当作文件数或安全验收条件。新增验证资料（`docs/validation/`、[optimization.md](optimization.md)）仍由 `docs/` 整体排除；离线部署边界检查见 [validation/README.md](validation/README.md)。

## 仓库特性说明

- **极简模板**：仅有的 `*.tmpl` 是 `symlink_dot_zshrc.tmpl` / `symlink_dot_zimrc.tmpl`（各一行 `{{ .chezmoi.homeDir }}/.config/zsh/...`，将 `~/.zshrc` 收敛至 XDG）—— 其余全部为静态文件，无 `.chezmoidata.*` 数据；无 `run_*` 脚本（历史 `run_once_create-ssh-sockets.sh` 已删除，`~/.ssh/sockets` 改由 `private_dot_ssh/private_sockets/.keep` 目录属性管理，每次 apply 校验）。所有机器 `chezmoi apply` 拿到同一套内容；如需进一步按机器差异化，可在现有模板基础上扩展。
- **运行时产物不入库**：`~/.config/zsh/.gitignore` 与 `~/.config/nvim/.gitignore` 已停止管理（源树 `dot_gitignore` 已删除），运行时产物由各机自行忽略；fzf 前缀缓存位于 HOME/ZDOTDIR，不依赖任何托管 `.gitignore`。
- **仅服务于仓库管理、不部署的文件**：根目录的 `.gitignore` 与 `.chezmoiignore` 被 chezmoi 默认忽略（源目录中点开头文件不参与 apply）；根级 `README.md`、`docs/`（本文档所在）以及全部嵌套 `README.md`（如 `zsh/README.md`、`nvim/README.md`）被 `.chezmoiignore` 排除；根级与 `nvim/LICENSE` 文件已删除，`**/LICENSE` 模式防御性保留。
- **不在仓库内的重要文件**：
  - `~/.config/gh/hosts.yml` / `config.yml`——由 `gh auth login` 生成，含凭据，切勿加入仓库；
  - `~/.zim/`——由 zimfw 自动管理（`~/.config/zsh/.zimrc` 仅为其配置，`~/.zimrc` 为符号链接）；
  - `~/.ssh/` 除 `config` 外的密钥——不在仓库内，切勿添加；`.chezmoiignore` 只影响部署，不能防止 Git 提交，也不会按内容识别密钥；
  - Neovim 插件本体（`~/.local/share/nvim/`）——由 lazy.nvim 安装（`lazy-lock.json` 为目标机运行时产物，已不入库）。
