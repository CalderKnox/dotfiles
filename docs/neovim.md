# Neovim：LazyVim 配置

`dot_config/nvim/` 是 chezmoi 管理的静态 LazyVim 配置，部署到
`~/.config/nvim/`。首次启动可能联网安装 lazy.nvim 与插件；离线验证不会执行这个
bootstrap。当前验证使用 Neovim 0.12.5；本机 LazyVim 16.0.1 要求 Neovim ≥ 0.11.2
（LuaJIT）。由于插件未由仓库锁定，最低版本应同时核对上游要求。

## 架构与事实来源

| 源文件 | 职责 |
| --- | --- |
| `init.lua` | `require("config.lazy")` |
| `lua/config/lazy.lua` | bootstrap lazy.nvim，导入 `lazyvim.plugins` 与本地 `plugins` |
| `lazyvim.json` | 22 个 extras 声明，包括语言、DAP、测试、编辑器与 Sidekick；完整列表以此文件为准 |
| `lua/config/options.lua` | `lazyvim_python_lsp=pyrefly`、scrolloff 8、120 列标线、showmatch、禁用 modeline |
| `lua/config/keymaps.lua` | 唯一的本地映射：Insert 模式 `jk` → Escape；其他映射沿用上游 |
| `lua/config/autocmds.lua` | `HighlightCursorLine` 组；仅完整 Normal 模式显示 cursorline |
| `lua/plugins/colorscheme.lua` | LazyVim 主题覆盖为 Catppuccin |
| `lua/plugins/mason.lua` | Mason 工具列表，含 pyrefly、ruff、debugpy、Biome、Go/Rust 等工具 |
| `lua/plugins/sidekick.lua` | CLI-only：`nes.enabled=false`，不启用 Copilot NES LSP |
| `stylua.toml` | 2 空格，120 列 |
| `README.md` | 仓库内安装概览；不部署 |

选项未在本地覆盖时由 LazyVim 或插件决定，不应将历史的 4 空格缩进、行号、剪贴板、
搜索等描述当成本仓库保证。配置加载由 LazyVim 管理：options 较早加载；keymaps
通常在 VeryLazy 阶段，autocmds 也可能在带文件启动时更早加载。

## cursorline 契约

旧的 InsertEnter/InsertLeave 实现会漏掉 Ctrl-C，因为它退出插入模式时不触发
InsertLeave。现在根据 ModeChanged 的实际模式同步，并在加载和 WinEnter 时刷新
window-local 选项。Insert、Replace、Visual、Ctrl-O 暂时 Normal 状态不显示高亮；
完整 Normal（`mode(1)=="n"`）显示。重复 source 会清空并重建同一 augroup。

## 插件与更新边界

- `lazy-lock.json` 不入库，各机运行时生成；浮动安装不能保证跨机相同版本。
- `:Lazy update` 更新插件并写入本机 lock；`:Lazy restore` 按本机 lock 恢复；
  `:Lazy sync` 安装、清理、更新。
- Mason 与 LSP 运行时下载依赖外部 registry，静态 Lua 解析不证明下载或服务可用。
- Shell 的 `update-all` 不更新 Neovim 插件；两个通道独立。
- 新增本地 spec 放入 `lua/plugins/`；声明 extras 修改 `lazyvim.json` 或使用 `:LazyExtras`
  后把目标端改动合并回源。

## 验证

```sh
python3 docs/validation/check.py --strict
```

包括逐文件 Lua 解析、真实 Neovim 输入产生的模式转换、窗口切换与重复加载，以及
本地 options/keymaps/plugin specs 的运行时断言。测试启动 `nvim -u NONE -i NONE -n`，
只加载指定源文件，**不会**安装或初始化真实 LazyVim 插件。

详见 [离线验证](validation/README.md)、[优化报告](optimization.md) 和
[子目录安装概览](../dot_config/nvim/README.md)。
