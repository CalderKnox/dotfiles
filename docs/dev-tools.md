# 开发工具链：git / gh / mise / codex / pi agent


> 本文档只做解释性说明，**不耦合**任何代码或配置。凡是源文件已经承载的实际内容（字段值、列表项、权限矩阵等），一律以源文件为唯一权威；跨文档冲突时，一律以源文件为准。下文各节不再逐行抄录文件内容。

## Git — `dot_gitconfig` → `~/.gitconfig`

`dot_gitconfig` 会随 `chezmoi apply` 部署为 `~/.gitconfig`（chezmoi managed 实测包含 `.gitconfig`）。它统一设置编辑器（VS Code）、默认分支 `main`、LFS 四件套、push 行为与全局忽略文件 `~/.gitignore_global`（`~` 由 git 原生展开，无用户名硬编码）。所有实际字段以源文件 `dot_gitconfig` 为唯一权威。

> **代理说明**：当前 `dot_gitconfig` 仅保留一条按域名限定的代理行 `[http "https://github.com"]`（socks5h://127.0.0.1:5376；socks5h 与 socks5 的差别是 DNS 由代理端解析）；非标准键（如 `[https …]`）会被 git 静默忽略。SSH 侧代理由 `private_dot_ssh/private_config` 的自适应 `ProxyCommand` 负责，探测端口同为 `5376`；如需 `git pull` 一律变基，应使用标准键 `pull.rebase = true`（当前未启用）。早期版本 `.chezmoiignore` 中按源文件名书写的 `dot_gitconfig` / `**/dot_git` 行从不匹配任何目标、未生效，现已删除，本文件正常随 `apply` 部署。

全局忽略规则（`dot_gitignore_global` → `~/.gitignore_global`，完整清单以源文件为准）：编辑器临时文件与交换文件（`*~`、`.DS_Store`、`*.swp` 等）、IDE 目录（`.idea` / `*.iml` / `.vscode`）、构建产物（`*.aux` / `*.log*` 及根锚定的 `/dist/` / `/build/` / `/target/`；`bin/` 已移除以免误伤正常入库的同名目录）、Python 相关（`__pycache__/` / `*.venv` / `*.cache`）与 Node 依赖（`node_modules/`）。具体条目与分类以源文件 `dot_gitignore_global` 为准。

## GitHub CLI — `gh`

当前仓库未直接托管 `private_dot_config/gh/private_config.yml`（该目录不存在），`gh` 配置由目标机执行 `gh auth login` 后生成（`~/.config/gh/hosts.yml` / `config.yml`）：

- 协议 `git_protocol: https` 为默认值；`hosts.yml` 中通常按主机覆盖为 `ssh`。
- 常用别名：`gh co` = `pr checkout`（若在本地配置）。
- `pager` / `browser` 留空，跟随环境变量；`spinner` 动画开启。
- 配合 `private_dot_config/zsh/aliases.zsh` 中的 `gopen`（`gh browse`）在浏览器打开当前仓库。
- 网络可达性与 `dot_gitconfig` / `private_dot_ssh/private_config` 共用本机 `127.0.0.1:5376` SOCKS5 代理（见 [getting-started.md](getting-started.md)「弱网环境：bootstrap 前先设代理」），已统一为 `5376`，不再区分 `7890`。

## mise — `private_dot_config/mise/config.toml`

mise 工具链由 `private_dot_config/mise/config.toml` 声明（工具与版本见该文件，当前为若干工具的 `latest`），由 `private_dot_config/zsh/dot_zshrc` 中的 `eval "$(mise activate zsh)"` 接管 zsh 环境；实际声明以源文件为准。常用操作见 `mise` 文档与 `aliases.zsh` 的 `update-all` 复用。

### 包管理器更新：`aliases.zsh` 的 `auto-update` 与 `update-all`

`private_dot_config/zsh/aliases.zsh` 提供两个更新入口，实际更新逻辑已收敛为一处：

| 函数 | 位置 | 覆盖目标 | 核心机制 | 适用场景 |
| --- | --- | --- | --- | --- |
| `auto-update` | `aliases.zsh` | 与 `update-all` 相同 | 薄包装：打印横幅后委托 `update-all` 执行，详见源文件 | 兼容旧习惯的一键入口 |
| `update-all` | `aliases.zsh` | 多项（`brew`/`sdk`/`rustup`/`tldr`/`uv`/`mise` 等，详见源文件） | 关联数组声明任务，支持参数过滤、守卫、失败计数与彩色输出，详见 `aliases.zsh` | 需灵活选择目标、查看统计 |

要点：

- 旧版 `auto_update` 曾顺序守卫调用五个 `*_update` 辅助函数（`uv_update` / `sdk_update` / `rust_update` / `tldr_update` / `brew_update`），它们已在提交 `0af1f61` 中删除；现 `auto-update` 委托 `update-all`，二者覆盖目标完全一致（均含 `mise`）。
- `update-all` 的 `brew` 任务为激进的全量升级流程（含 `brew cu`），历史上的 `brew_update` 别名已删除，详见 `aliases.zsh` 中 `tasks` 定义。

