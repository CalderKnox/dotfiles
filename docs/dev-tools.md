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

mise 工具链由 `private_dot_config/mise/config.toml` 声明（当前各工具使用 `latest` 浮动选择器，非钉版；以源文件为准），由 `private_dot_config/zsh/dot_zshrc` 中的 `eval "$(mise activate zsh)"` 接管 zsh 环境（fish 侧由 `conf.d/01_activate.fish` 守卫激活）；实际声明以源文件为准。常用操作见 `mise` 文档与 `aliases.zsh` 的 `update-all` 复用。

### 包管理器更新：`aliases.zsh` 的 `auto-update` 与 `update-all`

`private_dot_config/zsh/aliases.zsh` 提供两个更新入口，实际更新逻辑已收敛为一处：

| 函数 | 位置 | 覆盖目标 | 核心机制 | 适用场景 |
| --- | --- | --- | --- | --- |
| `auto-update` | `aliases.zsh` | 与 `update-all` 相同 | 薄包装：打印横幅后委托 `update-all` 执行，详见源文件 | 兼容旧习惯的一键入口 |
| `update-all` | `aliases.zsh` | 多项（`brew`/`sdk`/`rustup`/`tldr`/`uv`/`mise`/`pi` 等，详见源文件） | 关联数组声明任务，支持参数过滤、守卫、失败计数与彩色输出，详见 `aliases.zsh` | 需灵活选择目标、查看统计 |

要点：

- 旧版 `auto_update` 曾顺序守卫调用五个 `*_update` 辅助函数（`uv_update` / `sdk_update` / `rust_update` / `tldr_update` / `brew_update`），它们已在提交 `0af1f61` 中删除；现 `auto-update` 委托 `update-all`，二者覆盖目标完全一致（均含 `mise`）。
- `update-all` 的 `brew` 任务为激进的全量升级流程（含 `brew cu`），历史上的 `brew_update` 别名已删除，详见 `aliases.zsh` 中 `tasks` 定义。

> 验证：`zsh -n ~/.config/zsh/aliases.zsh` 可覆盖两函数语法；`zsh -ic 'type update-all auto-update'` 确认已加载。

## Codex — `dot_codex/private_config.toml`

`config.toml` **不随 `chezmoi apply` 部署**：已被 `.chezmoiignore` 的排除行 `.codex/config.toml` 排除（该配置含 provider、hooks/projects trust 等机器本地状态，由各机 cc-switch 注入维护，不入部署）。仓库内的 `dot_codex/private_config.toml` 仅作参考快照（`private_` 前缀对应 `0600` 权限语义），实际生效值以各机 `~/.codex/config.toml` 为准。

## pi coding agent — `dot_pi/`

本仓库仅部署三个 [pi](https://github.com/earendil-works/pi) 配置，值与扩展清单以对应源文件为准：

| 源文件 | 目标 | 用途 |
| --- | --- | --- |
| `dot_pi/agent/settings.json` | `~/.pi/agent/settings.json` | 扩展包、默认 provider/tools/model、思考等级等 |
| `dot_pi/agent/pi-goal.json` | `~/.pi/agent/pi-goal.json` | Goal 扩展设置 |
| `dot_pi/workflows/settings.json` | `~/.pi/workflows/settings.json` | `ultracode` 触发词、工作流并发/重试/预算/进度面板等 |

`dot_pi`、`agent`、`workflows` 均无 `private_` 前缀：默认目标目录属性为 `0755`，配置文件为 `0644`；不代表当前机器上的实际权限。`.chezmoiignore` 按目标名只开放上述三文件，`.gitignore` 按源名镜像该 allowlist，其余 Pi 运行时、会话与凭据默认排除。Git 忽略规则不保护已跟踪文件或强制添加；部署忽略规则不能阻止提交。

### 安全边界

本仓库**没有** `sandbox.json`、`landstrip.json` 或 `pi-permission-system` 权限矩阵。扩展声明、项目 trust、代理地址与工作流预算都不构成 OS 安全边界；不能据此承诺拒绝读取 `.env`/SSH 凭据或禁止 `sudo`/`rm`。

Pi、扩展和子进程通常拥有启动账户的权限。需要强隔离时，应另外部署容器、VM 或操作系统沙箱，并限制挂载、凭据和网络。请参阅上游 [security.md](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/security.md) 与 [containerization.md](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/containerization.md)。本次修正只更新说明与 Git 排除，不改 provider/model、扩展策略或目录权限。
