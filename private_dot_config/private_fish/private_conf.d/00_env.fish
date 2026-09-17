# =============================================================================
# 00_env.fish — Fish 环境变量与 PATH 收敛
# =============================================================================
# Description : Fish 启动时最早加载的 conf.d 配置（00_ 前缀保证顺序）。
#               职责：PATH 收敛、locale/editor/homebrew 标志、kubecolor 包装、
#               以及 Go 代理等语言工具环境。`__fish_env_loaded` 守卫避免重复
#               source 时重复注入 PATH 或重复注册补全。
# Usage       : 由 Fish 自动 source（conf.d 目录按字典序加载）；无需手动 source
# Guards      : fish_add_path 本身幂等（去重）；rustup/go 等路径均带目录存在性
#               + contains 守卫；kubecolor 补全仅在 binary 存在时注册
# Author      : Payne
# =============================================================================

if set -q __fish_env_loaded
    exit
end
set -g __fish_env_loaded

# ---------------------------------------------------------------------------
# PATH 基础收敛（幂等，去重）
# ---------------------------------------------------------------------------
# fish_add_path 已去重；按优先级前置，首项优先命中同名二进制。
fish_add_path /opt/homebrew/bin /opt/homebrew/sbin /usr/local/bin $HOME/.local/bin

# Homebrew 前缀兼容（Apple Silicon / Intel / Linux）：优先取已设 HOMEBREW_PREFIX，
# 否则回退 /opt/homebrew，保证后续 rustup 等路径推导不硬编码。
set -q HOMEBREW_PREFIX; or set -l HOMEBREW_PREFIX /opt/homebrew
set -l rustup_bin "$HOMEBREW_PREFIX/opt/rustup/bin"
if test -d "$rustup_bin"; and not contains "$rustup_bin" $PATH
    set -x PATH "$rustup_bin" $PATH
end

# kubecolor → kubectl 彩色包装：仅在二进制存在时注册补全，避免无 kubectl 机器报错。
type -q kubecolor; and complete --command kubecolor --wraps kubectl

# ---------------------------------------------------------------------------
# Locale / Editor / Homebrew
# ---------------------------------------------------------------------------
set -gx LANG zh_CN.UTF-8

set -gx EDITOR nvim
set -gx VISUAL nvim

set -gx HOMEBREW_NO_AUTO_UPDATE 1      # 禁用自动更新提示（由 update-all 显式触发）
set -gx HOMEBREW_NO_INSTALL_CLEANUP 0  # 0 = 保留清理（brew 默认）；1 = 禁用
set -gx HOMEBREW_NO_ENV_HINTS 1         # 静默 hints

# ---------------------------------------------------------------------------
# 语言工具链（按需启用，已收敛为实际使用的 Go；其余保留为注释模板）
# ---------------------------------------------------------------------------
# 原则：仅对当前实际使用的 toolchain 暴露环境变量；空占位会污染文件且误导
# 新机器 — 已清理原 15 行空 clang/cpp/rust/zig/jvm/node/bun/deno/python 占位。
# 如需新增，按下方模板追加并带目录/命令存在性守卫：
#   type -q go; and set -gx GOPATH $HOME/go; and fish_add_path $GOPATH/bin
#   test -d ~/.cargo/bin; and fish_add_path ~/.cargo/bin   # rust (cargo)
#   test -d /opt/homebrew/share/android-ndk; and set -gx ANDROID_NDK_HOME ...

# Go — 仅当 GOPATH 存在或需默认时注入；GOPROXY 走国内镜像，GOPATH 统一为 ~/.local/share/go
# 注意：GOROOT 由 mise 管理，此处不硬编码（历史的 mise GOROOT 行已移除，避免版本漂移）。
set -gx GOPROXY https://goproxy.cn,direct
set -gx GOPATH $HOME/.local/share/go
if test -d "$GOPATH"; and not contains "$GOPATH/bin" $PATH
    fish_add_path $GOPATH/bin
end