> 验证：`zsh -n ~/.config/zsh/aliases.zsh` 可覆盖两函数语法；`zsh -ic 'type update-all auto-update'` 确认已加载。

## Codex — `dot_codex/private_config.toml`

`config.toml` **不随 `chezmoi apply` 部署**：已被 `.chezmoiignore` 的排除行 `.codex/config.toml` 排除（该配置含 provider、hooks/projects trust 等机器本地状态，由各机 cc-switch 注入维护，不入部署）。仓库内的 `dot_codex/private_config.toml` 仅作参考快照（`private_` 前缀对应 `0600` 权限语义），实际生效值以各机 `~/.codex/config.toml` 为准。

## pi coding agent — `private_dot_pi/private_agent/`

为 [pi](https://github.com/earendil-works/pi) 编码代理准备的受限运行环境（部署到 `~/.pi/agent/`）。四个文件各司其职：由于 chezmoi 目标名均无 `private_` 前缀，文件应用后为默认权限 `0644`，仅父目录因 `private_dot_pi/private_agent` 命名为 `0700`。以下各文件的实际字段、列表与策略条目，一律以对应源文件为唯一权威。

### settings.json — 主题与扩展包

`private_dot_pi/private_agent/settings.json` 配置 pi 的主题、扩展包、默认 provider / tools / model 与出站代理。它声明一组 npm 扩展包（含若干带 `extensions` 过滤的条目），并固定 `defaultProvider`、`defaultTools`、`defaultModel`、`defaultThinkingLevel` 与 `httpProxy`（与 git / SSH 同端口 5376）；实值以 `private_dot_pi/private_agent/settings.json` 为唯一权威。

### sandbox.json — 文件系统与网络沙箱

`private_dot_pi/private_agent/sandbox.json` 定义 agent 的文件系统与网络沙箱策略。沙箱总开关开启后，文件系统采用窄白名单读取（`allowRead`）与大范围 `denyRead` / `denyWrite` 拒绝读写；`shell.readAccess = "policy"` 使该读策略对 bash/shell 命令同样生效（denied 路径无法用 `cat` 等绕过；曾为 `host` 全豁免，已收紧），网络默认关闭（禁网）但允许本地端口绑定与全部 Unix socket，并仅对 github.com 系列域名开放白名单；Windows 容器模式在 macOS 上不生效。所有规则条目以 `private_dot_pi/private_agent/sandbox.json` 为唯一权威。

> 网络默认关闭（禁网策略）：沙箱内禁止出站网络，仅放行本地端口绑定与 Unix socket；`allowedDomains` 域名白名单仅在网络启用时作为出站限制生效（当前不生效），`deniedDomains` 为空。

### landstrip.json — 子代理与任务权限

`private_dot_pi/private_agent/landstrip.json` 控制子代理派生的任务级权限：任务级 `*`（`task` 执行类）默认 `ask`，即派生子代理前需用户确认；landstrip.json 未配置 `review` 条目，只读审查类子代理与执行类同样按 `task` 规则处理（不因「只读」豁免确认）。它与 `workflows/settings.json` 的 `progressPanelMaxAgents` 职责不同、相互独立：后者限制工作流进度面板的并发 / 展示代理数上限，前者指定沙箱复用。详见 [layout.md](layout.md) 与下节。

### workflows/settings.json — 动态工作流设置

位于 `private_dot_pi/workflows/settings.json`（部署到 `~/.pi/workflows/settings.json`）。它配置工作流运行时的并发、重试、进度面板与会话持久化等行为；实值以 `private_dot_pi/workflows/settings.json` 为唯一权威。`progressPanelMaxAgents` 用于 `pi-dynamic-workflows` 的进度面板，与 `landstrip.json` 的 `toolFilesystemPolicy` 相互独立。详见 [layout.md](layout.md)。

### extensions/pi-permission-system/config.json — 工具级权限矩阵

`private_dot_pi/private_agent/extensions/pi-permission-system/config.json` 定义工具级权限矩阵：默认全局 `allow`，对 `read` / `write` / `edit` / `path` 中的敏感路径（如 `*.env`、`~/.ssh/*`、`~/.aws/*`、`/etc/*`、`/var/*`）与高危 bash 命令（`sudo` / `mv` / `rm` / `dd` / `mkfs.*` 等）硬拒绝（`deny`）；`external_directory` 为需确认（`ask`，仅 `~/.cargo/registry`、`~/.npm`、`~/.cache` 白名单放行），`python3 *` / `node *` 显式保持放行（`allow`）；`yoloMode` 开启时所有 `ask` 自动批准、硬 `deny` 仍生效。其目标是让 agent 完成日常编码与受控编辑，同时杜绝误删、密钥外泄与敏感路径写入；完整矩阵与 `$schema` 指向 pi-permission-system 的 JSON Schema，实值以源文件 `private_dot_pi/private_agent/extensions/pi-permission-system/config.json` 为唯一权威。
