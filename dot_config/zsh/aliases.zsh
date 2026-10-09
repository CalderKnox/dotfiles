# =============================================================================
# aliases.zsh —— 通用别名与函数
# =============================================================================
# Description : 个人 zsh 别名/函数集合（系统应用、包管理更新、目录跳转、
#               Kubernetes、编辑器、AI 助手、开发构建等）
# Usage       : 由 ~/.zshrc source 加载；加载顺序必须为
#               aliases.zsh -> fzf.zsh -> sdk.zsh
#               aliases 必须最先：其导出的 $EDITOR 在 fzf.zsh 的 Ctrl-G 绑定
#               中于 source 时展开；sdk.zsh 最后因其 compdef 注册需 compinit
# Guards      : 本文件无外部命令强依赖；update-all 内逐项 command -v 守卫
# Depends     : lsd/bat/htop/fastfetch/yazi/nvim 等，完整清单见 README.md
# Author      : Payne
# =============================================================================

# =============================================================================
# 系统与应用
# =============================================================================
alias finder='open .'                            # Finder 打开当前目录
alias iterm_ghostty='open -a ghostty "$PWD"'     # Ghostty 打开当前目录（单引号保证运行时取 $PWD）
alias iterm='open -a iTerm "$PWD"'               # iTerm 打开当前目录

alias chezc='code ~/.local/share/chezmoi'        # 编辑 chezmoi 源目录 (~/.local/share/chezmoi)
alias chezs='chezmoi status'                     # 查看 chezmoi 状态
alias chezdf='chezmoi diff'                      # 预览 chezmoi 变更 (apply 前必跑)
alias chezap='chezmoi apply -v'                  # 应用 chezmoi 变更 (verbose)

# --- 编辑器快捷入口 (按 XDG 路径分组) ---
alias fishconfig='code ${HOME}/.config/fish'     # 编辑 fish 配置 (~/.config/fish)
alias zshconfig='code ~/.zshrc'                  # 编辑 ~/.zshrc
alias zshsource='source ~/.zshrc'                # 重新加载配置


# 启用终端代理 (127.0.0.1:5376, HTTP/HTTPS + SOCKS5)
onproxy() {
    local host="127.0.0.1" port=5376
    local http="http://$host:$port" socks="socks5h://$host:$port"
    export all_proxy="$socks" http_proxy="$http" https_proxy="$http" \
           ALL_PROXY="$socks" HTTP_PROXY="$http" HTTPS_PROXY="$http"
    # 回环豁免（与 fish 侧一致）：本机/localhost 流量不走代理，brew 本地镜像、
    # OrbStack docker、ssh ControlSocket 等本机服务不受代理干扰
    export no_proxy="localhost,127.0.0.1,::1" NO_PROXY="localhost,127.0.0.1,::1"
    printf "🚀 终端代理已开启：\n   HTTP/HTTPS: $http\n   SOCKS5: $socks"
}

# 关闭终端代理
ofproxy() {
    unset all_proxy http_proxy https_proxy ALL_PROXY HTTP_PROXY HTTPS_PROXY
    unset no_proxy NO_PROXY
    printf "⛵️ 终端代理已关闭。"
}

# =============================================================================
# 包管理器更新
# =============================================================================
# 一键全量更新（薄包装：可选 onproxy 后委托 update-all，无参即全量）
# 守卫：onproxy 仅在函数存在时调用；实际更新由 update-all 逐项 command -v 守卫
auto-update() {
    echo "🚀 开始更新 ..."
    (( $+functions[onproxy] )) && onproxy
    echo -e "\n"
    update-all
}

# =============================================================================
# Unix 命令增强
# =============================================================================

# ~~~ 目录跳转 ~~~
alias dl='cd ${HOME}/Downloads'
alias dt='cd ${HOME}/Desktop'
alias doc='cd ${HOME}/Documents'
alias wp='cd ${HOME}/WorkSpaces'
alias ws='cd ${HOME}/WisdomSpaces'

