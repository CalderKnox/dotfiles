--[[
  自定义按键映射（keymaps）

  作用：定义个人快捷键，在 LazyVim 默认按键之上追加，不替换其核心映射表。
  加载时机：LazyVim 在 VeryLazy 事件时自动加载本文件，因此映射在启动稍晚、
            UI 与插件基本就绪后才生效；适合日常编辑用的快捷键。
  用法：用 vim.keymap.set 注册；模式、按键、动作按需填写。
  参考：https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
]]

-- 插入模式下连按 jk 退出到 Normal 模式。
-- 动机：减少伸手去 Esc 的次数；jk 在英文输入中较少连打，误触成本低。
-- 生效：仅 insert 模式（"i"）；每次按键序列匹配时触发。
vim.keymap.set("i", "jk", "<ESC>")
