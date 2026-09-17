# Neovim：LazyVim 配置


`private_dot_config/nvim/` 是基于 [LazyVim](https://www.lazyvim.org/) starter 的 Neovim 配置，目标 Neovim ≥ 0.9（本机验证 0.12）。`chezmoi apply` 渲染为 `~/.config/nvim/`（静态文件，无模板），首次启动由 `lua/config/lazy.lua` 自动 bootstrap `lazy.nvim` 并按 `lazy-lock.json` 安装插件。

> **文档分工**：本文档是 chezmoi 仓库视角，说明各组件的结构与配置意图。编辑器面向用户的安装与功能概览见 [`private_dot_config/nvim/README.md`](../private_dot_config/nvim/README.md)（仓库内文档，由 `**/README.md` 排除、不部署到 `~/.config/nvim/README.md`），二者互补不重复。所有实际配置值（extras 清单、选项、键位、自动命令、插件锁定）一律以 `lua/config/*.lua` 与 `lazy-lock.json` 为唯一权威，本文不逐行抄录。

## 目录结构

实际文件（`private_dot_config/nvim/**` → `~/.config/nvim/**`，`dot_*` 按 chezmoi 规则还原为 dotfile）：

- `init.lua`：入口，仅 `require("config.lazy")`。
- `lua/config/`：`lazy.lua`（bootstrap 与插件 spec）、`options.lua`（全局选项）、`keymaps.lua`（自定义键位，在 LazyVim 默认之后加载、可直接覆盖）、`autocmds.lua`（自动命令，VeryLazy 时加载）。
- `lua/plugins/`：自定义插件 spec（往此目录加文件即生效；含已生效的 `example.lua` 示例）。
- `lazy-lock.json`：插件 commit 级锁定（可复现环境）。
- `lazyvim.json`：LazyVim 元数据（运行时写入，`extras` 为空是预期行为，真实启用清单以 `lazy.lua` 的 `import` 为准）。
- `stylua.toml`：Lua 格式化规则。
- `dot_gitignore` → `.gitignore`、`LICENSE`、`README.md`：均按 `.chezmoiignore` 规则部分排除、不部署。

> 完整映射与忽略规则见 [layout.md](layout.md)。

## 启用的 Extras 与插件策略

- `lazy.lua` 通过 `spec` 导入 LazyVim 自带的一组 `lang.*` extras（TypeScript / JSON / Python / Rust / Go / CMake / Docker / YAML / Markdown）外加 `ui.mini-animate`，并导入本地 `plugins` 目录；**具体 extras 清单以 `lazy.lua` 的 `import` 列表为准**。
- LSP / 格式化 / lint 由 LazyVim 内置的 mason + nvim-lspconfig + conform + nvim-lint 组合处理；首次打开对应语言文件时 mason 会提示安装相应 server。
- **bootstrap**：首次启动时若 `lazy.nvim` 未安装则自动 clone（失败即报错退出），随后幂等 `prepend` 到 `rtp`。
- **更新与复现**：`:Lazy update` 更新并同步 lock；`:Lazy restore` 回滚；`:Lazy sync` 清理/安装/更新；换机器后按 `lazy-lock.json` 安装同版本插件。**当前锁定插件的数量与清单以 `lazy-lock.json` 为准**（新增/删除插件后需提交更新后的 lock 文件以保持可复现）。
- **与 shell `update-all` 无关联**：zsh 的 `update-all` 仅覆盖 `brew`/`sdk`/`rustup`/`tldr`/`uv`/`mise` 六项，不触及 Neovim 插件；两者更新通道相互独立。

## 关键设置（设计意图）

- **选项**（`options.lua`）：行号同时显示绝对与相对；4 空格缩进、不折行；搜索智能大小写 + 增量高亮；真彩 24-bit + 100 列标线。剪贴板与补全不覆盖、沿用 LazyVim 上游默认（剪贴板含 SSH 感知）。完整 `vim.opt` 取值以源文件为准。
- **键位**（`keymaps.lua`）：Leader 为空格（LazyVim 默认），本仓库在默认之后叠加少量自定义项（如 `jk` 退出插入、`<leader>sv/sh` 分屏、`<leader>rl` 切换相对行号；`<leader>bd` 关缓冲由 LazyVim 内置 Snacks.bufdelete 提供，不再自定义）；其余沿用 LazyVim 默认，可用 `<leader>` 唤出 which-key 查看。完整映射以 `keymaps.lua` 为准。
- **自动命令**（`autocmds.lua`，VeryLazy 之后加载）：仅保留『仅普通模式高亮 cursorline』一件；yank 高亮与窗口均分已由 LazyVim v16 上游覆盖，不再重复定义（无 per-filetype autocmd，缩进由 `options.lua` 全局提供）；保存时格式化交由 LazyVim 内置 autoformat 接管。完整定义以 `autocmds.lua` 为准。
- **示例插件**（`lua/plugins/example.lua`）：顶部守卫当前为注释状态（示例配置实际生效）；如仅当模板用应取消该行注释。其中部分示例（如 `catppuccin` 强制配色、telescope 布局、mason 工具等）已生效，另一些以注释保留为模板参考。

## 与 private_dot_config/nvim/README.md 的分工

- 本文档（`docs/neovim.md`）：chezmoi 仓库视角，面向维护者，说明结构与各组件的配置意图、与 shell `update-all` 的边界。
- `private_dot_config/nvim/README.md`：仓库内视角，面向新机器使用者，基于 LazyVim starter 模板的安装步骤、功能概览与键位速览。

二者互补不矛盾；改动配置时以 `lua/config/*.lua` 与 `lazy-lock.json` 为权威来源。

## 参见

- [仓库结构与映射](layout.md) · [安装与验证](getting-started.md) · [维护流程](maintenance.md)
- 子目录 README（仓库内，不部署）：[`private_dot_config/nvim/README.md`](../private_dot_config/nvim/README.md)
- 上游文档：[LazyVim](https://www.lazyvim.org/) · [lazy.nvim](https://github.com/folke/lazy.nvim)
