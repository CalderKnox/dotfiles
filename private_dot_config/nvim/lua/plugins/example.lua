-- ~/.config/nvim/lua/plugins/example.lua
-- lua/plugins/ 下每个文件都会被 lazy.nvim 自动加载;返回的表会被合并。
-- 下方生效的 spec 确实起作用（模板守卫 `if true then return {} end` 处于注释状态）。
-- 注释块为不生效的示例——取消注释即可启用。
-- if true then return {} end

-- "plugins" 目录下每个 spec 文件都会被 lazy.nvim 自动加载
--
-- 在插件文件中，你可以:
-- * 追加额外插件
-- * 禁用/启用 LazyVim 插件
-- * 覆盖 LazyVim 插件的配置
--
-- 更多信息见: https://lazyvim.github.io/guide/return-a-plugin-return-func/
return {
    -- ============================================================================
    -- 示例: 添加 Gruvbox 配色
    -- ============================================================================
    -- 取消下面一行的注释即可添加 gruvbox 配色:
    -- { "ellisonleao/gruvbox.nvim" },

    -- 配置 LazyVim 默认配色（catppuccin）;gruvbox 备选保留在上方注释中
    {
        "LazyVim/LazyVim",
        opts = {
            colorscheme = "catppuccin",
        },
    },

    -- ============================================================================
    -- 示例: 配置 Trouble（诊断窗口）
    -- ============================================================================
    -- 已移除 spec: { "folke/trouble.nvim", opts = { use_diagnostic_signs = true } }
    -- 属 trouble v2 时代选项——v3（lazy-lock bd67efe）无此字段，
    -- 诊断图标经其自身默认值渲染，该 spec 是空操作。
    -- 如不需要，用下面一行整体禁用 Trouble:
    -- { "folke/trouble.nvim", enabled = false },

    -- ============================================================================
    -- 示例: 添加 nvim-cmp 与 emoji source
    -- ============================================================================
    -- 已禁用（原为不生效的死配置）: LazyVim v14 以 blink.cmp 为补全引擎，
    -- 且除非导入 "lazyvim.plugins.extras.coding.nvim-cmp" extra，
    -- 否则会丢弃 nvim-cmp spec，因此该 spec 从未真正加载
    -- （cmp-emoji 因此不在 lazy-lock.json 中）。要启用，先导入该 extra
    -- 并运行 :Lazy sync 使 cmp-emoji 入锁，再取消注释:
    -- {
    --     "hrsh7th/nvim-cmp",
    --     dependencies = { "hrsh7th/cmp-emoji" },
    --     ---@param opts cmp.ConfigSchema
    --     opts = function(_, opts)
    --         table.insert(opts.sources, { name = "emoji" })
    --     end,
    -- },

    -- ============================================================================
    -- 示例: fzf-lua 插件文件浏览器（默认选择器为 fzf-lua）
    -- ============================================================================
    -- 添加浏览插件文件的键位
    {
        "ibhagwan/fzf-lua",
        keys = {
            -- 用 leader+fp 查找插件文件
            {
                "<leader>fp",
                function() require("fzf-lua").files({ cwd = vim.fn.stdpath("data") .. "/lazy" }) end,
                desc = "查找插件文件",
            },
        },
    },

    -- ============================================================================
    -- 示例: 用 typescript.nvim 添加 tsserver
    -- ============================================================================
    -- 添加 tsserver 并用 typescript.nvim（而非 lspconfig）配置
    -- {
    --     "neovim/nvim-lspconfig",
    --     dependencies = {
    --         "jose-elias-alvarez/typescript.nvim",
    --         init = function()
    --             require("lazyvim.util").lsp.on_attach(function(_, buffer)
    --                 -- 整理导入
    --                 -- stylua: ignore
    --                 vim.keymap.set("n", "<leader>co", "TypescriptOrganizeImports",
    --                     { buffer = buffer, desc = "Organize Imports" })
    --                 -- 重命名文件
    --                 vim.keymap.set("n", "<leader>cR", "TypescriptRenameFile", { desc = "Rename File", buffer = buffer })
    --             end)
    --         end,
    --     },
    --     ---@class PluginLspOpts
    --     opts = {
    --         ---@type lspconfig.options
    --         servers = {
    --             -- tsserver 会随 mason 自动安装并经 lspconfig 加载
    --             tsserver = {},
    --         },
    --         -- 可在此做任何额外的 LSP server 配置
    --         -- 若不想让该 server 经 lspconfig 配置，返回 true
    --         ---@type table<string, fun(server:string, opts:_.lspconfig.options):boolean?>
    --         setup = {
    --             -- 示例: 用 typescript.nvim 配置
    --             tsserver = function(_, opts)
    --                 require("typescript").setup({ server = opts })
    --                 return true
    --             end,
    --             -- 指定 * 将此函数作为任意 server 的回退
    --             -- ["*"] = function(server, opts) end,
    --         },
    --     },
    -- },

    -- 或改用 LazyVim 的 typescript extra
    -- { import = "lazyvim.plugins.extras.lang.typescript" },

    -- ============================================================================
    -- 配置 lualine 自定义分区
    -- ============================================================================
    -- 向 lualine_x（右侧）追加自定义组件
    {
        "nvim-lualine/lualine.nvim",
        event = "VeryLazy",
        opts = function(_, opts)
            table.insert(opts.sections.lualine_x, {
                function()
                    return "😄"
                end,
            })
        end,
    },

    -- 或指定新选项覆盖全部默认值
    -- 已禁用: lazy.nvim 中 opts 函数的返回值会替换合并后的 opts，
    -- 此处返回 {} 会清空 LazyVim 的整个 lualine 配置
    -- （含上面添加的 emoji 组件）。仅与真实配置一起取消注释:
    -- {
    --     "nvim-lualine/lualine.nvim",
    --     event = "VeryLazy",
    --     opts = function()
    --         return {
    --             --[[在此添加自定义 lualine 配置]]
    --         }
    --     end,
    -- },

    -- ============================================================================
    -- 用 mini.starter 替代 alpha
    -- ============================================================================
    -- 启动屏备选
    -- { import = "lazyvim.plugins.extras.ui.mini-starter" },

    -- ============================================================================
    -- JSON LSP/schema 支持来自 lang.json extra（已在 lua/config/lazy.lua 导入）
    -- ============================================================================
    -- 为 json/json5/jsonc 配置 treesitter
    -- { import = "lazyvim.plugins.extras.lang.json" },

    -- ============================================================================
    -- 添加想要安装的工具
    -- ============================================================================
    -- LSP/dap/工具安装器的 mason 配置
    {
        "mason-org/mason.nvim",
        opts = {
            ensure_installed = { "shellcheck" }, -- Shell 脚本检查器
            -- "prettier",       -- JS 格式化器（需要时启用）
        },
    },

    -- ============================================================================
    -- 示例: 调试适配器配置
    -- ============================================================================
    -- { import = "lazyvim.plugins.extras.dap.python" },

    -- ============================================================================
    -- 示例: 添加 git 命令导航
    -- ============================================================================
    -- { import = "lazyvim.plugins.extras.ui.gitsigns" },
}
