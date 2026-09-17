# 安装与快速开始

本文档说明如何在一台新的 macOS（Apple Silicon）机器上，用本仓库还原完整的开发环境。

## 1. 安装 Homebrew 与前置依赖（全部在 `chezmoi apply` 之前）

```bash
# Homebrew（若未安装，Apple Silicon 默认前缀 /opt/homebrew）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
eval "$(/opt/homebrew/bin/brew shellenv)"

# —— chezmoi 本体与字体 ——
brew install chezmoi
brew install --cask font-jetbrains-mono-nerd-font   # Ghostty / Alacritty / Neovim 均依赖该字体

# —— git-lfs（必装）：本仓库 dot_gitconfig 配置了 [filter "lfs"] 且 required = true，
#    部署后对全机所有仓库生效——未装 git-lfs 时任何 clone/push 都会因 LFS filter
#    缺失而直接报错失败，必须在首次 git 操作前装好并初始化
brew install git-lfs && git lfs install

# —— 启动必需工具（首次启动 zsh 即被使用，建议随本节一并装；完整清单与说明见 §4）——
#    fzf-tab 无需手动安装：由 zimfw 首次启动时按 private_dot_config/zsh/dot_zimrc 自动拉取
brew install fzf starship zoxide mise fd ripgrep
```

> **为什么要在 `apply` 之前**：`apply` 后一般会立即 `exec zsh` 首次启动（Zim 拉模块、
> 各工具初始化、补全加载），上述前置若缺装会导致功能明显退化甚至 git 全局断链。
> 守卫化说明：`~/.config/zsh/.zshrc`（经 symlink 兼容 `~/.zshrc`）中 `zoxide` / `mise` / `starship` 的 `eval` 均带
> `command -v` 守卫，rustup/cargo 的 PATH 注入为目录存在性 + 去重双守卫（静态路径，
> 不再调用 `brew --prefix` 子进程），fzf 初始化统一收敛到 `fzf.zsh`（带守卫），
> 缺装时全部**静默跳过、不再报 `command not found`**——因此其余体验增强类工具
> （`bat` / `lsd` / `kubectl` / SDKMAN 等，见 §4）完全可以 `apply` 之后按需补装，
> 静默退化不报错。

## 2. 应用配置

### 弱网环境：bootstrap 前先设代理（可选但推荐）

本仓库引导链共有三次直连 GitHub 的网络动作：`chezmoi init` 拉取本仓库（方式 A）、
首次启动 `zsh` 时 `zimfw` 下载全部 Zim 模块、首次运行 `nvim` 时 `lazy.nvim` 安装 43 个
插件。弱网/受限网络环境建议在执行下面任何 bootstrap 步骤**之前**先临时设置代理：

```bash
# 示例：本机代理监听 5376（与 dot_gitconfig / ~/.ssh/config 中的代理端口一致）
export https_proxy=http://127.0.0.1:5376
export http_proxy=http://127.0.0.1:5376
export all_proxy=socks5h://127.0.0.1:5376

# 探活：确认代理端口确实在监听，再继续后面的 bootstrap
nc -z 127.0.0.1 5376 && echo "proxy ok" || echo "proxy not listening on 5376"
```

- 代理不在监听时先解决代理本身，或改走直连/镜像；探活通过后再执行 `chezmoi init`、
  首次启动 `zsh`、首次运行 `nvim`。
- 两通道行为不对称：`dot_gitconfig` 中仅一处按域名限定的 GitHub 代理（`[http "https://github.com"]`，对该 URL 匹配的 HTTP/HTTPS 远程均生效；冗余的 `[https …]` / `[ssh …]` 段已删）固定为
  `socks5h://127.0.0.1:5376` 且**无直连回退**——代理离线时对 GitHub 的 git 操作会卡住或报
  `Connection refused`；`~/.ssh/config` 的 `ProxyCommand` 则先探测 `127.0.0.1:5376`，
  在线走 SOCKS5、离线自动回退直连。
- 首次启动 `zsh` 时 `zimfw` 拉模块走 HTTPS（新机默认无 `~/.gitconfig` 即不受 git 代理
  影响），此时 shell 侧导出的 `https_proxy` 即为其提供代理通道。

