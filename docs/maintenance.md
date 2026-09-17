# 维护指南

## 日常修改流程

本仓库是 chezmoi 的源目录——**永远编辑源文件，不要直接改 `$HOME` 下的目标文件**（否则下次 `apply` 会被覆盖，产生漂移）。

```bash
# 1. 编辑源文件（chezmoi edit 会直接打开源目录中的对应文件）
chezmoi edit ~/.config/zsh/.zshrc  # XDG 真实入口（源 private_dot_config/zsh/dot_zshrc）
chezmoi edit ~/.zshrc          # 注意：~/.zshrc 解析到的是一行符号链接模板 symlink_dot_zshrc.tmpl
                                # （改 zshrc 内容请用上面一行，chezmoi source-path 实测）
# 或直接：
$EDITOR ~/.local/share/chezmoi/private_dot_config/zsh/dot_zshrc
# 其他示例：
chezmoi edit ~/.config/nvim/lua/config/options.lua

# 2. 预览将要发生的变更（apply 前必看）
chezmoi diff

# 3. 应用到 $HOME
chezmoi apply

# 4. 验证（见下方验收清单），通过后提交
git -C ~/.local/share/chezmoi add -A && git -C ~/.local/share/chezmoi commit -m "..."
```

> 小贴士：`chezmoi edit` 等价于用 `$EDITOR` 打开 `~/.local/share/chezmoi/` 下的对应 `dot_` / `private_` 源文件；
> 直接编辑源文件亦可，效果相同。详见 [layout.md](layout.md) 的命名约定。

## 常用命令

| 命令 | 用途 |
| --- | --- |
| `chezmoi managed` | 列出所有被管理的目标文件 |
| `chezmoi diff` | 源与目标的差异预览（`apply` 前必看） |
| `chezmoi apply --dry-run` | 试运行，不实际写入 |
| `chezmoi add <file>` | 把已有文件纳入管理（自动加 `dot_` / `private_` 前缀） |
| `chezmoi add --encrypt` / `--template` | 需要时再启用加密/模板 |
| `chezmoi forget <file>` | 停止管理（源文件一并删除） |
| `chezmoi doctor` | 环境体检 |
| `chezmoi status` | 简要漂移概览（等价 `git status` 视角） |
| `chezmoi ignored` | 查看被 `.chezmoiignore` 排除的文件 |
| `zimfw update` | 更新 Zim 插件（`zsh`，改动 `private_dot_config/zsh/dot_zimrc` 后按需执行） |
| `zimfw upgrade` | 升级 `zimfw` 自身（`zsh`） |
| `zimfw init` | 重建 `${ZIM_HOME}/init.zsh`（改动 `~/.config/zsh/.zimrc` 后需要，`dot_zshrc` 会按 `-nt` 时间戳自动重建） |
| `zimfw info` | 查看 `zimfw` 版本与模块信息 |
| `auto-update` | 一键全量更新入口：若定义了 `onproxy` 函数则先切代理，随后直接委托 `update-all` 执行（覆盖目标一致）；定义于 `private_dot_config/zsh/aliases.zsh`，详见 [dev-tools.md](dev-tools.md) |
| `update-all [targets...]` | 关联数组驱动的批量更新，支持参数选择目标（如 `update-all brew mise`）、带失败计数与耗时统计；覆盖 `brew` / `sdk` / `rustup` / `tldr` / `uv` / `mise` 共 6 项（**已覆盖 `mise`**，与 `auto-update` 的核心差异）；定义于 `aliases.zsh`，详见 [dev-tools.md](dev-tools.md) |

> `auto-update` 与 `update-all` 均定义于 `private_dot_config/zsh/aliases.zsh`；`auto-update` 为兼容旧习惯的一键入口（内部委托 `update-all`），`update-all` 为支持参数过滤、失败计数与耗时统计的实际实现，二者覆盖目标一致（均含 `mise`）；详见 [dev-tools.md](dev-tools.md) 对比表。

## 验收清单

改动不同组件后至少跑过对应检查（覆盖 `zsh` / `zim` / `starship` / `ghostty` / `alacritty` / `nvim` / `fish` / `mise` / `git` / `chezmoi`）：

