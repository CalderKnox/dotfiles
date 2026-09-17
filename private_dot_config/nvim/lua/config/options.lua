-- =============================================================================
-- options.lua — 全局编辑器选项 (chezmoi: lua/config/options.lua)
-- =============================================================================
-- Description : 增量覆盖 LazyVim 默认的全局 vim.opt（与上游相同的项一律不写）。
--               分组：缩进宽度、显示滚动、搜索锚点与标尺；剪贴板/补全
--               刻意不覆盖（上游默认更优，见下方说明）。
-- Usage       : 在 LazyVim defaults 之后加载，值在此覆盖同名项；`:h <option>`
-- Guards      : 无外部依赖；所有选项幂等，重复加载安全
-- Author      : Payne
-- =============================================================================
-- Global editor options. Loaded *after* LazyVim's defaults, so values here
-- override LazyVim where they overlap. See `:h <option>` for details.
-- Only overrides and additions are set here; LazyVim handles the rest.

-- Clipboard / completion: deliberately NOT overridden. LazyVim's defaults are
-- smarter than static values here:
--   clipboard   — upstream is SSH-aware (empty over SSH_CONNECTION, enabling
--                 the OSC52 provider); a bare `unnamedplus` would break remote
--                 sessions, so it was removed from this file.
--   completeopt — upstream default is exactly `menu,menuone,noselect`; the
--                 former duplicate override (mislabeled as a customization)
--                 was removed.

-- Indentation width: 4 spaces (LazyVim default is 2). expandtab/smartindent
-- already match upstream and are not re-set; per-filetype overrides can be
-- added in autocmds.lua if a language needs a different width.
vim.opt.tabstop = 4 -- display width of <Tab>
vim.opt.shiftwidth = 4 -- size of >> / << and autoindent step

-- Display & scrolling
vim.opt.scrolloff = 8 -- keep 8 lines above/below cursor for context while scrolling (upstream: 4)
vim.opt.colorcolumn = "100" -- ruler at 100 cols as line-length guide

-- Search: hlsearch/incsearch are Neovim defaults and are not re-set here;
-- clear highlights with <leader><space> (see keymaps.lua). showmatch below is
-- a genuine override (Vim default: off).
vim.opt.showmatch = true -- briefly jump to matching bracket when cursor is on one