### 初始化与执行

```bash
# 方式 A：从远程仓库初始化并立即应用（新机器首选）
chezmoi init --apply <user>/<repo>

# 方式 B：源目录已在本机（~/.local/share/chezmoi）时
chezmoi diff     # 先预览
chezmoi apply

exec zsh   # 重启 shell 使全部配置生效（或重新打开终端）
```

### .chezmoiignore 的影响
新机器执行 `chezmoi apply` 时，根目录的 `.chezmoiignore` 会自动**跳过**以下内容不渲染到 `$HOME`（见 [layout.md](layout.md)）：

- 根级与全部嵌套的 `README.md` / `LICENSE`（模式 `**/README.md` / `**/LICENSE`，含 `zsh/README.md`、`nvim/README.md`、`nvim/LICENSE`）—— 仓库文档仅留在源目录，不污染目标机
- `docs/` —— 本文档所在目录整体不部署
- `*.local` / `*.local.*` / `*.bak` / `**/.DS_Store` / `node_modules/` / `.pnpm-store/` 等本地覆盖与构建产物
- `*token*` / `*secret*` / `*credential*` 等敏感文件名匹配

> 注意：`dot_gitconfig` **不在**忽略之列——`apply` 会正常生成 `~/.gitconfig`（历史上的
> 源名失配行 `dot_gitconfig` / `**/dot_git` 与 `**/REAMDME.md` 拼写错误均已修复，
> `managed` 目标数 59→55）。详见 [layout.md](layout.md)。

因此 `chezmoi diff` 中不会出现 `docs/` 的新增，`chezmoi doctor` 亦不会告警缺失——属预期行为。
如需排查可执行 `chezmoi ignored` / `chezmoi status` 查看被忽略列表。

## 3. 首次启动会发生什么

| 组件 | 行为 | 触发时机 |
| --- | --- | --- |
| `fish` / `pi` | `private_dot_config/private_fish/config.fish`（interactive 时初始化 Starship，插件由 `fish_plugins` 清单管理）、`private_dot_pi/**`（pi agent 配置）直接生效，均随 `apply` 写入 `$HOME`；本文档只覆盖 `zsh` 栈，其余见 [layout.md](layout.md) | 首次启动 `fish` / `pi` 时 |
| Zim 框架 | `~/.config/zsh/.zshrc` 检测 `~/.zim/zimfw.zsh` 缺失时自动下载并 `zimfw init` 安装 `dot_zimrc` 中声明的全部模块（详见 `private_dot_config/zsh/dot_zimrc`） | 首次启动 `zsh` |
| `PATH` / `brew` | 按 `dot_zshrc` 中守卫逻辑注入 Homebrew 与本地路径（前置 `~/bin` 等，cargo/rustup 按目录存在性守卫，详见 `private_dot_config/zsh/dot_zshrc`） | 每次启动 `zsh` |
| `zoxide` / `mise` / `starship` / `fzf` | 按 `command -v` 守卫 `eval` 初始化，未安装静默跳过；`fzf` 键位绑定唯一收敛于 `fzf.zsh`（详见 `dot_zshrc` 与 `fzf.zsh`） | 每次启动 `zsh` |
| `zsh` 三模块 | 按序 `source ~/.config/zsh/aliases.zsh` → `fzf.zsh`（含 `fzf` 前缀探测与 `~/.fzf_prefix_cache` 缓存）→ `sdk.zsh`（`pnpm` / `SDKMAN` **惰性加载** / `Go` / `Rust` / `Docker` / `kubectl`，补全走 `~/.cache/zsh/` 缓存 + `zcompile`，均有守卫） | 每次启动 `zsh` |
| Neovim | 首次运行 `nvim` 时 `lazy.nvim` 自动 `bootstrap` 并按 `lazy-lock.json` 安装 43 个插件（需网络） | 首次运行 `nvim` |
| `mise` 工具链 | `mise activate` 已挂接；按需执行 `mise install` 安装 `private_dot_config/mise/config.toml` 声明的工具（详见该文件） | 手动执行 |

