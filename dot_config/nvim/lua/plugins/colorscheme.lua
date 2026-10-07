--[[
  配色主题插件规格

  作用：通过覆盖 LazyVim 本体的 opts，把默认 colorscheme 设为 catppuccin。
  加载时机：由 lazy.nvim 在 setup 时 import "plugins"，合并进 LazyVim/LazyVim 规格；
            主题在 Neovim 应用 colorscheme 阶段生效（启动 UI 就绪后可见）。
  为何改 LazyVim 而非单独装插件：LazyVim 已集成主题切换入口，改 opts.colorscheme
            即可与 extras/安装回退（见 config/lazy.lua 的 install.colorscheme）对齐。
]]

return {
  {
    "LazyVim/LazyVim",
    opts = {
      -- 全局默认主题名；启动后 LazyVim 会据此调用 colorscheme
      colorscheme = "catppuccin",
    },
  },
}