# ~~~ 系统信息 ~~~
alias ff='fastfetch'
alias nowdatetime='date "+%Y%m%d_%H%M%S"'
# macOS 各版本 date 对 %N 支持不一（旧版会输出字面 N），毫秒/微秒统一用 python3 保证可移植（与 zsh/fish 两侧保持一致）
alias timestamp_seconds='date +%s'
alias timestamp_millisecond='python3 -c "import time; print(int(time.time()*1000))"'
alias timestamp_microsecond='python3 -c "import time; print(int(time.time()*1000*1000))"'

# ~~~ 进程与资源 ~~~
alias top='htop'                                 # htop 替代 top
alias df='df -h'                                 # 人类可读的磁盘占用
alias du='du -h -d 2'                            # 目录占用统计（两层深）
alias ping='ping -c 5'                           # 默认只发 5 个探测包
alias pws='ps -p $$'                             # 查看当前 shell 进程

# ~~~ 终端复用 ~~~
alias tmux='tmux -2'                             # 强制 256 色

# ~~~ 基础命令 ~~~
# 注：原 chown/chmod/chgrp --preserve-root 别名已移除——GNU 专属标志在 macOS BSD
# 工具链上必然报 illegal option（历史版本即已损坏），需要时从 git 历史找回。
alias wget='wget -c'                             # 断点续传
# alias rm='rm -i'                                 # 删除前逐个确认
# alias cp='cp -i'                                 # 覆盖前确认
# alias mv='mv -i'                                 # 移动覆盖前确认
alias mkdir='mkdir -p -v'                        # 自动创建父目录并显示过程

# ~~~ 列表与导航 (lsd) ~~~
alias l='lsd --group-directories-first'          # 目录排在前面
alias ls='l'                                     # ls -> lsd
alias tree='lsd --tree --depth 3'                # 树状显示 3 层
alias cat='bat --paging=never'                   # bat 替代 cat（脚本中需要原生行为时用 command cat）

# =============================================================================
# Kubernetes (kubectl)
# 注意：短别名 k 定义在 sdk.zsh（k -> kubectl，含 kubecolor 包装），此处不再重复定义。
# =============================================================================
alias kk='kubectl krew'
alias kg='kubectl get'
alias kl='kubectl logs'
alias kd='kubectl describe'
alias kdel='kubectl delete'
alias ka='kubectl apply -f'

alias kgp='kubectl get pods -o wide'
alias kgn='kubectl get nodes -o wide'
alias kgs='kubectl get svc -o wide'
alias kgd='kubectl get deployment -o wide'

alias ksys='kubectl -n kube-system'

alias kctx='kubectl config current-context'
alias kctxs='kubectl config get-contexts'

alias format='biome format --write --files-max-size=10485760'
# =============================================================================
# 编辑器 (Neovim) —— EDITOR 契约
# =============================================================================
# 必须为环境变量（非 alias），供 git/crontab/fzf 的 Ctrl-G 绑定等子进程读取；
# fzf.zsh 的 ctrl-g:execute($EDITOR ...) 在 source 时展开，故本文件必须先于 fzf.zsh 加载。
# 守卫：已继承的 EDITOR/VISUAL（远端/launchd 注入）优先，缺省回落 nvim（与 fish 00_env.fish 一致）
[[ -n "${EDITOR:-}" ]] || export EDITOR='nvim'
[[ -n "${VISUAL:-}" ]] || export VISUAL='nvim'

alias v='nvim'
alias vi='nvim'
alias vim='nvim'
alias nv='nvim'
alias nvi='nvim'

# =============================================================================
# AI 助手 (Agent-Native)
# =============================================================================
alias cla='claude'
alias cla-unsafe='claude --dangerously-skip-permissions'
alias clp='opencode'
alias clp_cfg='code ${HOME}/.config/opencode'
alias cla_cfg='code ${HOME}/.claude'

# =============================================================================
# 开发与构建
# =============================================================================

# ~~~ 编译构建 ~~~
# 半核并行（与 fish 侧 functions/__half_cpu_count.fish 同语义）：nproc（coreutils）
# 缺失时回退 sysctl（macOS 原生）；探测失败/非数字时回退 1；下限 1。
__half_cpu_count() {
    local n
    if command -v nproc >/dev/null 2>&1; then
        n=$(nproc 2>/dev/null)
    else
        n=$(sysctl -n hw.ncpu 2>/dev/null)
    fi
    [[ "$n" == <-> ]] || n=2
    (( n < 2 )) && n=2
    print -- $(( n / 2 ))
}
makes() { make -j "$(__half_cpu_count)" "$@"; }
xargsp() { xargs -P "$(__half_cpu_count)" "$@"; }

