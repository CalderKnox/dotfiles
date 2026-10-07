--[[
  编辑器选项与 LazyVim 全局变量覆盖

  作用：只声明与 LazyVim 默认值不同的 vim.opt / vim.g，保持配置精简、意图清晰。
  加载时机：LazyVim 启动早期加载 options（早于 VeryLazy），因此此处设置会尽快生效，
            影响打开缓冲区后的编辑体验与部分 extras（LSP/格式化）的选型。
  原则：默认行为交给 LazyVim；本文件只放有意识的差异。
]]

-- 指定 Python LSP 使用 pyrefly（覆盖 LazyVim 默认的 pyright/basedpyright 等选型）。
-- 在打开 Python 相关缓冲区、LazyVim 装配 LSP 时生效。
vim.g.lazyvim_python_lsp = "pyrefly"

vim.opt.scrolloff = 8 -- 光标上下至少保留 8 行可视区域，滚动时不易贴边
vim.opt.colorcolumn = "120" -- 在第 120 列画参考线，提示行宽约束（不强制换行）
vim.opt.showmatch = true -- 输入闭合括号时短暂跳到匹配括号，辅助核对配对
vim.opt.modeline = false -- 禁用 modeline，避免不可信文件通过 modeline 改选项（安全）
