# 终端：Ghostty（主力）、Alacritty（备用）与 kitty

三套配置可独立安装、互不依赖；Ghostty 使用 `JetBrainsMonoNL Nerd Font Mono`，Alacritty/kitty 使用 `JetBrainsMono Nerd Font Mono`。Ghostty 为日常主力（支持热重载、Quick Terminal），Alacritty 为轻量备用，kitty 仅以增量个人配置 `kitty.local.conf` 入库作参考、不部署（目标机文件机器本地维护，在新机生成的默认 `kitty.conf` 末尾 `include` 引入即可，见下文）。四者的 shell 均已统一为 fish：Ghostty `command = fish -l`、Alacritty `shell = fish + tmux`、kitty `shell = fish`、tmux `default-shell = fish`（无 fish 环境时 tmux 侧经 if-shell 自动回退 `/bin/bash`，见 `dot_tmux.conf`；其余三者为硬编码路径）。

> **分工**：本文件只解释终端模拟器自身的配置思路与日常使用，不重复具体数值。提示符与配色方案的完整定义（Starship `catppuccin_mocha`、powerline 格式与各段样式）见 [shell.md — Starship 提示符](shell.md#starship-提示符机器本地-starshiptoml)。所有实际配置值（字体、透明度、键位、配色等）一律以源文件为唯一权威：Ghostty 见 `dot_config/ghostty/config`，Alacritty 见 `dot_config/alacritty/alacritty.toml`，kitty 见 `dot_config/kitty/kitty.local.conf`。

---

## Ghostty — `dot_config/ghostty/config`

部署到 `~/.config/ghostty/config`。查看最终生效值用 `ghostty +show-config`（`--default --docs` 可对照默认值）；CLI 默认不在 PATH，需在 Ghostty 菜单 → "Install CLI tool" 安装，或用全路径 `/Applications/Ghostty.app/Contents/MacOS/ghostty`。

- **启动即 Fish 登录 shell**：`command = /opt/homebrew/bin/fish -l`（与 tmux `default-shell` 一致——tmux 侧含 Homebrew fish → `/usr/bin/fish` → `/bin/bash` 的 if-shell 回退链，无 fish 环境自动回退；`working-directory = ~/workspaces`）；`zsh -l` / `tmux` 等方案以注释形式保留为备用。
- **外观与 macOS 集成**：Catppuccin Mocha 主题、JetBrainsMonoNL Nerd Font Mono、毛玻璃与窗口装饰策略；具体数值（透明度、字号、padding、光标样式等）见源文件。
- **键位**：基本沿用 Ghostty 默认，并叠加若干自定义绑定（标签 / 分屏 / 字号 / Quick Terminal 等）；完整 `keybind` 列表以源文件为准。
- **安全与剪贴板**：允许系统剪贴板读写并启用粘贴保护；`quit-after-last-window-closed` 在源中仅为注释模板，并非本仓库启用的行为。
- **Quick Terminal**：顶部下拉、失焦自动收起；screen/animation-duration 在源码中为注释模板，实际默认由 Ghostty 版本决定。
- **性能与存储**：`window-save-state = always`；scrollback-limit/image-storage-limit 的示例数值为注释，并非生效设置。

> 历史上曾存在重复赋值的键，已按 Ghostty「末次赋值生效」语义去重为单次赋值，实际行为不变。

## Alacritty — `dot_config/alacritty/alacritty.toml`

轻量备用，Catppuccin Mocha 配色（与 Ghostty 同主题；Dracula 调色板整块注释保留为模板），与 Ghostty 互为独立配置，切换无需改另一文件。

- **启动即 Fish + tmux**：`alacritty.toml` 的 `shell = { program = "/opt/homebrew/bin/fish", args = ["-c", "tmux new -A -s main"] }`（共享 tmux 会话，Ghostty 已直接使用 Fish，此处通过 tmux 复用）；毛玻璃、仅右 Option 作 Alt 等与 Ghostty 策略一致。
- **字体**为 JetBrainsMono Nerd Font Mono、`size = 16`；Ghostty 使用 NL 变体。
- **配色**：活跃调色板为 Catppuccin Mocha（`colors.primary / normal / bright` 的 `#1e1e2e` / `#f38ba8` 系列）；Dracula 块整体注释保留，需要时取消注释切换。实际 hex 值以源文件 `alacritty.toml` 的 `[colors]` 为准。
- **键位**：复用交给 tmux，故屏蔽 `Cmd+T` / `Cmd+N`、保留 `Cmd+Enter` 切换全屏；其余自定义绑定见源文件。

## kitty — `dot_config/kitty/kitty.local.conf`（仅仓库参考，不部署）

仓库中的 `kitty.local.conf` 仅入库作参考、**不部署**：`.chezmoiignore` 的 `**/*.local.*` 已将其排除（`chezmoi ignored` 含 `.config/kitty/kitty.local.conf`，`chezmoi managed` 不含该文件）。目标机的 `~/.config/kitty/kitty.local.conf` 为机器本地维护文件，新机需从仓库版本手工拷贝或自建，并在 kitty 首次启动生成的 `~/.config/kitty/kitty.conf` 末尾手工添加一行 `include kitty.local.conf` 引入（kitty 不会自动读取该文件名；仓库有意不含 `kitty.conf`，避免整份覆盖上游默认值，此操作一次即可）。之后可用 `Cmd+,`（`edit_config_file`）编辑、`Ctrl+Cmd+,`（`load_config_file`）热重载。

- **启动即 Fish**：`shell = /opt/homebrew/bin/fish --login --interactive`（默认取自 `$SHELL`/passwd，本机为 zsh，故显式固定为 Fish，与 Ghostty 的 `command`、tmux 的 `default-shell` 统一；tmux 侧无 fish 时经 if-shell 自动回退 `/bin/bash`）。
- **字体与外观**：JetBrainsMono Nerd Font Mono、Catppuccin Mocha 配色、powerline 标签栏与 minimal 边框；具体数值见源文件。
- **布局**：`enabled_layouts splits:split_axis=horizontal,*` 让方向分屏快捷键在新标签默认的 splits 布局中生效，并保留其他布局。
- **键位**：`Cmd+T` 在 `~/workspaces` 开新标签页、`Cmd+D` / `Cmd+Shift+D` 横纵分屏、`Cmd+Shift+Enter` 在相邻位置开窗、`Cmd+1`–`Cmd+9` 标签跳转等；完整 `map` 列表以源文件为准。

## tmux 插件初始化

`dot_tmux.conf` 先选择 TPM 根目录并在可用时加载 Catppuccin，再构造 status-right，最后运行 TPM 以让 tmux-cpu/tmux-battery 替换占位符。CPU/RAM/battery 不是全部由 Catppuccin 独立提供：RAM 使用已安装 `tmux-cpu` 的 `ram_percentage`。首次使用时，TPM 本身必须先通过上游说明安装到 `~/.config/tmux/plugins/tpm` 或 `~/.tmux/plugins/tpm`；配置里的 `prefix+I` 只能在 TPM 已存在时安装插件，不能安装 TPM 自身。重载会去重 terminal-overrides/features，不会不断追加相同能力。

## 字体安装与校验

```bash
brew install --cask font-jetbrains-mono-nerd-font
ghostty +show-config            # 查看 Ghostty 最终生效值（CLI 需先经 Ghostty 菜单 "Install CLI tool" 安装，
                                #   或用全路径 /Applications/Ghostty.app/Contents/MacOS/ghostty）
ghostty +show-config --default --docs | grep -E "font-family|theme|background-opacity"
alacritty --help | head         # 确认 Alacritty 可执行
```

两个终端均要求 Nerd Font 变体——Starship 提示符与 `lsd`（含 fzf 预览）等工具依赖其中的图标字形（powerline 箭头、OS logo、目录图标）。Starship 渲染细节与调色板说明见 [shell.md](shell.md)。
