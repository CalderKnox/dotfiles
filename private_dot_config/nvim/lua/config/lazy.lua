-- =============================================================================
-- lazy.lua — LazyVim 引导与插件编排 (chezmoi: lua/config/lazy.lua)
-- =============================================================================
-- Description : Bootstrap lazy.nvim（blobless 部分克隆，stable 分支）+ LazyVim
--               核心 + 10 extras（9 语言 + mini-animate）+ 本地 plugins/*
--               spec。install 回退与 checker 静默检查。
-- Usage       : 由 init.lua `require("config.lazy")` 加载；首次启动自动 clone
-- Guards      : vim.uv / vim.loop 双兼容，fs_stat 判空，shell_error 守卫 + 失败退出
-- Author      : Payne
-- =============================================================================
-- init.lua 所要求的入口（`require("config.lazy")`）。

-- 缺失时将 lazy.nvim bootstrap 到 stdpath("data")/lazy/lazy.nvim。
-- 为提速使用 stable 分支的 blobless（部分）克隆——不用 --depth，
-- 因此 lazy.nvim 仍能在需要时解析插件的历史/标签。
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
    -- LazyVim 核心 + 默认插件
    { "LazyVim/LazyVim",                                import = "lazyvim.plugins" },
    -- 语言与 UI extras（唯一事实来源；lazyvim.json 的 `extras: []` 仅为运行时元数据）。lazyvim.json 由 chezmoi 托管：extras 增删一律改本文件后 chezmoi apply，
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
    -- 来自 lua/plugins/*.lua 的自定义 spec
    { import = "plugins" },
  },

  defaults = {
    lazy = false,    -- 自定义插件随启动加载；设 true 则默认全部惰性加载
    version = false, -- 总是最新 git commit；version 标签往往滞后
  },

  install = {
    colorscheme = { "tokyonight", "habamax" }, -- 首次安装、插件未加载前的回退配色
  },

  checker = {
    enabled = true, -- 自动检查插件更新
    notify = false, -- 静默；手动执行 :Lazy check 查看
  },

  performance = {
    rtp = {
      disabled_plugins = {
        -- 相比 LazyVim starter（其禁用 gzip）仅重新启用 gzip；
        -- matchit/matchparen/netrwPlugin 是默认启用的 Vim 插件，
        -- LazyVim 从不禁用它们。
        "tarPlugin",
        "tohtml",
        "tutor",
        "zipPlugin",
      },
    },
  },
})
