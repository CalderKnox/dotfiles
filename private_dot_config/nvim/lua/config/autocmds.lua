--[[
  自动命令（autocmd）配置

  作用：在特定事件发生时自动执行逻辑，扩展或覆盖 LazyVim 的默认行为。
  加载时机：LazyVim 在 VeryLazy 事件时自动加载本文件（启动后、插件就绪后），
            不会在 Neovim 最早期启动阶段执行。
  与默认的关系：LazyVim 自带一组 autocmd；此处只追加个人定制，不重复定义默认项。
  参考：https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/autocmds.lua
]]

-- 仅在 Normal 模式显示光标行高亮：进入插入模式时关闭，离开插入模式时开启。
-- 动机：插入编辑时 cursorline 容易干扰视线；Normal 模式下保留便于定位当前行。
-- 触发：任意缓冲区的 InsertEnter / InsertLeave（pattern = "*"）。
-- 实现：用 augroup 包住，clear = true 保证重复加载配置时不会重复注册同一组回调。
vim.api.nvim_create_autocmd({ "InsertEnter", "InsertLeave" }, {
  group = vim.api.nvim_create_augroup("HighlightCursorLine", { clear = true }),
  pattern = "*",
  callback = function(ev)
    -- InsertLeave 时打开 cursorline；InsertEnter 时关闭
    vim.wo.cursorline = (ev.event == "InsertLeave")
  end,
})
