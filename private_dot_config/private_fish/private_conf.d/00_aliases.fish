# =============================================================================
# 00_aliases.fish — Fish 通用别名与函数
# =============================================================================
# Description : Fish 交互别名/函数集合（系统导航、进程/文件、网络、代理、
#               yazi 包装、并行构建、批量更新等）。与 zsh aliases.zsh 职责
#               对齐，适配 Fish 语法（fish_add_path、type -q 守卫、set -gx）。
# Usage       : 由 Fish 自动 source（conf.d 按字典序）；00_ 前缀保证在
#               01_* 之前加载。函数均带 --description / --wraps 供
#               `functions` 与 `type` 查询；别名与函数不依赖外部强依赖。
# Guards      : PROXY 端口统一 5376（与 dot_gitconfig / ssh config 一致）；
#               update-all 内逐项 type -q / command -q 守卫；y() 带 tmp
#               清理；find-large / serve 参数回退默认值幂等。
# Author      : Payne
# =============================================================================

alias chezc='code ~/.local/share/chezmoi'        # 编辑 chezmoi 源目录 (~/.local/share/chezmoi)
alias chezs='chezmoi status'                     # 查看 chezmoi 状态
alias chezdf='chezmoi diff'                      # 预览 chezmoi 变更 (apply 前必跑)
alias chezap='chezmoi apply -v'                  # 应用 chezmoi 变更 (verbose)

# ---------------------------------------------------------------------------
# Kubernetes / 容器 (与 zsh sdk.zsh 的 k→kubectl 一致，fish 侧别名形态)
# ---------------------------------------------------------------------------
alias k="kubecolor"
alias kk="k krew"
alias kg="kubectl get"
alias kl="kubectl logs"
alias kd="kubectl describe"

# ---------------------------------------------------------------------------
# 笔记与快速访问
# ---------------------------------------------------------------------------
# alias notes="open ~/Documents/notes"
# alias docs="open ~/Documents/docs"

alias dl="cd ~/Downloads"
alias dt="cd ~/Desktop"
alias doc="cd ~/Documents"
alias wp="cd ~/WorkSpaces"
alias wi="cd ~/WisdomSpaces"
alias finder="open ."

# 终端：Ghostty / iTerm 快速打开当前目录（单引号保证运行时取 $PWD，与 zsh 侧一致）
alias iterm_ghostty='open -a ghostty $PWD'
alias iterm='open -a iTerm $PWD'

# 编辑器快捷入口（XDG 路径）
alias fishconfig="code ~/.config/fish"
alias fishsource="exec fish"
alias zshconfig="code ~/.zshrc"
alias zshsource="source ~/.zshrc"

# ---------------------------------------------------------------------------
# 剪贴板
# ---------------------------------------------------------------------------
alias cbcopy="pbcopy"
alias cbpaste="pbpaste"

# ---------------------------------------------------------------------------
# 智能 cd / mkdir (自动 ls / cd)
# ---------------------------------------------------------------------------
function cdd --wraps='builtin cd' --description 'cd 后自动列目录'
    builtin cd $argv
    ls -la --group-directories-first 2>/dev/null
end

function mkcd --description '创建目录并进入'
    mkdir -p $argv[1]; and builtin cd $argv[1]
end

# ---------------------------------------------------------------------------
# 文件与磁盘
# ---------------------------------------------------------------------------
# 查找大文件（按字节阈值，默认 100M；接受 100M / 500M / 1G 等）
# 用法: find-large [size]  e.g. find-large 500M
function find-large --description '按大小查找大文件（默认 100M）'
    set -l size_limit 100M
    if test (count $argv) -gt 0
        set size_limit $argv[1]
    end
    # +size_limit 为 find 语法（-size +100M）；结果按大小可读输出
    find . -type f -size +$size_limit -exec ls -lh {} \; 2>/dev/null | awk '{ print $9 ": " $5 }' | sort -k2hr
end

