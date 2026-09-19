-- =============================================================================
-- keymaps.lua — 自定义键位 (chezmoi: lua/config/keymaps.lua)
-- =============================================================================
-- Description : 在 LazyVim 默认之后加载，可直接覆盖上游键位；全部带 desc 供
--               which-key 与 :map 查询，使用 vim.keymap.set（noremap+silent）。
-- Usage       : Leader 为 <Space>（LazyVim 默认）；按 <leader> 等待 which-key
-- Guards      : 无；键位定义幂等，重复加载覆盖同名映射
-- Author      : Payne
-- =============================================================================
-- 自定义键位在 LazyVim 默认*之后*加载，可在此覆盖 LazyVim。
-- 全部映射带 `desc`，供 which-key 与 `:map` 查询。使用 vim.keymap.set
-- （默认 noremap + silent）。

-- 插入模式: `jk` 快速 Esc —— 双手不必离开主键位区。
vim.keymap.set("i", "jk", "<ESC>", { desc = "用 jk 退出插入模式" })

-- 普通模式 —— leader 映射

-- 清除 hlsearch 高亮但不全局关闭 hlsearch。
-- 有意覆盖: 会遮蔽 LazyVim 默认的 <leader><space>
-- "Find Files (Root Dir)"（fzf-lua，已自动启用为 LazyVim 默认选择器）;
-- 用户键位在 VeryLazy 时更晚加载，故生效——与下方 <leader>bd 说明同属
-- 有文档记载的覆盖先例。
vim.keymap.set("n", "<leader><space>", "<cmd>nohlsearch<CR>", { desc = "清除搜索高亮" })

-- 分屏（经 leader 可发现;等价 <C-w>v / <C-w>s）。
vim.keymap.set("n", "<leader>sv", "<C-w>v", { desc = "垂直分屏" })
-- 有意覆盖: 遮蔽 fzf 默认选择器的 <leader>sh "Help Pages"
-- （与上方 <leader><space> 同属有文档记载的覆盖先例）。
vim.keymap.set("n", "<leader>sh", "<C-w>s", { desc = "水平分屏" })

-- 缓冲区: 不自定义 <leader>bd —— LazyVim 已内置 <leader>bd
-- （Snacks.bufdelete，保留窗口布局）与 <leader>bD（裸 :bd）。
-- 此前 <leader>bd 上的裸 `bdelete` 曾静默顶掉 Snacks 版本，
-- 而其注释却声称是补充。

-- 切换相对行号（结对编程或演示时有用）。
vim.keymap.set("n", "<leader>rl", "<cmd>set relativenumber!<CR>", { desc = "切换相对行号" })