```bash
# zsh 模块（语法 + 干净启动 + 关键定义）
for f in ~/.config/zsh/{aliases,fzf,sdk}.zsh ~/.config/zsh/.zshrc ~/.config/zsh/.zimrc; do zsh -n "$f" || exit 1; done
# 逐文件校验（实测 zsh -n 多文件传参时只查首个）；覆盖 aliases.zsh 中的 auto-update / update-all（含关联数组、耗时统计）语法
zsh -ic 'exit'                              # 干净启动无报错
zsh -ic 'type ls df du; echo $EDITOR'       # 关键别名/变量（EDITOR=nvim）
zsh -ic 'type auto-update update-all'       # 验证更新函数已加载（update-all 支持参数过滤、失败计数与耗时统计）
# 注意：短别名 k 定义在 sdk.zsh 且仅当 kubectl 可用时才存在，无 kubectl 的机器上属预期缺失

# Zim 插件管理器（改动 ~/.config/zsh/.zimrc 后；重启 shell 时 dot_zshrc 会按 -nt 时间戳自动重建 init.zsh）
zsh -ic 'zimfw info'                        # 查看 zimfw 版本
zsh -ic 'zimfw update'                      # 更新插件
zsh -ic 'zimfw init'                        # 手动重建 init.zsh

# starship 渲染
starship prompt
starship explain  # 可选：查看各模块判定

# ghostty 配置解析（会打印生效值；ghostty CLI 需先在 Ghostty 菜单 →
# "Install CLI tool" 安装，否则用全路径 /Applications/Ghostty.app/Contents/MacOS/ghostty）
ghostty +show-config
# 或：ghostty +show-config | head -n 50

# neovim 无报错启动
nvim --headless +qa
nvim --headless -c "lua require('config.lazy')" -c "qa"  # 可选：校验 lazy spec

# git 配置合法（未知键不会报错，但可确认解析；proxy 与 SSH 统一为 5376）
git config --list --show-origin | head
git config --get core.editor
git config --get safe.directory
git config --get-regexp proxy               # 应为 socks5h://127.0.0.1:5376（与 SSH ProxyCommand 5376 统一）
# 或校验源文件：
git config --file ~/.local/share/chezmoi/dot_gitconfig --get-regexp proxy

# fish 配置语法检查（fish -n 只校验首个文件，必须逐个检查；实测多文件传参时后续文件被静默跳过）
for f in ~/.config/fish/config.fish ~/.config/fish/conf.d/*.fish; fish -n $f; or exit 1; end
# conf.d 现含四文件：00_env / 00_aliases / 01_dev / 01_rev（fish 侧 fzf 键位由 fisher 插件 patrickf1/fzf.fish 运行时生成 conf.d/fzf.fish，不入库）

# mise 环境体检
mise doctor
mise ls                                     # 应列出 bun/deno/go/node/pnpm（均为 latest）

# alacritty：CLI 无 --print-config 子命令（0.17 实测报错），配置解析在启动时进行，
# 冒烟启动（瞬间退出）即可验证配置可解析
alacritty --version
alacritty -e true

# chezmoi 全局状态
chezmoi doctor && chezmoi diff
```

提交约定：小步提交、说明动机；涉及行为变化的改动在 `commit body` 里写明验证命令与结果。
更多工具链细节见 [dev-tools.md](dev-tools.md)，完整映射见 [layout.md](layout.md)。

## 常见问题（FAQ）

### fzf 找不到 / 快捷键失效

`fzf` 安装前缀缓存放在 `$ZDOTDIR/.fzf_prefix_cache`（未设置 `ZDOTDIR` 时即 `~/.fzf_prefix_cache`）。升级/卸载/换机器后若失效，模块会自愈删除并重新探测；
也可手动删除该缓存文件强制重建：

```bash
rm -f ~/.fzf_prefix_cache && exec zsh
```

详见 `private_dot_config/zsh/fzf.zsh` 的探测逻辑与 [shell.md](shell.md)。

### 换了代理端口 / 地址

`dot_gitconfig` 中仅一处引用 `socks5h://127.0.0.1:5376`（`http "https://github.com"`，对该 URL 匹配的
HTTP/HTTPS 远程均生效），已与 `private_dot_ssh/private_config` 的 `ProxyCommand` 探测端口 `5376` 统一
（`nc -z 127.0.0.1 5376`），全局替换即可。
历史遗留的冗余 `[https …]` / `[ssh "ssh.github.com"]` 段及注释化全局代理段均已清理，无需再处理旧注释。详见 [dev-tools.md](dev-tools.md) 与 [getting-started.md](getting-started.md)。

### auto-update 与 update-all 的区别

`auto-update` 现为 `update-all` 的薄包装：打印 🚀 横幅、（若定义）先执行 `onproxy` 切代理，
随后直接调用 `update-all`（无参全量）。二者覆盖目标与失败统计行为完全一致：

| 维度 | `auto-update` | `update-all` |
| --- | --- | --- |
| 定义位置 | `aliases.zsh:53` | `aliases.zsh:206` |
| 覆盖目标 | 6 项（同 `update-all`，经委托实现） | 6 项：`brew` / `sdk` / `rustup` / `tldr` / `uv` / `mise`（含 `mise upgrade`） |
| 参数 | 无参数，固定调用 `update-all` 全量 | 支持 `update-all brew mise` 参数过滤，未传参则全量；未知目标报错并提示可用列表 |
| 守卫与容错 | 由 `update-all` 实现 | 循环内 `command -v $name` 守卫 + `eval` 失败则 `failed++` |
| 统计与输出 | 由 `update-all` 提供（另加 🚀 横幅与可选 `onproxy`） | 失败计数 `failed`、耗时 `mins` / `secs`、`print -P` 彩色输出（蓝标题/绿成功/黄跳过/红失败） |
| 适用场景 | 兼容旧习惯的一键全量（含代理切换） | 需单目标更新、需查看耗时与失败统计、脚本化调用 |