function dus --description '磁盘占用汇总（排序）'
    du -sh */ 2>/dev/null | sort -hr
end

function filestats --description '统计当前目录的文件类型'
    find . -type f 2>/dev/null | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -20
end

function recent --description '显示最近修改的文件（默认 10 个）'
    set -l count 10
    if test (count $argv) -gt 0
        set count $argv[1]
    end
    ls -lt 2>/dev/null | head -n (math $count + 1)
end

function tree-size --description '可视化目录大小'
    # command 绕开本文件 du='du -kh' 别名；-d 1 为 BSD/GNU 通用的深度写法
    # （原 --max-depth=1 仅 GNU du 支持，BSD 下静默失败输出为空）
    command du -h -d 1 2>/dev/null | sort -hr | head -20
end

# ---------------------------------------------------------------------------
# 进程与网络
# ---------------------------------------------------------------------------
function psgrep --description '按模式搜索进程'
    if test (count $argv) -eq 0
        echo "Usage: psgrep <pattern>"
        return 1
    end
    ps aux 2>/dev/null | grep -v grep | grep $argv[1]
end

function port --description '查看端口占用'
    if test (count $argv) -eq 0
        echo "Usage: port <port>"
        return 1
    end
    lsof -i :$argv[1] 2>/dev/null
end

function colortest --description '显示 256 色调色板'
    for i in (seq 0 255)
        printf "\x1b[38;5;%dmcolor %3d\x1b[0m " $i $i
        if test (math $i % 6) -eq 5
            echo
        end
    end
    echo
end

function netcheck --description '快速网络诊断'
    echo (set_color cyan)"🌐 External IP:"(set_color normal)
    curl -s icanhazip.com; echo

    echo (set_color cyan)"📡 DNS Test:"(set_color normal)
    dig google.com +short 2>/dev/null | head -1; echo

    echo (set_color cyan)"⚡ Speed Test (Download):"(set_color normal)
    curl -s https://raw.githubusercontent.com/sivel/speedtest-cli/master/speedtest.py | python3 - --simple 2>/dev/null | head -1
end

# ---------------------------------------------------------------------------
# 快速 HTTP 服务器
# ---------------------------------------------------------------------------
# 用法: serve [port]  默认 8000
function serve --description '启动简易 HTTP 服务器（默认 8000）'
    set -l port 8000
    if test (count $argv) -gt 0
        set port $argv[1]
    end
    echo (set_color green)"🚀 Server running at http://localhost:$port"(set_color normal)
    python3 -m http.server $port
end

# --- JSON helpers (按需启用，保留为模板) ---
# function json_format --description 'Format JSON'
#     if test (count $argv) -eq 0
#         cat /dev/stdin | python3 -m json.tool
#     else
#         cat $argv[1] | python3 -m json.tool
#     end
# end

# ---------------------------------------------------------------------------
# 代理切换 (与 dot_gitconfig / ssh config 同端口 5376, 统一为 5376)
# ---------------------------------------------------------------------------
function onproxy --description "启用终端代理 (127.0.0.1:5376, socks5/http)"
    set -l proxy_host "127.0.0.1"
    set -l proxy_port 5376
    set -l proxy_url "http://$proxy_host:$proxy_port"
    set -l socks_url "socks5h://$proxy_host:$proxy_port"

    set -gx all_proxy "$socks_url"
    set -gx http_proxy "$proxy_url"
    set -gx https_proxy "$proxy_url"
    set -gx ALL_PROXY "$socks_url"
    set -gx HTTP_PROXY "$proxy_url"
    set -gx HTTPS_PROXY "$proxy_url"

    echo -e "🚀 终端代理已开启："
    echo -e "   HTTP/HTTPS: $proxy_url"
    echo -e "   SOCKS5: $socks_url"
end

function ofproxy --description "关闭终端代理"
    set -e all_proxy; set -e http_proxy; set -e https_proxy
    set -e ALL_PROXY; set -e HTTP_PROXY; set -e HTTPS_PROXY
    echo -e "⛵️ 终端代理已关闭。"
