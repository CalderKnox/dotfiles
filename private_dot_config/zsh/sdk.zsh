# =============================================================================
# sdk.zsh —— 多语言 SDK 环境与补全配置
# =============================================================================
# Description : pnpm 补全、SDKMAN（惰性加载）、Android NDK、Python(uv/pip)、
#               Go、Rust(rustup)、Docker/Kubectl 补全缓存与 kubecolor 包装
# Usage       : 由 ~/.zshrc source 加载；必须在 compinit 之后、aliases.zsh 之后
#               且为三模块最后加载（内含 compdef 注册，需 compinit 已完成；
#               顺序即语义）
# Guards      : 单项工具均 command -v / 目录存在 + 去重守卫；SDKMAN 惰性桩；
#               补全缓存按二进制 mtime 失效并 zcompile
# 加载顺序契约: aliases.zsh -> fzf.zsh -> sdk.zsh（sdk 最后）
# Author      : Payne
# =============================================================================

########## pnpm ##########
# pnpm 补全（tabtab 模板）：函数名必须为 _pnpm_completion，且 compdef 注册到 pnpm
# （compdef 守卫：Zim 引导失败时 compinit 未跑、compdef 未定义，静默跳过不报错）
if command -v pnpm &>/dev/null && command -v compdef &>/dev/null; then
    _pnpm_completion () {
        local reply
        local si=$IFS
        IFS=$'\n' reply=($(COMP_CWORD="$((CURRENT-1))" COMP_LINE="$BUFFER" COMP_POINT="$CURSOR" SHELL=zsh pnpm completion-server -- "${words[@]}"))
        IFS=$si
        if [ "$reply" = "__tabtab_complete_files__" ]; then
            _files
        else
            _describe 'values' reply
        fi
    }
    compdef _pnpm_completion pnpm
fi

########## Java / SDKMAN ##########
# SDKMAN 惰性加载（省约 45ms 启动耗时）：此处仅定义 sdk 占位函数，首次调用
# 时才 source sdkman-init.sh——其内部重定义 sdk 为真实实现并注入
# PATH/JAVA_HOME，后续调用即由真实实现接管。未安装 SDKMAN 时不定义任何内容。
# 注意：JAVA_HOME 与各 candidate 的 PATH 注入也随之延迟到首次 sdk 调用。
if [[ -s "$HOME/.sdkman/bin/sdkman-init.sh" ]]; then
    sdk() {
        source "$HOME/.sdkman/bin/sdkman-init.sh"
        sdk "$@"
    }
fi

########## Android ##########
# NDK 由 Homebrew cask 安装；目录存在时才导出，避免悬空变量
[[ -d "/opt/homebrew/share/android-ndk" ]] && export ANDROID_NDK_HOME="/opt/homebrew/share/android-ndk"

########## Python ##########
# Python 环境由 uv 管理；conda 已卸载，相关 init 已移除（见 git 历史）
# 如需切换 PyPI 镜像可启用：
# export UV_DEFAULT_INDEX="https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple"

########## Golang ##########
export GOPROXY='https://goproxy.cn,direct'           # 国内模块代理
# GOPATH 统一为 ~/.local/share/go（与 fish 00_env.fish 完全一致；XDG 风格，
# 曾用 ~/WorkSpaces/project/go 与 fish 侧冲突为两个不同的工作区）
export GOPATH="${HOME}/.local/share/go"
export GOBIN="${GOPATH}/bin"
# PATH 收敛：仅当 GOBIN 实际存在且尚未在 PATH 时加入，避免死路径与重复累积
# 去重守卫使用冒号定界（":$PATH:"），与 dot_zshrc / krew 处的双守卫惯例一致
[[ -d "$GOBIN" && ":$PATH:" != *":$GOBIN:"* ]] && export PATH="$PATH:${GOBIN}"

########## Rust ##########
# rustup 环境（brew 安装的 rustup 无此文件时静默跳过）
source "$HOME/.cargo/env" 2>/dev/null

########## Container ##########
# 通用补全缓存加载器：kubectl/docker 的补全脚本需拉起子进程生成（各 ~10ms 级），
# 首次生成后缓存到 ${ZDOTDIR:-~}/.cache/zsh/ 并 zcompile，之后启动直接 source 缓存
# （zsh 自动优先加载不早于源文件的 .zwc 字节码）。
# 失效策略：工具二进制比缓存新（升级）时自动重建；生成失败则回退为本次跳过。
_ZSH_CACHE_DIR="${ZDOTDIR:-${HOME}}/.cache/zsh"
_load_cached_completion() {
    # $1: 工具名，补全生成命令固定为 "$1 completion zsh"
    # 前置守卫：工具不存在，或 compdef 未定义（Zim 引导失败的弱网场景）时静默跳过
    local tool="$1" bin_path cache_file
    command -v "$tool" &>/dev/null && command -v compdef &>/dev/null || return 0
    # 用 whence -p 只解析二进制路径（command -v 会命中同名函数/别名，如 kubectl 包装函数）
    bin_path="$(whence -p "$tool" 2>/dev/null)"
    cache_file="${_ZSH_CACHE_DIR}/${tool}-completion.zsh"

    if [[ ! -s "$cache_file" || ( -n "$bin_path" && "$bin_path" -nt "$cache_file" ) ]]; then
        command mkdir -p "$_ZSH_CACHE_DIR"
        if ! "$tool" completion zsh > "$cache_file" 2>/dev/null; then
            command rm -f -- "$cache_file"
            return 0
        fi
    fi
    if [[ ! -s "${cache_file}.zwc" || "$cache_file" -nt "${cache_file}.zwc" ]]; then
        zcompile "$cache_file" 2>/dev/null
    fi
    source "$cache_file"
}

# Docker 补全（未安装 docker CLI 时跳过；子进程生成结果走缓存）
if (( $+commands[docker] )); then
    _load_cached_completion docker
fi

# ==================== kubectl / kubecolor ====================
# 1. kubectl 存在时加载其补全（子进程生成结果走缓存，见上方 _load_cached_completion）
if command -v kubectl &> /dev/null; then
    _load_cached_completion kubectl
fi

# 2. 主命令：优先使用 kubecolor 彩色输出，否则保留原生 kubectl
if command -v kubecolor &> /dev/null; then
    kubectl() { kubecolor "$@"; }
    command -v compdef &>/dev/null && compdef kubecolor=kubectl
fi

# 3. 短别名 k -> kubectl（仅在 kubectl 可用时定义；补全一并关联。
#    注意：本别名会覆盖 aliases.zsh 中可能存在的同名定义——这是有意设计）
if command -v kubectl &> /dev/null; then
    alias k='kubectl'
    command -v compdef &>/dev/null && compdef k=kubectl
fi

# 4. krew 二进制目录：同样目录存在 + 去重双守卫（冒号定界，与 GOBIN/dot_zshrc
#    惯例一致；原裸子串匹配对同级路径名可能误判）
[[ -d "${KREW_ROOT:-$HOME/.krew}/bin" && ":$PATH:" != *":${KREW_ROOT:-$HOME/.krew}/bin:"* ]] && \
    export PATH="${KREW_ROOT:-$HOME/.krew}/bin:$PATH"
