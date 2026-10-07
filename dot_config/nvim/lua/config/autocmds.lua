--[[
  自动命令（autocmd）配置

  作用：在特定事件发生时自动执行逻辑，扩展或覆盖 LazyVim 的默认行为。
  加载时机：LazyVim 在 VeryLazy 事件时自动加载本文件（启动后、插件就绪后），
            不会在 Neovim 最早期启动阶段执行。
  与默认的关系：LazyVim 自带一组 autocmd；此处只追加个人定制，不重复定义默认项。
  参考：https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/autocmds.lua
]]

-- 仅在 Normal 模式高亮。ModeChanged 覆盖不触发 InsertLeave 的 Ctrl-C，
-- 也覆盖 Replace、Visual 和 Ctrl-O 暂时离开/返回插入模式。
-- 使用实际模式，初始化与窗口切换时同步 window-local 选项；重复加载不累积回调。
local group = vim.api.nvim_create_augroup("HighlightCursorLine", { clear = true })
local function update_cursorline()
  vim.wo.cursorline = vim.fn.mode(1) == "n"
end
vim.api.nvim_create_autocmd("ModeChanged", {
  group = group,
  pattern = "*:*",
  callback = update_cursorline,
})
vim.api.nvim_create_autocmd("WinEnter", {
  group = group,
  callback = update_cursorline,
})
update_cursorline()
