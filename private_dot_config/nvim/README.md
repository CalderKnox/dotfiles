# 💤 LazyVim

[LazyVim](https://github.com/LazyVim/LazyVim) 的 starter 模板 —— 经 [chezmoi](https://www.chezmoi.io/) 从 `private_dot_config/nvim/` 部署到 `~/.config/nvim/`。

> **chezmoi 视角**：本文件由源目录 `.chezmoiignore` 的 `**/README.md` 排除、**不**部署到 `~/.config/nvim/README.md`，仅仓库内查阅。仓库级一致性校验（extras 清单 / 43 锁定 / 选项与键位逐行核对）见 [`docs/neovim.md`](../../docs/neovim.md)，二者互补不重复；改动配置以 `lua/config/*.lua` 与 `lazy-lock.json` 为权威。

## 概览

基于 LazyVim 的 Neovim 配置，目标是提供现代化、高度可定制的编辑器体验：默认值合理、开箱即用。本配置以静态文件管理（无模板），并在 `lua/config/*.lua` 全程附有详尽注释。

- **目标版本**：Neovim ≥ 0.9（本机验证 0.12）
- **管理器**：[lazy.nvim](https://github.com/folke/lazy.nvim)，commit 级锁定（`lazy-lock.json`，43 个插件）
- **Extras**：10 个 extras（9 个 `lang.*` + 1 个 `ui.mini-animate`，见 `lua/config/lazy.lua`）
- **风格**：`stylua.toml` —— Spaces、宽度 2、列宽 120；默认配色 `catppuccin`（经 `lua/plugins/example.lua`）

## 安装

### 推荐：经 chezmoi（本 dotfiles 仓库）

```bash
# 1. 预览并应用（源目录为 ~/.local/share/chezmoi）
chezmoi diff
chezmoi apply

# 2. 启动 Neovim —— 首次启动会 bootstrap lazy.nvim 并安装 43 个插件（需网络）
nvim
# :Lazy sync    —— 以后新增插件后执行
# :checkhealth  —— 校验 LSP / treesitter / provider 健康度
```

无需单独 `git clone`；`chezmoi apply` 已将本目录放置到 `~/.config/nvim/`。

### 独立使用（不经 chezmoi）

若要在 chezmoi 之外使用本 `nvim/` 目录：

```bash
# 1. 备份已有配置（可选但推荐）
mv ~/.config/nvim ~/.config/nvim.bak

# 2. 克隆/拷贝本目录
git clone <your-fork-url> ~/.config/nvim
# 注意：裸 cp 会保留 dot_gitignore/.gitignore 这类 chezmoi 命名——优先用 chezmoi apply，而非手工拷贝

# 3. 启动 Neovim（自动 bootstrap）
nvim
```

## 目录结构

```
~/.config/nvim/  （源: private_dot_config/nvim）
├── init.lua                  → 仅 require("config.lazy")
├── lua/
│   ├── config/
│   │   ├── lazy.lua          bootstrap + spec（LazyVim + 10 extras + plugins）
│   │   ├── options.lua       全局选项（行号 / 4 空格缩进 / 搜索 / 真彩；剪贴板与补全沿用 LazyVim 默认）
│   │   ├── keymaps.lua       自定义键位（在 LazyVim 默认之后加载）
│   │   └── autocmds.lua      自动命令（VeryLazy 时加载）
│   └── plugins/
│       └── example.lua       示例 spec（已生效：catppuccin / fzf-lua(<leader>fp) / lualine 😄 / mason；trouble spec 已移除，nvim-cmp 与第二个 lualine spec 已禁用）
├── lazy-lock.json            43 个插件按 commit 锁定（可复现）
├── lazyvim.json              LazyVim 元数据（extras=[]、news 11866、version 8 —— extras 为空是预期行为，真实清单在 lazy.lua）
├── stylua.toml               Spaces 2 / 120 列
├── .gitignore                忽略 tag / log / data
├── LICENSE                   Apache-2.0（LazyVim starter，与根 LICENSE 同源同哈希）；仓库内，**/LICENSE 排除，不部署
└── README.md                 本文件（仓库内，**/README.md 排除，不部署）
```

chezmoi 完整映射（`dot_gitignore` → `.gitignore` 等）与 `.chezmoiignore` 说明见 [`docs/neovim.md`](../../docs/neovim.md)。

## 功能特性

### Extras（lua/config/lazy.lua —— 10 个）

```lua
{ import = "lazyvim.plugins.extras.lang.typescript" },
{ import = "lazyvim.plugins.extras.lang.json" },
{ import = "lazyvim.plugins.extras.lang.python" },
{ import = "lazyvim.plugins.extras.lang.rust" },
{ import = "lazyvim.plugins.extras.lang.go" },
{ import = "lazyvim.plugins.extras.lang.cmake" },
{ import = "lazyvim.plugins.extras.lang.docker" },
{ import = "lazyvim.plugins.extras.lang.yaml" },
{ import = "lazyvim.plugins.extras.lang.markdown" },
{ import = "lazyvim.plugins.extras.ui.mini-animate" },
```

9 个语言 extras + `mini-animate`。LSP / 格式化 / lint 由 mason + nvim-lspconfig + conform + nvim-lint 组合处理；首次打开对应语言文件时 mason 会提示安装相应 server。`lazyvim.json` 的 `extras: []` 是预期行为——该文件由 LazyVim 在运行时写入；唯一事实来源是 `lazy.lua`。

### 锁定插件（lazy-lock.json —— 43 个）

`LazyVim`、`SchemaStore.nvim`、`blink.cmp`、`bufferline.nvim`、`catppuccin`、`cmake-tools.nvim`、
`conform.nvim`、`crates.nvim`、`flash.nvim`、`friendly-snippets`、`fzf-lua`、`gitsigns.nvim`、
`grug-far.nvim`、`lazy.nvim`、`lazydev.nvim`、`lualine.nvim`、`markdown-preview.nvim`、
`mason-lspconfig.nvim`、`mason.nvim`、`mini.ai`、`mini.animate`、`mini.icons`、`mini.pairs`、
`neo-tree.nvim`、`noice.nvim`、`nui.nvim`、`nvim-lint`、`nvim-lspconfig`、
`nvim-treesitter`、`nvim-treesitter-textobjects`、`nvim-ts-autotag`、`persistence.nvim`、
`plenary.nvim`、`render-markdown.nvim`、`rustaceanvim`、`snacks.nvim`、`telescope.nvim`、
`todo-comments.nvim`、`tokyonight.nvim`、`trouble.nvim`、`ts-comments.nvim`、
`venv-selector.nvim`、`which-key.nvim`。

> 更新用 `:Lazy update`（同步 lock 文件）/ `:Lazy restore`（回滚）。shell 的 `update-all`（brew/mise/sdk/…）**不会**触及 Neovim 插件——两条更新通道相互独立。

### 插件要点（来自 lua/plugins/example.lua）

- **catppuccin** —— 设为 LazyVim 默认 `colorscheme`（覆盖 tokyonight）
- **trouble.nvim** —— 无自定义 spec：原 `use_diagnostic_signs = true` 属 trouble v2 时代选项（锁定 bd67efe 的 v3 已无此字段）；v3 经自身默认值渲染诊断图标
- **telescope.nvim** —— `<leader>fp`「查找插件文件」+ `horizontal / prompt_position=top / ascending` 布局
- **nvim-lspconfig** —— 启用 `pyright`；`tsserver` 示例保留注释（改用 `lang.typescript` extra）
- **nvim-treesitter** —— `ensure_installed` 含 bash/html/javascript/json/lua/markdown/markdown_inline/python/query/regex/tsx/typescript/vim/yaml（单一 spec；tsx/typescript 仅列一次——原重复 spec 已合并）
- **mason.nvim** —— `ensure_installed` 含 stylua / shellcheck / shfmt / flake8
- **lualine.nvim** —— 追加 `😄` 组件（第二个「空覆盖」spec 已注释——opts 函数返回值会替换合并后的 opts，会清空 LazyVim 的整个 lualine 配置）
- **nvim-cmp + cmp-emoji** —— **已禁用（注释）**：不生效的死配置——LazyVim v14 自带 blink.cmp，且除非导入 `lazyvim.plugins.extras.coding.nvim-cmp` extra，否则会丢弃 nvim-cmp spec，因此从未真正加载（cmp-emoji 不在 lock 中）。要启用，先导入该 extra 并运行 `:Lazy sync`
- *（注释、未生效）*：gruvbox、mini.starter、dap.python、gitsigns/json extras —— 保留为模板。

> `lazy-lock.json` 仍锁定 `fzf-lua`，但已无 spec 引用；将来手动 `:Lazy sync` / `:Lazy clean` 会将其移除（入库 lock 保持 43 条，可复现）。

### 内置设置（lua/config/options.lua）

- **行号**：`number` + `relativenumber`（当前行绝对、其余相对）
- **缩进**：`tabstop=4` `shiftwidth=4` `expandtab` `smartindent` `autoindent` `wrap=false`（4 空格）
- **滚动**：`scrolloff=8`
- **剪贴板 / 补全**：不在此设置——沿用 LazyVim 默认（上游剪贴板具备 SSH 感知：存在 `SSH_CONNECTION` 时为空，OSC52 provider 可在远程工作；`completeopt=menu,menuone,noselect` 本就是上游默认。原静态覆盖已移除）
- **搜索**：`ignorecase` + `smartcase` + `hlsearch` + `incsearch` + `inccommand=nosplit` + `showmatch`（智能大小写、增量高亮）
- **颜色**：`termguicolors` + `colorcolumn="100"`（真彩、100 列标线）
- **cursorline**：仅普通模式高亮（经 `InsertEnter`/`InsertLeave` autocmd 切换）

### 键位（lua/config/keymaps.lua）

Leader 为 `<Space>`（LazyVim 默认）。自定义映射在默认之后加载（可直接覆盖）：

| 键位              | 模式 | 动作                        | 说明                         |
| ----------------- | ---- | --------------------------- | ---------------------------- |
| `jk`              | i    | `<ESC>`                     | 退出插入模式                 |
| `<leader><space>` | n    | `<cmd>nohlsearch<CR>`       | 清除搜索高亮                 |
| `<leader>sv`      | n    | `<C-w>v`                    | 垂直分屏                     |
| `<leader>sh`      | n    | `<C-w>s`                    | 水平分屏                     |
| `<leader>rl`      | n    | `<cmd>set relativenumber!<CR>` | 切换相对行号              |

> **注意**：原 `<leader>bd` → 裸 `<cmd>bdelete<CR>` 映射已移除——它在声称「补充」的同时静默顶掉了 LazyVim 内置的 `<leader>bd`（Snacks.bufdelete，保留窗口布局）；LazyVim 的 `<leader>bD` 仍是裸 `:bd` 变体。

> **注意**：历史上的 `<leader>u`（UndotreeToggle）与 `<leader>f`（LSP format）映射已移除——前者报 `E492`，因为 `mbbill/undotree` 既不在 `lazy-lock.json` 也不在 `lua/plugins/`，且二者都会顶掉 LazyVim 的 `<leader>u` / `<leader>f` 分组前缀。要恢复 undotree，先添加真实 spec（如 `return { "mbbill/undotree" }` + `:Lazy sync`）再映射键位；格式化用 LazyVim 内置的 `<leader>cf` / `<leader>uf`。

其余键位均为 LazyVim 默认（flash、neo-tree、snacks、bufferline、which-key 等）。按 `<leader>` 等待 which-key 查看完整列表；完整参考见 [lazyvim.org/keymaps](https://www.lazyvim.org/keymaps)。

### 自动命令（lua/config/autocmds.lua）

| 事件  | 分组                    | 模式 | 动作                       |
| ----- | ----------------------- | ---- | -------------------------- |
| `InsertEnter`/`InsertLeave` | `user_cursorline_toggle` | `*` | cursorline 仅普通模式显示 |

> yank 高亮与窗口均分已由 LazyVim v16 上游覆盖，不再重复定义。

> 无按文件类型的 autocmd：原 `FileType python` 一行已过期（作为冗余项从 autocmds.lua 移除）——缩进在 `options.lua` 全局设置（4 空格），按文件类型的需求应写入 `autocmds.lua`。

> 保存时格式化现完全交给 LazyVim 内置 autoformat（默认开启；`<leader>uf` / `<leader>uF` 切换）。自定义 `FormatOnSave` `BufWritePre` autocmd 已移除——它导致每次保存双重格式化，且在 autoformat 关闭后仍在运行。

## 自定义

#### 添加插件

在 `lua/plugins/` 新建文件（或编辑 `lua/plugins/example.lua`）。`lua/plugins/` 下每个 spec 都会被 lazy.nvim 自动加载：

```lua
-- lua/plugins/my.lua
return { "mbbill/undotree", cmd = "UndotreeToggle" }
```

`example.lua` 顶部的守卫 `-- if true then return {} end` 目前处于**注释状态**（spec 生效）。取消其注释即可停用整个文件，将其用作纯模板。

#### 修改选项

编辑 `lua/config/options.lua` 设置全局项，或在插件 spec 中经 `opts` 字段覆盖。

#### 键位映射

在 `lua/config/keymaps.lua` 添加自定义映射（在 LazyVim 默认之后加载，可直接覆盖）。用 `desc` 提供 which-key 提示：

```lua
vim.keymap.set("n", "<leader>sv", "<C-w>v", { desc = "垂直分屏" })
```

## 更新与健康检查

- **查看**：`:Lazy` —— 插件状态；`:checkhealth` —— LSP / treesitter / providers。
- **更新**：`:Lazy update`（更新 `lazy-lock.json`）· **恢复**：`:Lazy restore` · **同步**：`:Lazy sync`。
- **检查器**：`lua/config/lazy.lua` 设 `checker.enabled=true, notify=false`（静默后台检查）。
- **Shell**：`private_dot_config/zsh/aliases.zsh` 的 `update-all` / `auto-update` 只覆盖 brew/mise/sdk/…——Neovim 插件需单独运行 `:Lazy update`。

## 与 docs/neovim.md 的关系

- 本 README = **仓库内视角**（保留在源码树；由 `.chezmoiignore` 的 `**/README.md` 排除，不部署到 `~/.config/nvim/README.md`）——安装、功能、键位、设置。
- [`docs/neovim.md`](../../docs/neovim.md) = **仓库视角（维护者）** —— 源结构、逐文件映射、extras 来源、锁定校验、autocmd 分组及 `update-all` 边界。
- 二者共享同一组数字：**10 个 extras（9 语言 + mini-animate）**与 **43 个锁定插件** / **5 个自定义键位**；如有冲突——以 `lua/config/*.lua` + `lazy-lock.json` 为准。

## 许可证

Apache-2.0 —— 详见 [LICENSE](LICENSE) 文件。