> `~/.config/zsh/.zshrc` 以 glob（`for file in ~/.config/zsh/*.zsh(N)`）加载三模块，没有逐文件 source 行；
> 如需禁用 `sdk.zsh`，重命名/移除已部署文件（如 `mv ~/.config/zsh/sdk.zsh ~/.config/zsh/sdk.zsh.disabled`）
> 或改 `dot_zshrc` 中的 glob 行。`SDKMAN` 为惰性加载——首次调用 `sdk` 时才真正 source init 并注入 PATH（Java 等
> candidate 的可用性随之延迟到首次 `sdk` 调用）；`fzf` 键位绑定只在 `fzf.zsh` 内
> `eval "$(fzf --zsh)"` 一次，`~/.zshrc` 不再重复。详见 [shell.md](shell.md)。

## 4. 依赖清单

### 启动必需（缺失会导致功能明显退化或报错；已随 §1 安装，此处为清单备查）

| 工具 | 用途 | 安装 |
| --- | --- | --- |
| `git-lfs` | Git LFS filter——`dot_gitconfig` 配置 `[filter "lfs"] required = true`，缺失时**全机所有仓库**的 clone/push 直接失败（硬性中断，非静默退化） | `brew install git-lfs && git lfs install` |
| `fzf` | `Ctrl-R` / `Ctrl-T` / `Alt-C` 及所有 `f*` 函数（`frg` / `fkill` / `ftm` / `fl*`） | `brew install fzf` |
| `fzf-tab` | 补全菜单模糊化（Zim 模块 `Aloxaf/fzf-tab`） | 无需手动安装，由 `zimfw` 按 `private_dot_config/zsh/dot_zimrc` 的 `zmodule Aloxaf/fzf-tab` 首次启动时自动安装并加载 |
| `starship` | 提示符（配置为机器本地 `~/.config/starship.toml` Catppuccin Mocha，未随仓库分发，跨机需自行拷贝） | `brew install starship` |
| `zoxide` | `z` 目录跳转 | `brew install zoxide` |
| `mise` | 运行时管理（`bun` / `deno` / `go` / `node` / `pnpm`） | `brew install mise` |
| `fd` | `fzf` 默认文件列表命令 | `brew install fd` |
| `ripgrep` (`rg`) | `frg` 内容搜索、`fd` 缺失时的回退 | `brew install ripgrep` |

> `fd` 未安装时 `fzf.zsh` 自动回退到 `rg --files`；`fzf` 本身缺失时按键绑定与 `f*` 函数均不可用，但不阻断 shell 启动（有 `command -v` 守卫）。

### 体验增强（别名 / 函数指向的目标，未安装时对应别名退化）

```bash
brew install bat lsd htop fastfetch neovim tmux yazi gh lazygit tldr coreutils \
             kubecolor uv rustup
```

- `coreutils` 提供 `nproc`（`makes` / `xargsp` 半核并行依赖它）
- Fish 侧：`brew install fish fisher`——`~/.config/fish/` 的 13 个插件由 `fish_plugins` 清单管理（`fisher update` 安装/更新）；提示符复用 `starship`、fzf 键位复用 `fzf.fish`（均已在上方依赖中）
- `bat` / `lsd` / `htop` 分别接管 `cat` / `ls` / `top`；脚本中需要原生行为时用 `command cat` 等
- `gh` 配合 `~/.ssh/config` 的 `Host github.com → ssh.github.com:443` 与 `dot_gitconfig` 的 `socks5h://127.0.0.1:5376` 代理共同保证 GitHub 可达。代理已统一为 `5376`，不再区分 `7890`（详见 [dev-tools.md](dev-tools.md) 中的代理配置说明）。

按需补装（别名 / 函数指向的目标，未装时对应功能退化）：

```bash
# Python lint：ruff_auto 函数的目标
brew install ruff
# Android 逆向：jdx / scr 别名的目标（jadx-gui / scrcpy）
brew install jadx scrcpy
```

另需注意：VS Code 及其 `code` CLI 是 `git config editor = code` 以及 `clp_cfg` / `cla_cfg` 别名的目标（`fzf` 的 `Ctrl-E` 绑定已注释停用，现为 `Ctrl-G` 走 `$EDITOR`），未安装时上述功能退化。

