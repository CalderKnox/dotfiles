-- =============================================================================
-- autocmds.lua — 自定义自动命令 (chezmoi: lua/config/autocmds.lua)
-- =============================================================================
-- Description : 在 VeryLazy 事件后加载，仅追加用户覆盖；LazyVim 已定义部分
--               autocmd，此文件仅增量。上游已接管 format-on-save，此处不重复。
-- Usage       : 每个 autocmd 使用独立 augroup + { clear = true }，重载不重叠
-- Guards      : 事件均幂等；TextYankPost/VimResized 上游 v16 已覆盖，不重复定义
-- Author      : Payne
-- =============================================================================
-- 自定义自动命令在 VeryLazy 事件（LazyVim 默认之后）加载。
-- LazyVim 已定义自己的 autocmd，本文件仅追加用户覆盖。
-- 上游 v16 已覆盖 TextYankPost（on_yank 高亮，默认 IncSearch）与
-- VimResized（`tabdo wincmd =` 并恢复当前标签页），故此处不再重复定义。
-- 每个 autocmd 使用独立 augroup + { clear = true }，重载配置不会重复注册。

-- 仅普通模式显示 cursorline;输入时隐藏。
-- LazyVim 默认启用 cursorline;本项在 InsertEnter 时关闭。
vim.api.nvim_create_autocmd({ "InsertEnter", "InsertLeave" }, {
  group = vim.api.nvim_create_augroup("user_cursorline_toggle", { clear = true }),
  desc = "插入模式隐藏 cursorline，普通模式恢复",
  callback = function(ev)
    vim.opt.cursorline = ev.event == "InsertLeave"
  end,
})

-- 注意: Python 缩进（tabstop=4 / shiftwidth=4 / expandtab）已在
-- lua/config/options.lua 全局设置，对所有文件类型生效。
-- 为 `python` 单设 FileType autocmd 属冗余，除非需要按文件类型覆盖
-- （如不同宽度）。仅当偏离全局默认时才在此添加。