# ~~~ Git 相关 ~~~
alias gopen='gh browse'                          # 浏览器打开当前仓库
alias lg='lazygit'

# ~~~ Python 工具 ~~~
ruff_auto() {
    # 自动修复 lint 并格式化；可传目标目录参数，默认当前目录
    local d="${1:-.}"
    ruff check --fix --exit-zero "$d" && ruff format "$d"
}

# 使用清华镜像安装 pip 包
alias pip_tsinghua_mirror='python3 -m pip install -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple'
# ⚠️ 破坏性操作：删除 HOME 下 .venv 与 uv.lock 后重建并同步
# 先检查 uv，且每一步失败即停止，避免依赖缺失或删除失败造成额外破坏。
# 注意：fish 侧同名函数目标为当前目录（conf.d/20_dev.fish），两侧行为不同，勿混用。
# 兼容在旧 alias 仍存在的 shell 中 reload（alias 会参与函数定义的解析）。
# unalias uv_resync 2>/dev/null || true
# uv_resync() {
#     if ! command -v uv >/dev/null 2>&1; then
#         print -u2 -- "uv not found; ${HOME}/.venv and ${HOME}/uv.lock left unchanged."
#         return 127
#     fi
#     command rm -rf -- "$HOME/.venv" "$HOME/uv.lock" || return $?
#     uv sync
# }

# =============================================================================
# Android 逆向工程
# =============================================================================
jdx() { nohup jadx-gui "$@" > /dev/null 2>&1 & } # 后台启动 jadx-gui 反编译工具
scr() { nohup scrcpy "$@" > /dev/null 2>&1 & }   # 后台启动 scrcpy 投屏
# 注：原 pkid / jeb 别名已移除——其指向的 jar 包与 JEB 目录已不存在，
# 需要时从 git 历史找回。

# =============================================================================
# 文件管理器 (yazi)
# =============================================================================

# yazi 包装：退出时自动 cd 到最后浏览的目录
# always 清理临时文件而不覆盖调用者的 traps；保留 yazi/cd 的失败状态。
y() {
    emulate -L zsh
    local tmp cwd rc=0
    tmp="$(command mktemp "${TMPDIR:-/tmp}/yazi-cwd.XXXXXX")" || return $?
    [[ -n "$tmp" ]] || return 1
    {
        command yazi "$@" --cwd-file="$tmp" || rc=$?
        if (( rc == 0 )); then
            IFS= read -r -d '' cwd < "$tmp"
            if [[ -n "$cwd" && "$cwd" != "$PWD" && -d "$cwd" ]]; then
                builtin cd -- "$cwd" || rc=$?
            fi
        fi
    } always {
        command rm -f -- "$tmp"
    }
    return "$rc"
}

