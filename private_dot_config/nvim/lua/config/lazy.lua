-- =============================================================================
-- lazy.lua — LazyVim 引导与插件编排 (chezmoi: lua/config/lazy.lua)
-- =============================================================================
-- Description : Bootstrap lazy.nvim (blobless partial clone, stable) + LazyVim
--               core + 10 extras (9 lang + mini-animate) + 本地 plugins/*
--               spec。install 回退与 checker 静默检查。
-- Usage       : 由 init.lua `require("config.lazy")` 加载；首次启动自动 clone
-- Guards      : vim.uv / vim.loop 双兼容，fs_stat 判空，shell_error 守卫 + 失败退出
-- Author      : Payne
-- =============================================================================
-- Entry point required by init.lua (`require("config.lazy")`).

-- Bootstrap lazy.nvim into stdpath("data")/lazy/lazy.nvim if missing.
-- Uses a blobless (partial) clone of the stable branch for speed — no --depth,
-- so lazy.nvim can still resolve plugins' history/tags when needed.
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not (vim.uv or vim.loop).fs_stat(lazypath) then
  local lazyrepo = "https://github.com/folke/lazy.nvim.git"
  local out = vim.fn.system({ "git", "clone", "--filter=blob:none", "--branch=stable", lazyrepo, lazypath })
  if vim.v.shell_error ~= 0 then
    vim.api.nvim_echo({
      { "Failed to clone lazy.nvim:\n", "ErrorMsg" },
      { out,                            "WarningMsg" },
      { "\nPress any key to exit..." },
    }, true, {})
    vim.fn.getchar()
    os.exit(1)
  end
end
vim.opt.rtp:prepend(lazypath)

require("lazy").setup({
  spec = {
    -- LazyVim core + default plugins
    { "LazyVim/LazyVim",                                import = "lazyvim.plugins" },
    -- Language & UI extras (source of truth; lazyvim.json `extras: []` is runtime
    -- metadata only). lazyvim.json 由 chezmoi 托管：extras 增删一律改本文件后 chezmoi apply，
    -- :LazyExtras / NEWS 弹窗写入的运行时改动会被 apply 回滚。
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
    -- Custom specs from lua/plugins/*.lua
    { import = "plugins" },
  },

  defaults = {
    lazy = false,    -- custom plugins load at startup; set true to lazy-load all by default
    version = false, -- always latest git commit; version tags are often stale
  },

  install = {
    colorscheme = { "tokyonight", "habamax" }, -- fallback during first install before plugins load
  },

  checker = {
    enabled = true, -- auto-check for plugin updates
    notify = false, -- silent; see :Lazy check manually
  },

  performance = {
    rtp = {
      disabled_plugins = {
        -- Only gzip is re-enabled vs the LazyVim starter (which disables it);
        -- matchit/matchparen/netrwPlugin are default-enabled Vim plugins that
        -- LazyVim never disables.
        "tarPlugin",
        "tohtml",
        "tutor",
        "zipPlugin",
      },
    },
  },
})
