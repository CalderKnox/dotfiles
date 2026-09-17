# 💤 LazyVim

A starter template for [LazyVim](https://github.com/LazyVim/LazyVim) — deployed via [chezmoi](https://www.chezmoi.io/) from `private_dot_config/nvim/` → `~/.config/nvim/`.

> **chezmoi 视角**：本文件由源目录 `.chezmoiignore` 的 `**/README.md` 排除、**不**部署到 `~/.config/nvim/README.md`，仅仓库内查阅。仓库级一致性校验（extras 清单 / 43 锁定 / 选项与键位逐行核对）见 [`docs/neovim.md`](../../docs/neovim.md)，二者互补不重复；改动配置以 `lua/config/*.lua` 与 `lazy-lock.json` 为权威。

## Overview

This is a Neovim configuration based on LazyVim, designed to provide a modern,
highly customizable editor experience with sensible defaults and a great out-of-the-box
setup. This configuration is managed as static files (no templates) and has been
enhanced with comprehensive comments throughout `lua/config/*.lua`.

- **Target**: Neovim ≥ 0.9 (verified on 0.12)
- **Manager**: [lazy.nvim](https://github.com/folke/lazy.nvim) with commit-level lock (`lazy-lock.json`, 43 plugins)
- **Extras**: 10 extras (9 `lang.*` + 1 `ui.mini-animate`, see `lua/config/lazy.lua`)
- **Style**: `stylua.toml` — Spaces, width 2, column 120; `catppuccin` as default colorscheme (via `lua/plugins/example.lua`)

## Installation

### Recommended: via chezmoi (this dotfiles repo)

```bash
# 1. Preview and apply (source is ~/.local/share/chezmoi)
chezmoi diff
chezmoi apply

# 2. Start Neovim — first launch bootstraps lazy.nvim and installs 43 plugins (needs network)
nvim
# :Lazy sync  — if you add plugins later
# :checkhealth — verify LSP / treesitter / provider health
```

No separate `git clone` is needed; `chezmoi apply` already places this directory at `~/.config/nvim/`.

### Standalone (without chezmoi)

If you use this `nvim/` directory outside chezmoi:

```bash
# 1. Backup existing config (optional but recommended)
mv ~/.config/nvim ~/.config/nvim.bak

# 2. Clone / copy this directory
git clone <your-fork-url> ~/.config/nvim
# NOTE: raw cp keeps chezmoi names like dot_gitignore/.gitignore unrenamed — prefer chezmoi apply over manual copy

# 3. Start Neovim (auto-bootstrap)
nvim
```

## Structure

```
~/.config/nvim/  (source: private_dot_config/nvim)
├── init.lua                  → require("config.lazy") only
├── lua/
│   ├── config/
│   │   ├── lazy.lua          bootstrap + spec (LazyVim + 10 extras + plugins)
│   │   ├── options.lua       global options (numbers / 4-space indent / search / truecolor; clipboard & completion inherit LazyVim defaults)
│   │   ├── keymaps.lua       custom keymaps (loaded after LazyVim defaults)
│   │   └── autocmds.lua      autocmds (loaded on VeryLazy)
│   └── plugins/
│       └── example.lua       example specs (effective: catppuccin / fzf-lua(<leader>fp) / pyright / treesitter / lualine 😄 / mason; trouble spec removed, nvim-cmp & second lualine spec disabled; 4-space indent, stylua.toml Spaces-2 pass pending)
├── lazy-lock.json            43 plugins locked by commit (reproducible)
├── lazyvim.json              LazyVim metadata (extras=[], news 11866, version 8 — extras empty is expected, real list is in lazy.lua)
├── stylua.toml               Spaces 2 / 120 columns
├── .gitignore                ignores tag / log / data
├── LICENSE                   Apache-2.0 (LazyVim starter, 与根 LICENSE 同源同哈希)；仓库内，**/LICENSE 排除，不部署
└── README.md                 this file（仓库内，**/README.md 排除，不部署）
```

See [`docs/neovim.md`](../../docs/neovim.md) for the full chezmoi mapping (`dot_gitignore` → `.gitignore`, etc.) and `.chezmoiignore` notes.

## Features

### Extras (lua/config/lazy.lua — 10)

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

9 language extras + `mini-animate`. LSP / formatting / lint are handled by mason + nvim-lspconfig + conform + nvim-lint; mason prompts to install the server on first open of the relevant filetype. `lazyvim.json` `extras: []` is expected — LazyVim writes that file at runtime; the source of truth is `lazy.lua`.

### Locked Plugins (lazy-lock.json — 43)

`LazyVim`, `SchemaStore.nvim`, `blink.cmp`, `bufferline.nvim`, `catppuccin`, `cmake-tools.nvim`,
`conform.nvim`, `crates.nvim`, `flash.nvim`, `friendly-snippets`, `fzf-lua`, `gitsigns.nvim`,
`grug-far.nvim`, `lazy.nvim`, `lazydev.nvim`, `lualine.nvim`, `markdown-preview.nvim`,
`mason-lspconfig.nvim`, `mason.nvim`, `mini.ai`, `mini.animate`, `mini.icons`, `mini.pairs`,
`neo-tree.nvim`, `noice.nvim`, `nui.nvim`, `nvim-lint`, `nvim-lspconfig`,
`nvim-treesitter`, `nvim-treesitter-textobjects`, `nvim-ts-autotag`, `persistence.nvim`,
`plenary.nvim`, `render-markdown.nvim`, `rustaceanvim`, `snacks.nvim`, `telescope.nvim`,
`todo-comments.nvim`, `tokyonight.nvim`, `trouble.nvim`, `ts-comments.nvim`,
`venv-selector.nvim`, `which-key.nvim`.

> Update via `:Lazy update` (syncs lock file) / `:Lazy restore` (rollback). The shell `update-all` (brew/mise/sdk/…) does **not** touch Neovim plugins — the two channels are independent.

### Plugin Highlights (from lua/plugins/example.lua)

- **catppuccin** — set as LazyVim default `colorscheme` (overrides tokyonight)
- **trouble.nvim** — no custom spec: the former `use_diagnostic_signs = true` was a trouble v2-era option (absent from v3 at lock bd67efe); v3 renders diagnostic icons via its own defaults
- **telescope.nvim** — `<leader>fp` "Find Plugin File" + `horizontal / prompt_position=top / ascending` layout
- **nvim-lspconfig** — `pyright` enabled; `tsserver` example kept commented (use the `lang.typescript` extra instead)
- **nvim-treesitter** — `ensure_installed` includes bash/html/javascript/json/lua/markdown/markdown_inline/python/query/regex/tsx/typescript/vim/yaml (single spec; tsx/typescript listed once — the former duplicate spec was merged)
- **mason.nvim** — `ensure_installed` includes stylua / shellcheck / shfmt / flake8
- **lualine.nvim** — appends `😄` component (the second "empty override" spec is now commented out — an opts-function return value replaces merged opts and would wipe LazyVim's entire lualine config)
- **nvim-cmp + cmp-emoji** — **disabled (commented out)**: inert dead config — LazyVim v14 ships blink.cmp and drops nvim-cmp specs unless the `lazyvim.plugins.extras.coding.nvim-cmp` extra is imported, so it never loaded (cmp-emoji is absent from the lock). To enable, import that extra first and run `:Lazy sync`
- *(commented, inactive)*: gruvbox, mini.starter, dap.python, gitsigns/json extras — keep as templates.

> `lazy-lock.json` still pins `fzf-lua`, but no spec references it anymore; a future manual `:Lazy sync` / `:Lazy clean` will drop it (committed lock stays 43 entries, reproducible).

### Built-in Settings (lua/config/options.lua)

- **Line numbers**: `number` + `relativenumber` (absolute current, relative others)
- **Indent**: `tabstop=4` `shiftwidth=4` `expandtab` `smartindent` `autoindent` `wrap=false` (4-space)
- **Scroll**: `scrolloff=8`
- **Clipboard / completion**: NOT set here — LazyVim's defaults are inherited (clipboard is SSH-aware upstream: empty over `SSH_CONNECTION` so the OSC52 provider works remotely; `completeopt=menu,menuone,noselect` is already the upstream default. Former static overrides removed.)
- **Search**: `ignorecase` + `smartcase` + `hlsearch` + `incsearch` + `inccommand=nosplit` + `showmatch` (smart case, incremental highlight)
- **Colors**: `termguicolors` + `colorcolumn="100"` (true color, 100-column ruler)
- **Cursorline**: highlighted only in Normal mode (toggled via `InsertEnter`/`InsertLeave` autocmd)

### Key Mappings (lua/config/keymaps.lua)

Leader is `<Space>` (LazyVim default). Custom mappings loaded after defaults (so you can override):

| Keymap            | Mode | Action                      | Description                  |
| ----------------- | ---- | --------------------------- | ---------------------------- |
| `jk`              | i    | `<ESC>`                     | Exit insert mode             |
| `<leader><space>` | n    | `<cmd>nohlsearch<CR>`       | Clear search highlights      |
| `<leader>sv`      | n    | `<C-w>v`                    | Split window vertically      |
| `<leader>sh`      | n    | `<C-w>s`                    | Split window horizontally    |
| `<leader>rl`      | n    | `<cmd>set relativenumber!<CR>` | Toggle relative line numbers |

> **Note**: a former `<leader>bd` → raw `<cmd>bdelete<CR>` map was removed — it silently overrode LazyVim's built-in `<leader>bd` (Snacks.bufdelete, keeps window layout) while claiming to complement it; LazyVim's `<leader>bD` remains the raw `:bd` variant.

> **Note**: historical `<leader>u` (UndotreeToggle) and `<leader>f` (LSP format) maps were removed — the former errored `E492` because `mbbill/undotree` is neither in `lazy-lock.json` nor in `lua/plugins/`, and both clobbered LazyVim's `<leader>u` / `<leader>f` group prefixes. To restore undotree, first add a real spec (e.g. `return { "mbbill/undotree" }` + `:Lazy sync`), then map keys; formatting uses LazyVim's built-in `<leader>cf` / `<leader>uf`.

All other keys are LazyVim defaults (flash, neo-tree, snacks, bufferline, which-key, etc.). Press `<leader>` and wait for which-key to see the full list; full reference at [lazyvim.org/keymaps](https://www.lazyvim.org/keymaps).

### Autocmds (lua/config/autocmds.lua)

| Event | Group | Pattern | Action |
| ----- | ----- | ------- | ------ |
| `InsertEnter`/`InsertLeave` | `user_cursorline_toggle` | `*` | Cursorline only in Normal mode |

> yank 高亮与窗口均分已由 LazyVim v16 上游覆盖，不再重复定义。

> No per-filetype autocmds: the former `FileType python` row was stale (removed from autocmds.lua as redundant) — indentation is set globally in `options.lua` (4-space) and per-filetype needs would go in `autocmds.lua`.

> Format-on-save is now handled solely by LazyVim's built-in autoformat (on by default; toggle with `<leader>uf` / `<leader>uF`). The custom `FormatOnSave` `BufWritePre` autocmd was removed — it double-formatted every save and kept running even after autoformat was disabled.

## Customization

#### Adding Plugins

Create new files in `lua/plugins/` (or edit `lua/plugins/example.lua`). Every spec under `lua/plugins/` is auto-loaded by lazy.nvim:

```lua
-- lua/plugins/my.lua
return { "mbbill/undotree", cmd = "UndotreeToggle" }
```

The guard `-- if true then return {} end` at the top of `example.lua` is currently **commented out** (specs are active). Uncomment it to disable the file and use it as a pure template.

#### Modifying Options

Edit `lua/config/options.lua` for globals, or override via the `opts` field in a plugin spec.

#### Key Mappings

Add custom maps in `lua/config/keymaps.lua` (loaded after LazyVim defaults, so you can override). Use `desc` for which-key hints:

```lua
vim.keymap.set("n", "<leader>sv", "<C-w>v", { desc = "Split window vertically" })
```

## Updating & Health

- **Check**: `:Lazy` — plugin status; `:checkhealth` — LSP / treesitter / providers.
- **Update**: `:Lazy update` (updates `lazy-lock.json`) · **Restore**: `:Lazy restore` · **Sync**: `:Lazy sync`.
- **Checker**: `lua/config/lazy.lua` sets `checker.enabled=true, notify=false` (silent background check).
- **Shell**: `update-all` / `auto-update` in `private_dot_config/zsh/aliases.zsh` cover brew/mise/sdk/… **only** — run `:Lazy update` separately for Neovim.

## Relationship to docs/neovim.md

- This README = **repository view** (kept in the source tree; excluded by `.chezmoiignore` `**/README.md`, not deployed to `~/.config/nvim/README.md`) — installation, features, keymaps, settings.
- [`docs/neovim.md`](../../docs/neovim.md) = **repository view (maintainer)** — source structure, file-by-file mapping, extras provenance, lock verification, autocmd groups, and the `update-all` boundary.
- Both share the same numbers: **10 extras (9 lang + mini-animate)** and **43 locked plugins** / **5 custom keymaps**; conflicts — `lua/config/*.lua` + `lazy-lock.json` win.

## License

Apache-2.0 — See the [LICENSE](LICENSE) file for details.
