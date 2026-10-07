# =============================================================================
# timer.fish — 简单倒计时
# =============================================================================
# Description : HH:MM:SS 单行刷新倒计时，结束时响铃。由原 conf.d/
#               00_aliases.fish 迁入 functions/ 惰性加载目录。
# Usage       : timer <seconds>
# Guards      : 缺参/非正整数返回 1 并打印用法
# Author      : Payne
# =============================================================================
function timer --description 简单倒计时
    set -l seconds $argv[1]
    if test -z "$seconds"
        echo "Usage: timer <seconds>"
        return 1
    end
    if not string match -qr '^[0-9]+$' -- $seconds
        echo "timer: seconds must be a non-negative integer, got '$seconds'" >&2
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
