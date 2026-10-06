# =============================================================================
# sdk.zsh —— 多语言 SDK 环境与补全配置
# =============================================================================
# Description : pnpm 补全、SDKMAN（惰性加载）、Android NDK、Python(uv/pip)、
#               Go、Rust(rustup)、Docker/Kubectl 补全缓存与 kubecolor 包装
# Usage       : 由 ~/.zshrc source 加载；必须在 compinit 之后、aliases.zsh 之后
#               且为三模块最后加载（内含 compdef 注册，需 compinit 已完成；
#               顺序即语义）
# Guards      : 单项工具均 command -v / 目录存在 + 去重守卫；SDKMAN 惰性桩；
#               补全缓存按可执行文件 stat 身份失效，锁内原子发布并 zcompile
# Loading-order contract: aliases.zsh -> fzf.zsh -> sdk.zsh (sdk last)
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
# SDKMAN 惰性加载：此处仅定义 sdk 占位函数，首次调用
# 时才 source sdkman-init.sh——其内部重定义 sdk 为真实实现并注入
# PATH/JAVA_HOME，后续调用即由真实实现接管。未安装 SDKMAN 时不定义任何内容。
# 注意：JAVA_HOME 与各 candidate 的 PATH 注入也随之延迟到首次 sdk 调用。
if [[ -s "$HOME/.sdkman/bin/sdkman-init.sh" ]] && (( ! $+functions[sdk] )); then
    sdk() {
        # 先移除占位桩：失败或初始化未定义 sdk 时不得递归调用自己。
        unfunction sdk
        source "$HOME/.sdkman/bin/sdkman-init.sh" || return $?
        if (( ! $+functions[sdk] )); then
            print -u2 -- "SDKMAN initialization did not define sdk."
            return 1
        fi
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
# 通用补全缓存加载器：首次调用真实二进制生成，之后启动复用源码/字节码。
# 路径 + stat 身份等值比较，兼容同路径降级及未来 mtime；不以缓存创建时间判断升级。
# 每工具的内建 flock 覆盖检查、生成、发布和 source，避免混用不同安装的源码/字节码。
# 最多等锁 1 秒；生成/校验失败保留旧文件但本次跳过，不阻塞启动或使用错误版本补全。
_ZSH_CACHE_DIR="${ZDOTDIR:-${HOME}}/.cache/zsh"
_load_cached_completion() {
    emulate -L zsh
    local tool="$1" bin_path cache_file cached_header header tmp_file lock_fd
    local -A executable_stat
    command -v compdef &>/dev/null || return 0
    # 解析真实二进制；不调用 kubecolor 包装函数或同名 alias。
    bin_path="$(whence -p "$tool" 2>/dev/null)"
    [[ -n "$bin_path" && -x "$bin_path" ]] || return 0
    bin_path="${bin_path:A}"
    zmodload zsh/stat && zmodload zsh/system || return 0
    cache_file="${_ZSH_CACHE_DIR}/${tool}-completion.zsh"
    [[ -d "$_ZSH_CACHE_DIR" ]] || command mkdir -p "$_ZSH_CACHE_DIR" || return 0
    # 稳定锁文件不能在解锁后删除：否则下一进程可能锁住不同 inode。
    : >> "${cache_file}.lock" || return 0
    zsystem flock -t 1 -i 0.02 -f lock_fd "${cache_file}.lock" 2>/dev/null || return 0
    {
        zstat -H executable_stat -- "$bin_path" 2>/dev/null || return 0
        header="# completion executable: ${(q)bin_path} ${executable_stat[device]}:${executable_stat[inode]}:${executable_stat[size]}:${executable_stat[mtime]}:${executable_stat[ctime]}"
        [[ -r "$cache_file" ]] && IFS= read -r cached_header < "$cache_file"
        if [[ ! -s "$cache_file" || "$cached_header" != "$header" ]]; then
            tmp_file="$(command mktemp "${cache_file}.XXXXXX")" || return 0
            [[ -n "$tmp_file" ]] || return 0
            if { print -r -- "$header"; "$bin_path" completion zsh; } >| "$tmp_file" 2>/dev/null &&
                [[ "$(<"$tmp_file")" != "$header" ]] && command zsh -dfn "$tmp_file" 2>/dev/null; then
                command rm -f -- "${cache_file}.zwc" && command mv -f -- "$tmp_file" "$cache_file" || return 0
                # .zwc 必须嵌入最终源码名，否则 rename 后 Zsh 会静默忽略字节码。
                # 锁覆盖发布；单独指定临时 output，仍以最终源码名编译。
                if zcompile -U "${tmp_file}.zwc" "$cache_file" 2>/dev/null; then
                    command mv -f -- "${tmp_file}.zwc" "${cache_file}.zwc"
                fi
            else
                return 0
            fi
        fi
        source "$cache_file"
    } always {
        [[ -n "$tmp_file" ]] && command rm -f -- "$tmp_file" "${tmp_file}.zwc"
        zsystem flock -u "$lock_fd"
    }
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