end

# ---------------------------------------------------------------------------
# update-all — 声明式批量更新 (fish 版; 默认清单与 zsh 有意不同, 非对齐关系)
# 用法: update-all [targets...]  无参全量；有参按名过滤
#       auto-update = onproxy + update-all（先开代理再全量更新）
# 任务: brew / rust / tldr / uv / mise / pi (fish 侧含 pi 更新)
#       fish 侧不支持 sdk 目标（sdkman 插件已移除，与 zsh 的能力差异属有意决定）
# 守卫: type -q / command -q 逐项守卫，未装跳过；失败计数与耗时统计
# ---------------------------------------------------------------------------
function auto-update --description "一键更新所有开发环境 (fish 版)"
    onproxy
    update-all
end

function update-all --description "一键更新所有开发环境 (fish 版)"
    # 默认清单与 zsh 有意不同：fish 含 pi 不含 sdk（sdkman 插件已移除，
    # 与 zsh 的能力差异属有意决定）；目标名 rust 对应 zsh 侧的 rustup
    set -l tasks brew rust tldr uv mise pi

    set -l targets
    if test (count $argv) -eq 0
        set targets $tasks
    else
        set targets $argv
    end

    set -l failed 0
    set -l start_time (date +%s)

    for name in $targets
        echo (set_color --bold blue)"═══ Updating $name ═══"(set_color normal)

        switch $name
            case brew
                if type -q brew
                    brew update -f && brew upgrade -f --greedy-latest -y && brew cu -y -a && brew cleanup --prune=all
                    or set failed (math $failed + 1)
                else
                    echo (set_color yellow)"⚠️  brew not found, skipped"(set_color normal)
                end


            case rust
                if type -q rustup
                    rustup update
                    or set failed (math $failed + 1)
                else
                    echo (set_color yellow)"⚠️  rustup not found, skipped"(set_color normal)
                end

            case tldr
                if type -q tldr
                    tldr --update
                    or set failed (math $failed + 1)
                else
                    echo (set_color yellow)"⚠️  tldr not found, skipped"(set_color normal)
                end

            case uv
                if type -q uv
                    uv tool upgrade --all
                    or set failed (math $failed + 1)
                else
                    echo (set_color yellow)"⚠️  uv not found, skipped"(set_color normal)
                end

            case mise
                if type -q mise
                    mise upgrade
                    or set failed (math $failed + 1)
                else
                    echo (set_color yellow)"⚠️  mise not found, skipped"(set_color normal)
                end

            case pi
                if type -q pi
                    pi update --all 2>/dev/null
                    or set failed (math $failed + 1)
                else
                    echo (set_color yellow)"⚠️  pi not found, skipped"(set_color normal)
                end

            case '*'
                echo (set_color red)"❌ Unknown target: $name"(set_color normal)
                echo "Available: "(string join ", " $tasks)
                return 1
        end
        echo ""
    end

    set -l duration (math (date +%s) - $start_time)
    set -l mins (math -s0 "$duration / 60")
    set -l secs (math -s0 "$duration % 60")

    if test $failed -eq 0
        # 耗时拼接需引号分断：fish 双引号内 {$mins} 的花括号按字面输出，${mins} 为语法错误
        echo (set_color --bold green)"✨ All updates completed in "$mins"m"$secs"s"(set_color normal)
    else
        echo (set_color --bold red)"⚠️  $failed update(s) failed, completed in "$mins"m"$secs"s"(set_color normal)
        return 1
    end
end

# ---------------------------------------------------------------------------
# yazi 包装：退出时自动 cd 到最后浏览的目录
# ---------------------------------------------------------------------------
function y --description 'yazi 包装: 退出时 cd 到最后浏览目录'
    set -l tmp (mktemp -t "yazi-cwd.XXXXXX")
    command yazi $argv --cwd-file="$tmp"
    # 读取 yazi 写入的 cwd（null 分隔或换行）；fish 的 read -z 读 NUL 分隔
    if read -z cwd < "$tmp"; and test "$cwd" != "$PWD"; and test -d "$cwd"
        builtin cd -- "$cwd"
    end
    rm -f -- "$tmp"
