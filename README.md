# Dotfiles


基于 [chezmoi](https://www.chezmoi.io/) 管理的 macOS（Apple Silicon）个人开发环境配置。

本仓库是 chezmoi 的**源目录**（source directory，位于 `~/.local/share/chezmoi`），
通过 `chezmoi apply` 将文件渲染到 `$HOME` 下对应位置。主体为静态文件，仅有的模板是
`symlink_dot_zshrc.tmpl` / `symlink_dot_zimrc.tmpl`（各一行，将 `~/.zshrc`/`~/.zimrc` 指向
`~/.config/zsh/` 的 XDG 收敛），其余所见即所得；通过 `.chezmoiignore` 将根级与嵌套的
`README.md` / `LICENSE`、`docs/`、`*.local` / `*.bak` 等仅供仓库查阅或本地覆盖的文件排除在
部署之外，避免污染目标 HOME 目录。

## ✨ 特性总览

| 领域 | 方案 | 说明 |
| --- | --- | --- |
| Shell | Zsh + [Zim](https://zimfw.sh/) + 自有模块 | `aliases.zsh` / `fzf.zsh` / `sdk.zsh` 三模块化加载；`update-all` 批量更新（`brew`/`sdk`/`rustup`/`tldr`/`uv`/`mise`/`pi`，支持参数过滤与失败计数） |
| Fish | Fish + [Fisher](https://github.com/jorgebucaran/fisher) + Starship | Ghostty 登录 shell（`fish -l`，tmux `default-shell` 同步）；`fish_plugins` 锁定 13 个插件（fzf.fish / forgit / autopair / done 等），`conf.d` 五文件（含 `02_mise.fish` 守卫激活 mise）设定 PATH/LANG/EDITOR 等环境，补全含 OrbStack docker/kubectl/orbctl 符号链接 |
| 提示符 | [Starship](https://starship.rs/) | Catppuccin Mocha powerline 风格（`starship.toml` 为机器本地文件，未入库） |
| 模糊搜索 | fzf + fzf-tab + fd | Ctrl-R 历史、Ctrl-T 文件、Alt-C 目录、`frg`/`fkill`/`ftm`/`fl*` 交互函数 |
| 终端 | Ghostty（主力）/ Alacritty（备用） | Ghostty 使用 JetBrainsMonoNL，Alacritty 使用 JetBrainsMono Nerd Font Mono；Catppuccin Mocha 配色（Dracula 以注释模板保留于 alacritty） |
| 编辑器 | Neovim + [LazyVim](https://www.lazyvim.org/) | extras 由 `private_dot_config/nvim/lazyvim.json` 声明，本地插件见 `lua/plugins/`；插件由 lazy.nvim 自动安装（`lazy-lock.json` 未入库） |
| 运行时管理 | mise | 多运行时一键切换（工具清单见 `private_dot_config/mise/config.toml`） |
| Git 工作流 | git + gh (CLI) | LFS、GitHub 走本地 SOCKS5 代理、`push.default=current` + `autoSetupRemote` |
| SSH | OpenSSH `~/.ssh/config` | `ssh.github.com:443` + 自适应 `ProxyCommand`（探活 `127.0.0.1:5376` SOCKS5，失败直连）+ OrbStack `Include` |
| AI Agent | pi coding agent | `dot_pi/` 管理 agent、Goal 与工作流三个配置；本仓库不提供操作系统级沙箱，详见 [dev-tools.md](docs/dev-tools.md) |

## 🚀 快速开始

### 前置要求

- macOS（Apple Silicon 优先；Intel 路径在 zsh/fzf 模块中有兼容分支）
- [Homebrew](https://brew.sh/)
- chezmoi ≥ 2.x：`brew install chezmoi`
- 字体：[JetBrainsMono Nerd Font Mono](https://www.nerdfonts.com/)：
  `brew install --cask font-jetbrains-mono-nerd-font`

完整依赖清单见 [docs/getting-started.md](docs/getting-started.md)。

### 新机器安装

先把本仓库推送到你自己的 Git 远程，然后：

```bash
chezmoi init --apply <user>/<repo>   # 克隆源目录并立即应用
exec zsh                             # 重启 shell
```

首次启动 Zsh 会自动下载 [zimfw](https://github.com/zimfw/zimfw) 并初始化模块；
首次打开 Neovim 会自动 bootstrap lazy.nvim 并安装全部插件（需要网络）。

### 本机重新应用

源目录已就位时：

```bash
chezmoi diff     # 先预览将要发生的变更
chezmoi apply    # 确认无误后应用
```

日常修改配置请走「编辑源 → diff → apply → commit」流程，
详见 [docs/maintenance.md](docs/maintenance.md)。

## 📁 仓库结构与目标映射

chezmoi 命名约定：`dot_` → 隐藏目录/文件（`.` 开头），`private_` → 权限收紧（目录 `0700` / 文件 `0600`），
`symlink_` → 符号链接（文件内容即链接目标）。完整逐文件映射见
[docs/layout.md](docs/layout.md)。

```text
~/.local/share/chezmoi                    应用到 $HOME
├── .chezmoiignore                     →  (不部署) 过滤根级与嵌套 README.md / LICENSE、docs/ 与 *.local / *.bak / *token* 等，避免污染家目录
├── .gitignore                         →  (git 侧) 忽略 .vscode / .git / node_modules / **/.DS_Store / *.log 等
├── symlink_dot_zshrc.tmpl             →  ~/.zshrc  (→ ~/.config/zsh/.zshrc)  模板符号链接，内容为 {{ .chezmoi.homeDir }}/.config/zsh/.zshrc
├── symlink_dot_zimrc.tmpl             →  ~/.zimrc  (→ ~/.config/zsh/.zimrc)  同上（XDG 收敛，兼容 ~/.zshrc 路径）
├── dot_gitconfig                      →  ~/.gitconfig                 用户信息 / 代理 / LFS / push 行为
├── dot_gitignore_global               →  ~/.gitignore_global          全局忽略规则（构建产物根锚定，无 bin/）
├── dot_tmux.conf                      →  ~/.tmux.conf                  tmux 配置（Fish 登录 shell、tpm 插件、Catppuccin Mocha 状态栏）
├── dot_codex/
│   └── private_config.toml            →  (不部署) ~/.codex/config.toml   cc-switch 机器本地配置参考快照（被 .chezmoiignore 的 .codex/config.toml 排除；~/.claude/settings.json 同此模式：源已移出仓库，各机本地维护）
├── private_dot_config/
│   ├── zsh/                           →  ~/.config/zsh/               ★ 三模块 zsh 配置 + 入口文件（含独立 README，不部署）
│   │   ├── dot_zshrc                  →  ~/.config/zsh/.zshrc         Zsh 入口：Zim 引导 + 工具 eval + 模块加载（symlink 目标，真实文件）
│   │   ├── dot_zimrc                  →  ~/.config/zsh/.zimrc         Zim 模块清单（仅供 zimfw 读取，symlink 目标）
│   │   ├── aliases.zsh                →  ~/.config/zsh/aliases.zsh
│   │   ├── fzf.zsh                    →  ~/.config/zsh/fzf.zsh
│   │   ├── sdk.zsh                    →  ~/.config/zsh/sdk.zsh
│   │   ├── dot_gitignore              →  ~/.config/zsh/.gitignore
│   │   └── README.md                  →  (不部署) 模块文档，由 **/README.md 排除
│   ├── ghostty/config                 →  ~/.config/ghostty/config     Ghostty 终端（command = fish -l）
│   ├── alacritty/private_alacritty.toml → ~/.config/alacritty/alacritty.toml Alacritty 备用（文件 0600）
│   ├── kitty/kitty.local.conf         →  (不部署) 仅入库作参考（.chezmoiignore 的 **/*.local.* 排除）；目标机 ~/.config/kitty/kitty.local.conf 机器本地维护，由本机 kitty.conf 末尾 include 引入（仓库不含 kitty.conf）
│   ├── mise/config.toml               →  ~/.config/mise/config.toml   mise 工具链
│   ├── nvim/                          →  ~/.config/nvim/              LazyVim 配置（含 stylua.toml；lazy-lock.json 已停止跟踪、不入库）
│   └── private_fish/                  →  ~/.config/fish/              Fish 辅助配置（Starship + Fisher 13 插件清单）
│       ├── config.fish                →  ~/.config/fish/config.fish
│       ├── fish_plugins                →  ~/.config/fish/fish_plugins     Fisher 13 插件清单
│       ├── private_completions/       →  ~/.config/fish/completions/  symlink_docker/kubectl/orbctl.fish → OrbStack
│       ├── private_conf.d/            →  conf.d/ 五文件（00_env / 00_aliases / 01_dev / 01_rev / 02_mise，02_mise 守卫激活 mise）
│       ├── private_functions/         →  functions/ 仅 .keep 占位（fisher 插件安装于 ~/.config/fish/fisher = fisher_path，退出 chezmoi 管理域；config.fish 注入其 functions/completions/conf.d，仓库 private_functions/private_completions 仅保留自定义 symlink 补全）
│       └── themes/                    →  ~/.config/fish/themes/       空占位目录（仅 .keep）
├── private_dot_ssh/
│   └── private_config                 →  ~/.ssh/config                ★ GitHub 走 ssh.github.com:443 + 自适应 SOCKS5 ProxyCommand（含 OrbStack Include；~/.ssh 目录 0700）
└── dot_pi/
    ├── agent/                        →  ~/.pi/agent/                 默认目录属性（无 private_ 前缀）
    │   ├── settings.json              →  ~/.pi/agent/settings.json     扩展/默认 provider/tools/model
    │   └── pi-goal.json               →  ~/.pi/agent/pi-goal.json      Goal 设置
    └── workflows/
        └── settings.json              →  ~/.pi/workflows/settings.json 工作流设置（并发/进度面板）
```

> 仓库文档、`docs/` 与许可文件由 `.chezmoiignore` 排除，不部署。模式按**目标名**匹配；Git 提交排除另由 `.gitignore` 负责。目标数量随配置与 chezmoi 版本变化（含目录与脚本条目），请执行 `chezmoi managed`，不要依赖历史硬编码数量。

## 📚 文档索引

| 文档 | 内容 |
| --- | --- |
| [docs/getting-started.md](docs/getting-started.md) | 安装步骤、必需/推荐/可选依赖、应用后验证清单 |
| [docs/layout.md](docs/layout.md) | 全部源文件 → 目标路径映射、chezmoi 命名约定详解 |
| [docs/shell.md](docs/shell.md) | Zsh 启动链路、Zim 模块、Starship 提示符、Fish 的角色 |
| [docs/terminals.md](docs/terminals.md) | Ghostty 与 Alacritty 配置详解与键位表 |
| [docs/neovim.md](docs/neovim.md) | LazyVim 结构、extras、键位、插件管理与升级 |
| [docs/dev-tools.md](docs/dev-tools.md) | git / gh / mise / codex / pi agent 配置说明 |
| [docs/maintenance.md](docs/maintenance.md) | 日常维护流程、常用命令、验收清单、常见问题 |
| [docs/validation/README.md](docs/validation/README.md) | 离线语法/部署边界/隔离回归检查 |
| [docs/optimization.md](docs/optimization.md) | UltraCode 审查结论、优化证据与保留事项 |
| [private_dot_config/zsh/README.md](private_dot_config/zsh/README.md) | zsh 三模块内部契约（加载顺序、依赖、函数速查） |
| [private_dot_config/nvim/README.md](private_dot_config/nvim/README.md) | Neovim/LazyVim 使用说明 |

> 新增配置请同步更新 [docs/layout.md](docs/layout.md)；新文档请更新此索引。

## 🔒 安全与隐私

- `private_` 前缀收紧对应一级权限：目录 `0700`（如 `~/.ssh/`、`~/.config/fish/`），文件 `0600`（如 `~/.ssh/config`）。`dot_pi/` 无此前缀，不应假定部署后的 `.pi` 目录为 `0700`。
- `~/.config/gh/` 下的 `config.yml` 与 `hosts.yml` 均由 `gh auth login`
  在目标机器上生成，含凭据，不入仓库。
- Pi 通常以启动账户的权限运行；本仓库不含 `sandbox.json`、`landstrip.json` 或工具权限矩阵，不能保证拒绝敏感路径或高危命令。需要隔离时请单独配置容器/VM/OS 沙箱，见 [docs/dev-tools.md](docs/dev-tools.md)。
- `.gitignore` 对 Pi 源布局仅开放三个配置，其余运行时/凭据默认不入库；它不保护已跟踪或 `git add -f` 的文件，提交前仍需检查 diff。
- `dot_gitconfig` 与 `private_dot_ssh/private_config` 中包含本地代理地址（`socks5h://127.0.0.1:5376`，git 一处（gitconfig 单条代理行）与 SSH 探测均统一为 5376，仅对 `github.com`/`ssh.github.com` 生效）
  与个人身份信息，公开 fork 前请先脱敏。

## 🧾 环境

- 目标平台：macOS (Apple Silicon)，Homebrew 前缀 `/opt/homebrew`
- 本轮验证版本（2026-10）：chezmoi v2.73.0 · zsh 5.9 · Fish 4.9.3 · fzf 0.74.4 · tmux 3.7c · Neovim 0.12.5 · kitty 0.49.2（验证范围见 docs/optimization.md）
- 维护者：[azwpayne](https://github.com/azwpayne)

## License

Apache-2.0（根级 `LICENSE` 文件已删除，此处仅保留许可声明；分发前请自行补回完整许可文本）。
