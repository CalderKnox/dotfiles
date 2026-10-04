--[[
  Mason 工具链保证安装列表

  作用：扩展 mason.nvim 的 ensure_installed，让常用 CLI 工具在首次进入相关功能时
        （或 Mason 同步时）自动装好，减少手动 :MasonInstall。
  加载时机：lazy 导入 lua/plugins/ 后与 LazyVim 自带的 mason 规格合并 opts；
            实际下载发生在 Mason 安装/确保流程中，非每次按键。
  影响范围：仅列出的工具；不改变 LSP 服务器列表（那些多由语言 extras 管理）。

  注意：名称必须是 mason-registry 中存在的包。不存在的包会让 LazyVim 的
        mr.get_package() 抛错，整段 mason config 失败，后续 ensure/自动安装全部中断。

  已由 LazyVim / extras 覆盖、故不在此重复：
  - stylua / shfmt（LazyVim core mason ensure）
  - shellcheck / bashls（util.dot extra）
]]

return {
  {
    "mason-org/mason.nvim",
    opts = {
      ensure_installed = {
        -- Lua
        "luacheck", -- Lua 静态检查（core 只保 stylua）
        -- Python
        "ruff", -- Python 静态检查
        "pyrefly", -- Python 类型检查（备用；LSP 选型见 lazyvim_python_lsp）
        "debugpy", -- Python DAP（提供 debugpy-adapter，供 nvim-dap-python 使用）
        -- JavaScript / TypeScript / JSON / YAML
        "biome",
        "typescript-language-server", -- TypeScript 语言服务器
        "json-lsp", -- JSON/JSONC 语言服务器（LazyVim lang.json 使用 jsonls）
        "yaml-language-server", -- YAML 语言服务器
        "yamlfmt", -- YAML 格式化
        "yamllint", -- YAML 静态检查
        -- Golang
        "golangci-lint", -- Golang 静态检查
        "gopls", -- Golang 语言服务器
        "delve", -- Golang 调试器
        "goimports", -- Golang 导入排序
        "gofumpt", -- Golang 格式化
        "gomodifytags", -- Golang 修改标签
        "impl", -- Golang 实现接口
        -- Rust（rustfmt 不在 mason registry，用 rustup component）
        "rust-analyzer", -- Rust 语言服务器
        "codelldb", -- Rust 调试器
      },
    },
  },
}