# ---------------------------------------------------------------------------
# update-all —— 声明式批量更新（7 目标：brew/sdk/rustup/tldr/uv/mise/pi）
# 用法：update-all [targets...]  # 无参全量；有参按名过滤
# 守卫与非直观逻辑：
#   - tasks 为关联数组，声明式列出命令模板；targets 过滤时校验 Unknown target
#   - command -v $name 逐项守卫，未安装跳过（黄字 ⚠️）不计入 attempted
#   - 每目标 stderr 重定向到 mktemp 临时文件（模板需 XXXXXX 才适配 macOS mktemp）；
#     2>! 强制覆盖：Zim 设 NO_CLOBBER，普通 2> 会对 mktemp 已创建文件报 file exists
#   - 成功时透传 stderr 警告；失败时取末 5 行作摘要，累计 failed/attempted 计时
# ---------------------------------------------------------------------------
update-all() {
    local -A tasks=(
        brew  "brew update -f && brew upgrade -f --greedy-latest -y && brew cu -y -a && brew cleanup --prune=all"
        sdk   "sdk update && sdk upgrade && sdk selfupdate && sdk flush"
        rustup  "rustup update"
        tldr  "tldr --update"
        uv    "uv tool upgrade --all"
        mise  "mise upgrade"
        pi  "pi update --all"
    )

    local -a targets
    if (( $# > 0 )); then
        targets=("$@")
    else
        targets=(${(k)tasks})
    fi

    # 全量预检：未知目标不得在前面的目标已更新后才被发现。
    local name
    for name in "${targets[@]}"; do
        if [[ -z "${tasks[$name]}" ]]; then
            print -u2 -- "Unknown target: $name"
            print -u2 -- "Available: ${(kj:, :)tasks}"
            return 1
        fi
    done

    local failed=0
    local attempted=0          # 实际执行的目标数（not found 跳过的不计）
    local skipped=0
    local -a failed_names skipped_names
    local start_time=$(date +%s)

    for name in "${targets[@]}"; do
        print -P "%F{blue}═══ Updating $name ═══%f"

        if command -v $name >/dev/null 2>&1; then
            (( attempted++ ))
            local errfile
            if ! errfile="$(command mktemp "${TMPDIR:-/tmp}/update-all.${name}.XXXXXX")" || [[ -z "$errfile" ]]; then
                (( failed++ ))
                failed_names+=("$name")
                print -u2 -- "Cannot allocate stderr file for $name; update skipped."
                continue
            fi
            local rc=0
            eval "${tasks[$name]}" 2>! "$errfile" || rc=$?
            if (( rc == 0 )); then
                [[ -s "$errfile" ]] && command cat "$errfile" >&2
                print -P "%F{green}✓ $name done%f"
            else
                (( failed++ ))
                failed_names+=($name)
                print -P "%F{red}✗ $name failed (exit=${rc})%f"
                if [[ -s "$errfile" ]]; then
                    print -P "%F{red}── $name 错误摘要（stderr 末 5 行）──%f"
                    command tail -n 5 "$errfile" | command sed 's/^/  /'
                fi
            fi
            command rm -f -- "$errfile"
        else
            (( skipped++ ))
            skipped_names+=($name)
            print -P "%F{yellow}⚠️  $name not found, skipped%f"
        fi
        echo ""
    done

    local duration=$(( $(date +%s) - start_time ))
    local mins=$(( duration / 60 ))
    local secs=$(( duration % 60 ))

    if (( skipped > 0 )); then
        print -P "%F{yellow}ℹ️  skipped ${skipped} not-installed target(s): ${(j:, :)skipped_names}%f"
    fi
    if (( attempted == 0 )); then
        print -P "%F{yellow}⚠️  no runnable targets in ${mins}m${secs}s%f"
        return 0
    fi
    if (( failed == 0 )); then
        print -P "%B%F{green}✨ All ${attempted} target(s) updated in ${mins}m${secs}s%f%b"
    else
        print -P "%B%F{red}✗ ${failed}/${attempted} target(s) failed in ${mins}m${secs}s: ${(j:, :)failed_names}%f%b"
        return 1
    fi
}



bak() {
    emulate -L zsh
    zmodload zsh/datetime 2>/dev/null
    local ts
    if (( $+builtins[strftime] )); then
        strftime -s ts '%Y%m%d_%H%M%S' $EPOCHSECONDS
    else
        ts=$(date +%Y%m%d_%H%M%S)
    fi
    (( $# )) || { print -u2 "Usage: bak <file1> <file2> ..."; return 1 }
    local file base backup failed=0
    for file in "$@"; do
        if [[ ! -e $file ]]; then
            print -u2 -P "%F{red}Error: $file does not exist%f"
            failed=1
            continue
        fi
        base=${file:t}
        # 关键守卫：zsh 的 :r/:e 会把 .bashrc 拆成 ""+"bashrc"，不能用
        if [[ $base == ?*.* ]]; then
            backup="${file:h}/${base%.*}_${ts}.${base##*.}"
        else
            backup="${file:h}/${base}_${ts}"
        fi
        if [[ -e $backup ]]; then
            print -u2 -P "%F{yellow}Warning: $backup already exists, skipped%f"
            continue
        fi
        if command cp -f -- "$file" "$backup"; then
            print -r -- "Backed up: $file -> $backup"
        else
            failed=1
        fi
    done
    return "$failed"
}
