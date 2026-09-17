-- ~/.config/nvim/lua/plugins/example.lua
-- Every file under lua/plugins/ is auto-loaded by lazy.nvim; returned tables are merged.
-- Active specs below DO take effect (template guard `if true then return {} end` is disabled).
-- Commented blocks are inert examples — uncomment to enable.
-- if true then return {} end

-- every spec file under the "plugins" directory will be loaded automatically by lazy.nvim
--
-- In your plugin files, you can:
-- * add extra plugins
-- * disable/enabled LazyVim plugins
-- * override the configuration of LazyVim plugins
--
-- For more information see: https://lazyvim.github.io/guide/return-a-plugin-return-func/
return {
    -- ============================================================================
    -- Example: Add Gruvbox colorscheme
    -- ============================================================================
    -- Add gruvbox colorscheme uncommenting the line below:
    -- { "ellisonleao/gruvbox.nvim" },

    -- Configure LazyVim's default colorscheme (catppuccin); gruvbox alternative kept commented above
    {
        "LazyVim/LazyVim",
        opts = {
            colorscheme = "catppuccin",
        },
    },

    -- ============================================================================
    -- Example: Configure Trouble (diagnostic window)
    -- ============================================================================
    -- Removed spec: { "folke/trouble.nvim", opts = { use_diagnostic_signs = true } }
    -- was a trouble v2-era option — v3 (lazy-lock bd67efe) has no such field and
    -- renders diagnostic icons via its own defaults, so the spec was a no-op.
    -- Disable Trouble entirely via the line below if not needed:
    -- { "folke/trouble.nvim", enabled = false },

    -- ============================================================================
    -- Example: Add nvim-cmp with emoji source
    -- ============================================================================
    -- Disabled (was inert dead config): LazyVim v14 ships blink.cmp as its
    -- completion engine and drops nvim-cmp specs unless the
    -- "lazyvim.plugins.extras.coding.nvim-cmp" extra is imported, so this spec
    -- never actually loaded (cmp-emoji is consequently absent from
    -- lazy-lock.json). To enable, import that extra first and run :Lazy sync
    -- so cmp-emoji gets pinned, then uncomment:
    -- {
    --     "hrsh7th/nvim-cmp",
    --     dependencies = { "hrsh7th/cmp-emoji" },
    --     ---@param opts cmp.ConfigSchema
    --     opts = function(_, opts)
    --         table.insert(opts.sources, { name = "emoji" })
    --     end,
    -- },

    -- ============================================================================
    -- Example: fzf-lua plugin file browser (default picker is fzf-lua)
    -- ============================================================================
    -- Add a keymap to browse plugin files
    {
        "ibhagwan/fzf-lua",
        keys = {
            -- Find plugin file with leader+fp
            {
                "<leader>fp",
                function() require("fzf-lua").files({ cwd = vim.fn.stdpath("data") .. "/lazy" }) end,
                desc = "Find Plugin File",
            },
        },
    },

    -- ============================================================================
    -- Example: Add tsserver with typescript.nvim
    -- ============================================================================
    -- Add tsserver and setup with typescript.nvim instead of lspconfig
    -- {
    --     "neovim/nvim-lspconfig",
    --     dependencies = {
    --         "jose-elias-alvarez/typescript.nvim",
    --         init = function()
    --             require("lazyvim.util").lsp.on_attach(function(_, buffer)
    --                 -- Organize imports
    --                 -- stylua: ignore
    --                 vim.keymap.set("n", "<leader>co", "TypescriptOrganizeImports",
    --                     { buffer = buffer, desc = "Organize Imports" })
    --                 -- Rename file
    --                 vim.keymap.set("n", "<leader>cR", "TypescriptRenameFile", { desc = "Rename File", buffer = buffer })
    --             end)
    --         end,
    --     },
    --     ---@class PluginLspOpts
    --     opts = {
    --         ---@type lspconfig.options
    --         servers = {
    --             -- tsserver will be automatically installed with mason and loaded with lspconfig
    --             tsserver = {},
    --         },
    --         -- You can do any additional lsp server setup here
    --         -- Return true if you don't want this server to be setup with lspconfig
    --         ---@type table<string, fun(server:string, opts:_.lspconfig.options):boolean?>
    --         setup = {
    --             -- Example to setup with typescript.nvim
    --             tsserver = function(_, opts)
    --                 require("typescript").setup({ server = opts })
    --                 return true
    --             end,
    --             -- Specify * to use this function as a fallback for any server
    --             -- ["*"] = function(server, opts) end,
    --         },
    --     },
    -- },

    -- Or use the LazyVim extra for typescript
    -- { import = "lazyvim.plugins.extras.lang.typescript" },

    -- ============================================================================
    -- Configure lualine with custom sections
    -- ============================================================================
    -- Add a custom component to lualine_x (right side)
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

    -- Or specify new options to override all the defaults
    -- Disabled: in lazy.nvim an opts function's return value replaces the
    -- merged opts, so returning {} here wipes LazyVim's entire lualine config
    -- (and the emoji component added above). Uncomment only together with a
    -- real config:
    -- {
    --     "nvim-lualine/lualine.nvim",
    --     event = "VeryLazy",
    --     opts = function()
    --         return {
    --             --[[add your custom lualine config here]]
    --         }
    --     end,
    -- },

    -- ============================================================================
    -- Use mini.starter instead of alpha
    -- ============================================================================
    -- Start screen alternative
    -- { import = "lazyvim.plugins.extras.ui.mini-starter" },

    -- ============================================================================
    -- JSON LSP/schema support comes from the lang.json extra (already imported in lua/config/lazy.lua)
    -- ============================================================================
    -- Setup treesitter for json, json5 and jsonc
    -- { import = "lazyvim.plugins.extras.lang.json" },

    -- ============================================================================
    -- Add tools you want to have installed
    -- ============================================================================
    -- Mason setup for LSP/dap/tools installers
    {
        "mason-org/mason.nvim",
        opts = {
            ensure_installed = { "shellcheck" }, -- Shell script checker
            -- "prettier",       -- JS formatter (enable if needed)
        },
    },

    -- ============================================================================
    -- Example: Debug adapter setup
    -- ============================================================================
    -- { import = "lazyvim.plugins.extras.dap.python" },

    -- ============================================================================
    -- Example: Add git commands navigation
    -- ============================================================================
    -- { import = "lazyvim.plugins.extras.ui.gitsigns" },
}