> 历史：旧版 `auto_update` 曾顺序守卫调用五个 `*_update` 辅助函数（不含 `mise`），
> 这些函数已在提交 `0af1f61` 中删除，`auto_update` 随之改为委托 `update-all`。

两者均定义于 `private_dot_config/zsh/aliases.zsh`，`zsh -n` 已覆盖其语法校验。
详见 [dev-tools.md](dev-tools.md) 与 `aliases.zsh` 源码。

### Go / Python 路径强绑定个人环境

- `GOPATH=~/.local/share/go`、`GOPROXY=https://goproxy.cn,direct`（`private_dot_config/zsh/sdk.zsh`，与 fish `00_env.fish` 统一）
- `pip` 清华镜像别名（`private_dot_config/zsh/aliases.zsh` 的 `pip_tsinghua_mirror`）、`uv` 镜像开关注释（`sdk.zsh`）

新机器路径不一致时按需调整源文件后 `chezmoi diff` → `apply`。详见 [shell.md](shell.md) 与 `sdk.zsh` 注释。

### `$HOME` 与仓库出现漂移（`diff` 有输出）

说明目标文件在应用后被直接改过（例如工具自动写回配置）。两种处理：

1. 这些改动是想要的 → 把内容合并回源文件再提交；
2. 是临时产物 → 直接 `chezmoi apply` 覆盖回去。

**不要**让漂移长期存在，否则无法分清哪边是权威版本。
可用 `chezmoi status` / `chezmoi diff` 快速查看漂移文件列表。

### .chezmoiignore 生效范围

`.chezmoiignore`（仓库根）控制 `chezmoi add` / `apply` 时忽略的**目标名**模式（模式按部署后的目标路径匹配，不是源文件名），当前包括：

- 本地覆盖与备份：`*.local`、`*.local.*`、`*.bak`、`**/.DS_Store`、`nvim.log`
- 仓库文档：`**/README.md`（根级与嵌套，含 `zsh/README.md`、`nvim/README.md`）、`**/LICENSE`（含 `nvim/LICENSE`）、`docs/`
- 敏感信息：`**/*token*`、`**/*secret*`、`**/*credential*`（`**` 前缀覆盖嵌套目录）
- 构建产物：`node_modules/`、`.pnpm-store/`
- fish 机器本地状态：`.config/fish/fish_variables`（fish Universal Variables，仅本机）

> 历史修正（2026-08 收口）：旧版曾按源名书写 `**/dot_git` / `**/dot_DS_Store` / `dot_gitconfig`（均不匹配目标名 `.git` / `.DS_Store` / `.gitconfig`，从未生效），且 `**/README.md` 误拼为 `**/REAMDME.md`、缺 `**/LICENSE`——现已全部按目标名改写、删除无效行并补齐。因此 `dot_gitconfig` → `~/.gitconfig` 为**正常部署目标**（旧文档称其被排除、"仅作本地参考快照"系对无效行的误读）；修复后 `chezmoi managed` 目标数 59→55；后续去重又删除了被更宽模式覆盖或已无对应文件的冗余行（根级 `README.md` / `LICENSE`、`docs/**`、`**/.git`、`*client_secret*`、两条 `**.md` 及已不存在的 `REPO-INSIGHT.md`），目标数保持 55 不变（核心 targets 不变），其后 fish 配置扩容实测曾达 81（纳入 `.config/fish/fish_variables` 后为 82，详见 [layout.md](layout.md)）。随后添加 `.config/fish/fish_variables` 至 `.chezmoiignore` 进一步排除。详见 [layout.md](layout.md)。

注意：`docs/` 被忽略意味着文档改动仅在仓库内维护，不会 `apply` 到 `$HOME`。新增文档请同步更新 [layout.md](layout.md) 的索引。

### 关于历史上的 `baseline` 标签

旧注释曾提到用 `git show baseline:...` 找回已删除的配置（`conda`、wezterm 别名等），现已改为直接指向
git 历史。本仓库自 `init` 提交起从未打过 `baseline` 标签（`git tag` 为空），旧内容来自更早的独立
`zsh-config` 仓库；如确需找回请去旧仓库翻历史。不要在本仓库中创建同名标签造成混淆。

### 新增文件的命名提醒

`chezmoi add` 会自动推断前缀；手工放文件进源目录时要记得：

- 隐藏文件加 `dot_`、要收紧权限的加 `private_`、符号链接用 `symlink_`（内容写目标路径）、可执行文件加 `executable_`
- 模板文件追加 `.tmpl` 后缀

详见 [layout.md](layout.md)。新增配置请同步更新 [layout.md](layout.md) 的映射表与 [getting-started.md](getting-started.md) 的验证清单。
