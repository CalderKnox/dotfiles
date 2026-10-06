# 💤 LazyVim

This static Neovim configuration is deployed by chezmoi from
`private_dot_config/nvim/` to `~/.config/nvim/`. This README stays in the repository;
`.chezmoiignore` excludes documentation from deployment.

## Installation

Preview the source-to-HOME changes before applying:

```sh
chezmoi diff
chezmoi apply
nvim
```

The first Neovim launch bootstraps lazy.nvim and downloads plugins if missing.
Current local verification uses Neovim 0.12.5 / LuaJIT; the inspected LazyVim
16.0.1 requires Neovim ≥ 0.11.2. Check upstream requirements when upgrading.

## Configuration

- `init.lua` loads `config.lazy`; `lua/config/lazy.lua` imports LazyVim core
  and `lua/plugins/`.
- `lazyvim.json` declares the extras: language support, DAP, testing, editing,
  UI and Sidekick. Do not rely on an old hard-coded extras list in documentation.
- `lua/plugins/colorscheme.lua` selects Catppuccin.
- `lua/plugins/mason.lua` extends the tool installation list.
- `lua/plugins/sidekick.lua` disables NES, retaining the CLI integration.
- `lua/config/options.lua` selects pyrefly for Python, scrolloff 8, a
  120-column ruler, showmatch and `modeline=false`. Other options inherit upstream defaults.
- `lua/config/keymaps.lua` adds one local mapping: Insert `jk` → Escape.
- `lua/config/autocmds.lua` enables cursorline only in full Normal mode,
  including correct recovery after Ctrl-C; its augroup is reload-idempotent.
- `stylua.toml` configures two-space Lua formatting with width 120.

Detailed architecture and validation contracts are in
[docs/neovim.md](../../docs/neovim.md). All effective local values are determined
by the JSON/Lua source, not copied keymap or plugin tables.

## Customization and updates

Put plugin specs in `lua/plugins/`. Configure options and mappings in
`lua/config/`; use `:LazyExtras` for extras and merge target-file changes back
into the chezmoi source.

- `:Lazy` and `:checkhealth`: runtime/plugin health.
- `:Lazy update`, `:Lazy restore`, `:Lazy sync`: plugin management.
- `lazy-lock.json` is local runtime state, not tracked by this repository;
  installations are not pinned across machines.
- Shell `update-all` does not update Neovim plugins.

## Offline verification

From the repository root:

```sh
python3 docs/validation/check.py --strict
```

The tests use disposable HOME/XDG paths and plugin-free Neovim instances. They
check local Lua syntax, actual mode changes and local overrides—not external
plugin installation, LSP connectivity or a complete LazyVim bootstrap.
See [validation/README.md](../../docs/validation/README.md).

## License

Apache-2.0 declaration retained from the starter; the repository does not contain
its full license text. See the [LazyVim starter](https://github.com/LazyVim/starter).
