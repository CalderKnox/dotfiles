-- =============================================================================
-- options.lua — 全局编辑器选项 (chezmoi: lua/config/options.lua)
-- =============================================================================
-- Description : 增量覆盖 LazyVim 默认的全局 vim.opt（与上游相同的项一律不写）。
--               分组：缩进宽度、显示滚动、搜索锚点与标尺；剪贴板/补全
--               刻意不覆盖（上游默认更优，见下方说明）。
-- Usage       : 在 LazyVim defaults 之后加载，值在此覆盖同名项；`:h <option>`
-- Guards      : 无外部依赖；所有选项幂等，重复加载安全
-- Author      : Payne
-- =============================================================================
-- 全局编辑器选项。在 LazyVim 默认值*之后*加载，重叠项以本文件为准。
-- 详见 `:h <option>`。此处只写覆盖与新增项，其余交给 LazyVim。

-- 剪贴板 / 补全: 刻意不覆盖。LazyVim 默认值比这里的静态值更智能:
--   clipboard   —— 上游具备 SSH 感知（存在 SSH_CONNECTION 时为空，从而启用
--                  OSC52 provider）;裸写 `unnamedplus` 会破坏远程会话，
--                  故已从本文件移除。
--   completeopt —— 上游默认恰为 `menu,menuone,noselect`;此前的重复覆盖
--                  （误标为自定义项）已删除。

-- 缩进宽度: 4 空格（LazyVim 默认 2）。expandtab/smartindent 与上游一致，
-- 不再重设;若某语言需要不同宽度，可在 autocmds.lua 中按文件类型覆盖。
vim.opt.tabstop = 4 -- <Tab> 的显示宽度
vim.opt.shiftwidth = 4 -- >> / << 与自动缩进的步长

-- 显示与滚动
vim.opt.scrolloff = 8 -- 滚动时在光标上下保留 8 行上下文（上游: 4）
vim.opt.colorcolumn = "100" -- 100 列标线，作行长参考

-- 搜索: hlsearch/incsearch 为 Neovim 默认值，此处不重设;
-- 用 <leader><space> 清除高亮（见 keymaps.lua）。下方 showmatch 是真正的
-- 覆盖项（Vim 默认: 关闭）。
vim.opt.showmatch = true -- 光标落在括号上时短暂跳到匹配括号