end

# ---------------------------------------------------------------------------
# 并行构建 helpers (半核并行, 与 zsh 的 makes/xargsp 一致)
# ---------------------------------------------------------------------------
function __half_cpu_count --description "返回可用 CPU 数的一半，最小为 1"
    set -l cpu_count 1
    if type -q nproc
        set cpu_count (nproc)
    else if type -q sysctl
        set cpu_count (sysctl -n hw.ncpu 2>/dev/null)
    end
    if not string match -qr '^[0-9]+$' -- $cpu_count
        set cpu_count 1
    end
    set -l half_count (math "max(1, floor($cpu_count / 2))")
    echo $half_count
end

function makes --description "用一半可用 CPU 并行执行 make"
    make -j (__half_cpu_count) $argv
end

function xargsp --description "用一半可用 CPU 并行执行 xargs"
    xargs -P (__half_cpu_count) $argv
end

# ---------------------------------------------------------------------------
# 系统与环境 (Unix 增强)
# ---------------------------------------------------------------------------
alias ff="fastfetch"
alias nowdatetime='date "+%Y%m%d_%H%M%S"'
alias timestamp_seconds='date +%s%N | cut -c 1-10'
alias timestamp_millisecond='date +%s%N | cut -c 1-13'
alias timestamp_microsecond='date +%s%N | cut -c 1-16'

alias top='htop'
alias df='df -h'
alias du='du -kh'
alias ping='ping -c 5'
alias pws='ps -p $fish_pid'

alias tmux="tmux -2"

alias l="lsd --group-directories-first"
alias ls="l"
alias lt="ls --tree"
alias tree="ls --tree --depth 3"
alias cat='bat --paging=never'
alias cp='cp -ir'
alias mv='mv -i'
alias mkdir='mkdir -p -v'
# --preserve-root 别名已移除：BSD 的 chmod/chown/chgrp 不支持该选项
# （alias 展开为 command chmod --preserve-root 后每次调用都报 illegal option，
# 与 zsh aliases.zsh 侧同因移除；macOS 根分区本身 SIP 只读，无需此护栏）

# ---------------------------------------------------------------------------
# 备份与工具
# ---------------------------------------------------------------------------
function bak --description "备份文件，添加时间戳后缀"
    if test (count $argv) -eq 0
        echo "Usage: bak <file1> <file2> ..."
        return 1
    end
    set -l date_stamp (date +%Y%m%d_%H%M%S)
    for file in $argv
        if test -e $file
            cp -f $file $file.$date_stamp.bak
            echo "Backed up: $file -> $file.$date_stamp.bak"
        else
            echo (set_color red)"Error: $file does not exist"(set_color normal)
        end
    end
end

function timer --description "简单倒计时"
    set -l seconds $argv[1]
    if test -z "$seconds"
        echo "Usage: timer <seconds>"
        return 1
    end
    while test $seconds -gt 0
        printf "\r%02d:%02d:%02d" (math -s0 "$seconds / 3600") (math -s0 "($seconds % 3600) / 60") (math -s0 "$seconds % 60")
        sleep 1
        set seconds (math $seconds - 1)
    end
    echo -e "\n⏰ Time's up!"
    printf '\a'
end

function decide --description "从多个选项中随机选择一个"
    if test (count $argv) -lt 2
        echo "Usage: decide <option1> <option2> ..."
        return 1
    end
    set -l idx (random choice $argv)
    # 兼容旧版 fish：无 `random choice` 时的回退
    if test -z "$idx"
        set idx $argv[(random 1 (count $argv))]
    end
    echo "🎲 决定：$idx"
end
