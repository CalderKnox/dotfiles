--[[
  lazy.nvim 引导与插件管理入口

  作用：确保 lazy.nvim 已安装，并将其加入 runtimepath，再调用 setup 加载
        LazyVim 发行版插件与本地 lua/plugins/ 下的自定义插件规格。
  加载时机：由 Neovim 启动流程（通常 init.lua）require 本文件，属于最早执行的
            用户配置之一；决定后续几乎所有插件如何安装、懒加载与更新。
  影响范围：全局——所有通过 lazy 管理的插件、启动性能、配色安装回退等。
]]

-- 若 data 目录下尚无 lazy.nvim，则从 GitHub stable 分支浅克隆一份。
-- --filter=blob:none 减少初次克隆体积；失败则打印错误并退出，避免半残环境继续跑。
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not (vim.uv or vim.loop).fs_stat(lazypath) then
  local lazyrepo = "https://github.com/folke/lazy.nvim.git"
  local out = vim.fn.system({ "git", "clone", "--filter=blob:none", "--branch=stable", lazyrepo, lazypath })
  if vim.v.shell_error ~= 0 then
    vim.api.nvim_echo({
      { "Failed to clone lazy.nvim:\n", "ErrorMsg" },
      { out, "WarningMsg" },
      { "\nPress any key to exit..." },
    }, true, {})
    vim.fn.getchar()
    os.exit(1)
  end
end
-- 把 lazy.nvim 放到 rtp 最前，才能 require("lazy")
vim.opt.rtp:prepend(lazypath)

require("lazy").setup({
  spec = {
    -- 拉取 LazyVim 本体，并 import 其默认插件集（LSP、UI、编辑增强等）
    { "LazyVim/LazyVim", import = "lazyvim.plugins" },
    -- 再导入本仓库 lua/plugins/ 下的规格，用于覆盖或追加插件
    { import = "plugins" },
  },
  defaults = {
    -- LazyVim 自带插件默认懒加载；自定义插件默认启动时加载。
    -- 设为 true 可让自定义插件也默认懒加载（需各规格自行声明触发条件）。
    lazy = false,
    -- 默认跟最新 git commit，避免部分插件 semver 过旧导致安装后行为异常。
    version = false, -- always use the latest git commit
    -- version = "*", -- try installing the latest stable version for plugins that support semver
  },
  install = {
    -- 首次安装/缺少配色时优先 catppuccin，回退 habamax，避免短暂无主题白屏
    colorscheme = { "catppuccin", "habamax" },
  },
  checker = {
    enabled = true, -- 后台周期性检查插件更新
    notify = false, -- 有更新时不弹通知，避免打断编辑流；可在 Lazy UI 里查看
  },
  performance = {
    rtp = {
      -- 禁用不常用的内置 rtp 插件，略减启动与 rtp 扫描开销。
      -- 被注释的项保留启用（如 matchparen），按需再关掉。
      disabled_plugins = {
        "gzip",
        -- "matchit",
        -- "matchparen",
        -- "netrwPlugin",
        "tarPlugin",
        "tohtml",
        "tutor",
        "zipPlugin",
      },
    },
  },
})
