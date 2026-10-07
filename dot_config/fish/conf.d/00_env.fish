# =============================================================================
# 00_env.fish — Fish 环境变量与 PATH 收敛
# =============================================================================
# Description : Fish 启动时最早加载的 conf.d 配置（00_ 环境层）。
#               职责：PATH 收敛、locale/editor/homebrew 标志、
#               以及 Go 代理等语言工具环境。`__fish_env_loaded` 守卫避免重复
#               source 时重复注入 PATH。
#               （kubecolor 补全已迁至 completions/kubecolor.fish 按需加载）
# Usage       : 由 Fish 自动 source（conf.d 目录按字典序加载）；无需手动 source
# Guards      : fish_add_path 均带 -g（仅当前会话全局，不落 Universal Variables，
#               PATH 完全由仓库收敛，不污染 fish_variables）；本身幂等（去重）；
#               rustup 等路径带目录存在性 + contains 守卫
# Author      : Payne
# =============================================================================

if set -q __fish_env_loaded
    exit
end
set -g __fish_env_loaded

# ---------------------------------------------------------------------------
# PATH 基础收敛（幂等，去重）
# ---------------------------------------------------------------------------
# fish_add_path 已去重（-g 不落 universal）；按优先级前置，首项优先命中同名二进制。
fish_add_path -g /opt/homebrew/bin /opt/homebrew/sbin /usr/local/bin $HOME/.local/bin

# Homebrew 前缀兼容（Apple Silicon / Intel / Linux）：优先取已设 HOMEBREW_PREFIX，
# 否则回退 /opt/homebrew，保证后续 rustup 等路径推导不硬编码。
set -q HOMEBREW_PREFIX; or set -l HOMEBREW_PREFIX /opt/homebrew
set -l rustup_bin "$HOMEBREW_PREFIX/opt/rustup/bin"
if test -d "$rustup_bin"; and not contains "$rustup_bin" $PATH
    set -x PATH "$rustup_bin" $PATH
end

# ---------------------------------------------------------------------------
# Locale / Editor / Homebrew
# ---------------------------------------------------------------------------
set -q LANG; or set -gx LANG zh_CN.UTF-8   # 仅当未继承时设置（SSH/远端 locale 不被覆盖，与 zsh dot_zshrc 一致）

set -q EDITOR; or set -gx EDITOR nvim       # 已继承的 EDITOR 优先（同 zsh aliases.zsh 守卫）
set -q VISUAL; or set -gx VISUAL nvim

set -gx HOMEBREW_NO_AUTO_UPDATE 1      # 禁用自动更新提示（由 update-all 显式触发）
# HOMEBREW_NO_INSTALL_CLEANUP 是 presence-style 开关，连 0 也会禁用清理。
# 不设置它：保持 brew 默认，同时尊重调用者显式继承的 opt-out。
set -gx HOMEBREW_NO_ENV_HINTS 1         # 静默 hints

# ---------------------------------------------------------------------------
# 语言工具链（按需启用，已收敛为实际使用的 Go；其余保留为注释模板）
# ---------------------------------------------------------------------------
# 原则：仅对当前实际使用的 toolchain 暴露环境变量；空占位会污染文件且误导
# 新机器 — 已清理原 15 行空 clang/cpp/rust/zig/jvm/node/bun/deno/python 占位。
# 如需新增，按下方模板追加并带目录/命令存在性守卫：
#   type -q go; and set -gx GOPATH $HOME/.local/share/go; and fish_add_path -g $GOPATH/bin
test -d ~/.cargo/bin; and fish_add_path -g ~/.cargo/bin   # rust (cargo)
#   test -d /opt/homebrew/share/android-ndk; and set -gx ANDROID_NDK_HOME ...

# Go — GOPROXY 走国内镜像，GOPATH 统一为 ~/.local/share/go；bin 目录追加到 PATH
# 末尾（-a，与 zsh 侧 sdk.zsh 一致：go install 的二进制不应覆盖 Homebrew 同名工具；
# 目录不存在时 fish_add_path 自动跳过，去重免守卫）。
# 注意：GOROOT 由 mise 管理，此处不硬编码（历史的 mise GOROOT 行已移除，避免版本漂移）。
set -gx GOPROXY https://goproxy.cn,direct
set -gx GOPATH $HOME/.local/share/go
fish_add_path -ga $GOPATH/bin
