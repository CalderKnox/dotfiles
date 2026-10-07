-- =============================================================================
-- init.lua — Neovim 入口 (chezmoi: init.lua → ~/.config/nvim/init.lua)
-- =============================================================================
-- Description : 唯一职责：bootstrap lazy.nvim 并加载 LazyVim + 全部插件
--               （委托 lua/config/lazy.lua）。保持极简，便于 chezmoi 静态部署
-- Usage       : nvim 启动时自动加载；首次启动由 lazy.lua 完成 clone 与安装
-- Author      : Payne
-- =============================================================================
require("config.lazy")
