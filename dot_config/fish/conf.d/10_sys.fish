# =============================================================================
# 10_sys.fish — Fish 系统增强别名与通用入口
# =============================================================================
# Description : 系统导航与 Unix 增强别名 + 轻量交互函数（lsd/bat/htop 导航、
#               目录跳转、剪贴板、配置与 chezmoi 入口、时间戳、进程/端口查询）。
#               由原 conf.d/00_aliases.fish 拆分而来：k8s 别名在 21_k8s.fish；
#               可调用大函数（update-all/代理切换/y/serve/备份计时/磁盘分析等）
#               迁至 functions/ 惰性加载目录，首次调用时才 source。
# Usage       : 由 Fish 自动 source（conf.d 字典序，1x 为系统基础层，
#               顺序无关）；行为改变型别名（top/df/du/ping/tmux/wget/ls 系/
#               cat/rm/cp/mv/mkdir）仅在交互 shell 定义——对齐 zsh 侧 .zshrc
#               只在交互 shell 加载的语义，非交互 fish -c 脚本拿到原生命令。
# Guards      : 本文件无外部强依赖；别名未加 type -q 守卫，依赖缺失时
#               错误在调用时暴露（属预期）；与 zsh aliases.zsh 职责对齐。
# Author      : Payne
# =============================================================================

# ---------------------------------------------------------------------------
# chezmoi 入口
# ---------------------------------------------------------------------------
alias chezc='code ~/.local/share/chezmoi' # 编辑 chezmoi 源目录 (~/.local/share/chezmoi)
alias chezs='chezmoi status' # 查看 chezmoi 状态
alias chezdf='chezmoi diff' # 预览 chezmoi 变更 (apply 前必跑)
alias chezap='chezmoi apply -v' # 应用 chezmoi 变更 (verbose)

# ---------------------------------------------------------------------------
# 目录跳转与快速访问
# ---------------------------------------------------------------------------
# alias notes="open ~/Documents/notes"
# alias docs="open ~/Documents/docs"

alias dl="cd ~/Downloads"
alias dt="cd ~/Desktop"
alias doc="cd ~/Documents"
alias wp="cd ~/WorkSpaces"
alias ws="cd ~/WisdomSpaces"   # 命名与 zsh 侧统一（原 wi，已废弃）
alias finder="open ."

# 终端：Ghostty / iTerm 快速打开当前目录（单引号保证运行时取 $PWD，与 zsh 侧一致）
alias iterm_ghostty='open -a ghostty $PWD'
alias iterm='open -a iTerm $PWD'

# 编辑器快捷入口（XDG 路径）
alias fishconfig="code ~/.config/fish"
alias fishsource="exec fish"
alias zshconfig="code ~/.zshrc"

# 编辑器快捷入口（与 zsh 侧 aliases.zsh 对齐）
alias v="nvim"
alias vi="nvim"
alias vim="nvim"
alias nv="nvim"
alias nvi="nvim"
alias zshsource="source ~/.zshrc"

# ---------------------------------------------------------------------------
# 剪贴板
# ---------------------------------------------------------------------------
alias cbcopy="pbcopy"
alias cbpaste="pbpaste"

# ---------------------------------------------------------------------------
# 智能 cd / mkdir (自动 ls / cd)
# ---------------------------------------------------------------------------
function cdd --wraps='builtin cd' --description 'cd with automatic listing'
    builtin cd $argv; or return
    ls -la --group-directories-first 2>/dev/null
end

function mkcd --description 'Create directory and cd into it'
    mkdir -p $argv[1]; and builtin cd $argv[1]
end

# ---------------------------------------------------------------------------
# 进程与网络（磁盘分析/网络诊断/HTTP 服务器等大函数见 functions/ 惰性加载目录）
# ---------------------------------------------------------------------------
function psgrep --description 'Search processes by pattern'
    if test (count $argv) -eq 0
        echo "Usage: psgrep <pattern>"
        return 1
    end
    ps aux 2>/dev/null | grep -v grep | grep $argv[1]
end

function port --description 'Check what is using a port'
    if test (count $argv) -eq 0
        echo "Usage: port <port>"
        return 1
    end
    lsof -i :$argv[1] 2>/dev/null
end

function colortest --description 'Display 256 color palette'
    for i in (seq 0 255)
        printf "\x1b[38;5;%dmcolor %3d\x1b[0m " $i $i
        if test (math $i % 6) -eq 5
            echo
        end
    end
    echo
end

# ---------------------------------------------------------------------------
# 系统与环境 (Unix 增强)
# ---------------------------------------------------------------------------
alias ff="fastfetch"
alias nowdatetime='date "+%Y%m%d_%H%M%S"'
# macOS 各版本 date 对 %N 支持不一（旧版会输出字面 N），毫秒/微秒统一用 python3 保证可移植（与 zsh/fish 两侧保持一致）
# alias timestamp_seconds='date +%s%N | cut -c 1-10'
# alias timestamp_millisecond='date +%s%N | cut -c 1-13'
# alias timestamp_microsecond='date +%s%N | cut -c 1-16'
alias timestamp_seconds='date +%s'
alias timestamp_millisecond='python3 -c "import time; print(int(time.time()*1000))"'
alias timestamp_microsecond='python3 -c "import time; print(int(time.time()*1000*1000))"'

# 行为改变型别名仅交互 shell 定义（见文件头 Usage）：非交互脚本中 top/du/cat
# /cp/mv/mkdir 等保持原生语义，不被 lsd/bat/-i 等包装劫持（等价 zsh 侧
# .zshrc 只在交互 shell 加载的语义；cdd/mkcd 等显式函数调用不受影响）
if status is-interactive
    alias top='htop'
    alias df='df -h'
    alias du='du -h -d 2'   # 与 zsh 侧同 profile：人类可读 + 两层深度
    alias ping='ping -c 5'
    alias pws='ps -p $fish_pid'

    alias tmux="tmux -2"
    alias wget='wget -c'    # 断点续传（与 zsh 侧一致）

    alias l="lsd --group-directories-first"
    alias ls="l"
    alias lt="ls --tree"
    alias tree="lsd --tree --depth 3"
    alias cat='bat --paging=never'
    # alias rm='rm -i'   # 删除前逐个确认（与 zsh 侧 / cp/mv 护栏一致）
    # alias cp='cp -ir'
    # alias mv='mv -i'
    alias mkdir='mkdir -p -v'
end
# --preserve-root 别名已移除：BSD 的 chmod/chown/chgrp 不支持该选项
# （alias 展开为 command chmod --preserve-root 后每次调用都报 illegal option，
# 与 zsh aliases.zsh 侧同因移除；macOS 根分区本身 SIP 只读，无需此护栏）

# --- JSON helpers (按需启用，保留为模板) ---
# function json_format --description 'Format JSON'
#     if test (count $argv) -eq 0
#         cat /dev/stdin | python3 -m json.tool
#     else
#         cat $argv[1] | python3 -m json.tool
#     end
# end
