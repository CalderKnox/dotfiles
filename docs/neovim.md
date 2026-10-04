# Neovim：LazyVim 配置


`private_dot_config/nvim/` 是基于 [LazyVim](https://www.lazyvim.org/) starter 的 Neovim 配置，目标 Neovim ≥ 0.9（本机验证 0.12）。`chezmoi apply` 渲染为 `~/.config/nvim/`（静态文件，无模板），首次启动由 `lua/config/lazy.lua` 自动 bootstrap `lazy.nvim` 并安装全部插件（最新版；`lazy-lock.json` 已停止跟踪，不再按锁定 commit 复现）。

> **文档分工**：本文档是 chezmoi 仓库视角，说明各组件的结构与配置意图。编辑器面向用户的安装与功能概览见 [`private_dot_config/nvim/README.md`](../private_dot_config/nvim/README.md)（仓库内文档，由 `**/README.md` 排除、不部署到 `~/.config/nvim/README.md`），二者互补不重复。所有实际配置值（extras 清单、选项、键位、自动命令）一律以 `lua/config/*.lua` 为唯一权威，本文不逐行抄录。

## 目录结构

实际文件（`private_dot_config/nvim/**` → `~/.config/nvim/**`，`dot_*` 按 chezmoi 规则还原为 dotfile）：

- `init.lua`：入口，仅 `require("config.lazy")`。
- `lua/config/`：`lazy.lua`（bootstrap 与插件 spec）、`options.lua`（全局选项）、`keymaps.lua`（自定义键位，在 LazyVim 默认之后加载、可直接覆盖）、`autocmds.lua`（自动命令，VeryLazy 时加载）。
- `lua/plugins/`：自定义插件 spec 入口（往此目录加文件即生效，由 `lazy.lua` 的 `{ import = "plugins" }` 加载）；`example.lua` 已删除，当前无自定义插件 spec，仓库不含任何自定义插件（catppuccin 强制配色等示例行为已随删除移除）。
- `lazy-lock.json`：**已停止跟踪**（3c3d65f）——由 lazy.nvim 在目标机 `~/.config/nvim/` 运行时生成，不入库，插件版本不再由仓库锁定。
- `lazyvim.json`：LazyVim 元数据（运行时写入，`extras` 为空是预期行为，真实启用清单以 `lazy.lua` 的 `import` 为准）。
- `stylua.toml`：Lua 格式化规则。
- `dot_gitignore` → `.gitignore`、`README.md`：按 `.chezmoiignore` 规则排除、不部署；`LICENSE` 文件已从仓库删除（`**/LICENSE` 模式防御性保留）。

> 完整映射与忽略规则见 [layout.md](layout.md)。

## 启用的 Extras 与插件策略

- `lazy.lua` 通过 `spec` 导入 LazyVim 自带的一组 `lang.*` extras（TypeScript / JSON / Python / Rust / Go / CMake / Docker / YAML / Markdown）外加 `ui.mini-animate`，并导入本地 `plugins` 目录；**具体 extras 清单以 `lazy.lua` 的 `import` 列表为准**。
- LSP / 格式化 / lint 由 LazyVim 内置的 mason + nvim-lspconfig + conform + nvim-lint 组合处理；首次打开对应语言文件时 mason 会提示安装相应 server。
- **bootstrap**：首次启动时若 `lazy.nvim` 未安装则自动 clone（失败即报错退出），随后幂等 `prepend` 到 `rtp`。
- **更新**：`:Lazy update` 更新插件并刷新目标机本地 lock；`:Lazy restore` 回滚；`:Lazy sync` 清理/安装/更新。`lazy-lock.json` 已停止跟踪（3c3d65f）：lock 仅存在于目标机本地，换机器后安装各插件最新版，跨机不再保证同版本（如需可复现可重新入库该文件）。
- **与 shell `update-all` 无关联**：zsh 的 `update-all` 覆盖 `brew`/`sdk`/`rustup`/`tldr`/`uv`/`mise`/`pi` 七项目标，不触及 Neovim 插件；两者更新通道相互独立。

## 关键设置（设计意图）

- **选项**（`options.lua`）：行号同时显示绝对与相对；4 空格缩进、不折行；搜索智能大小写 + 增量高亮；真彩 24-bit + 100 列标线。剪贴板与补全不覆盖、沿用 LazyVim 上游默认（剪贴板含 SSH 感知）。完整 `vim.opt` 取值以源文件为准。
- **键位**（`keymaps.lua`）：Leader 为空格（LazyVim 默认），本仓库在默认之后叠加少量自定义项（如 `jk` 退出插入、`<leader>sv/sh` 分屏、`<leader>rl` 切换相对行号；`<leader>bd` 关缓冲由 LazyVim 内置 Snacks.bufdelete 提供，不再自定义）；其余沿用 LazyVim 默认，可用 `<leader>` 唤出 which-key 查看。完整映射以 `keymaps.lua` 为准。
- **自动命令**（`autocmds.lua`，VeryLazy 之后加载）：仅保留『仅普通模式高亮 cursorline』一件；yank 高亮与窗口均分已由 LazyVim v16 上游覆盖，不再重复定义（无 per-filetype autocmd，缩进由 `options.lua` 全局提供）；保存时格式化交由 LazyVim 内置 autoformat 接管。完整定义以 `autocmds.lua` 为准。
- **自定义插件**：`lua/plugins/example.lua` 已删除（其 catppuccin 强制配色、telescope 布局、mason 工具清单等生效行为随之移除，配色回落 LazyVim 默认）；当前无任何自定义 spec，需自定义时往 `lua/plugins/` 新增文件即生效。

## 与 private_dot_config/nvim/README.md 的分工

- 本文档（`docs/neovim.md`）：chezmoi 仓库视角，面向维护者，说明结构与各组件的配置意图、与 shell `update-all` 的边界。
- `private_dot_config/nvim/README.md`：仓库内视角，面向新机器使用者，基于 LazyVim starter 模板的安装步骤、功能概览与键位速览。

二者互补不矛盾；改动配置时以 `lua/config/*.lua` 为权威来源（插件版本 lock 文件已不入库）。

## 参见

- [仓库结构与映射](layout.md) · [安装与验证](getting-started.md) · [维护流程](maintenance.md)
- 子目录 README（仓库内，不部署）：[`private_dot_config/nvim/README.md`](../private_dot_config/nvim/README.md)
- 上游文档：[LazyVim](https://www.lazyvim.org/) · [lazy.nvim](https://github.com/folke/lazy.nvim)