### 有守卫的可选组件（未安装时静默跳过）

SDKMAN（Java）、Android NDK（`/opt/homebrew/share/android-ndk`）、Docker、`kubectl`（`k` → `kubectl` 别名；已装 `kubecolor` 时由 `kubectl()` 函数透明包装彩色输出）、`pnpm`、`~/.cargo/env`、`onproxy` 函数。

### 终端模拟器（二选一即可，建议都装）

```bash
brew install --cask ghostty alacritty
```

两者均在 `font-jetbrains-mono-nerd-font` 就绪后开箱可用；Ghostty 为主力，Alacritty 为备用。详见 [terminals.md](terminals.md)。

## 5. 应用后验证清单

逐项确认还原成功：

```bash
# chezmoi 本身（先看）
chezmoi doctor                       # 各项检查通过；.chezmoiignore 导致 docs/README 等不计入 diff 属正常
chezmoi diff                         # 应用后应为空（或仅剩有意保留的本地差异）
chezmoi ignored                      # 确认 docs/、README.md 等在忽略列表

# shell 栈
for f in ~/.config/zsh/.zshrc ~/.config/zsh/*.zsh ~/.config/zsh/.zimrc; do zsh -n "$f" || exit 1; done # 语法检查无报错；逐文件（zsh -n 多文件传参时只查首个，实测）
zsh -ic 'exit'                       # 干净启动无报错
zsh -ic 'type k; echo $EDITOR'       # k -> kubectl（kubecolor 包装）；EDITOR=nvim
                                     # 〔未装 kubectl 则跳过：type k 报 not found 属预期〕
starship prompt                      # 渲染 powerline 提示符无报错〔未装 starship 则跳过本项〕

# fzf（含前缀缓存）〔未装 fzf 则本组全部跳过〕
zsh -ic 'echo $FZF_DEFAULT_COMMAND'  # 以 fd 开头〔装了 fzf 但未装 fd 则以 rg 开头〕
cat ~/.fzf_prefix_cache              # 应为 /opt/homebrew/opt/fzf（Apple Silicon）〔未装 fzf 时无此文件，跳过〕
zsh -ic 'type frg fkill ftm'         # fzf 交互函数已加载

# mise〔未装 mise 则跳过本组〕
mise ls                              # 列出 bun/deno/go/node/pnpm（未 install 时提示安装）
mise doctor                          # 可选：检查 mise 健康度

# 编辑器〔首次运行会触发 lazy.nvim 安装需联网，见 §2 代理段〕
nvim --headless +qa                  # 无插件加载错误

# SSH / GitHub 可达性
cat ~/.ssh/config                    # 顶部含 Include ~/.orbstack/ssh/config，github.com 走 ssh.github.com:443
git lfs version                      # 确认 git-lfs 已装（缺失时 clone/push 会因 filter lfs required=true 全局失败）
git config --get-regexp proxy        # 应为 socks5h://127.0.0.1:5376（与 SSH ProxyCommand 5376 统一；
                                     # apply 已部署 ~/.gitconfig，可直接读取）
                                     # 也可直接校验源文件：
                                     # git config --file ~/.local/share/chezmoi/dot_gitconfig --get-regexp proxy
```

> **日常更新速览**：`private_dot_config/zsh/aliases.zsh` 提供 `auto-update`（若定义了 `onproxy` 函数则先切代理，随后直接委托 `update-all` 执行，覆盖目标一致）与更细粒度的 `update-all [brew|mise|rustup|tldr|uv|sdk]`（关联数组 6 项，支持参数过滤、失败计数与耗时统计，**含 `mise`**；**失败即红**——失败目标打印红色 `✗` 与错误摘要、结尾汇总 `N/M 目标失败` 并返回非零，成功目标保持绿色 `✓`）；验证通过后可按需执行 `zsh -ic 'auto-update'` 或 `zsh -ic 'update-all'`，详见 [maintenance.md](maintenance.md) 与 [dev-tools.md](dev-tools.md) 的对比表及 `aliases.zsh` 源码。

全部通过后即可进入日常使用；更多维护流程见 [maintenance.md](maintenance.md)，完整映射见 [layout.md](layout.md)。
