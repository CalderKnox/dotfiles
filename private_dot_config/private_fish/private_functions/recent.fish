# =============================================================================
# recent.fish — 最近修改的文件
# =============================================================================
# Description : 由原 conf.d/00_aliases.fish 迁入 functions/ 惰性加载目录。
# Usage       : recent [count]  默认 10
# Guards      : command ls 绕过 ls→l(lsd) 别名，行为确定；count 仅接受数字
# Author      : Payne
# =============================================================================
function recent --description 'Show recently modified files (default 10)'
    set -l count 10
    if test (count $argv) -gt 0
        set count $argv[1]
    end
    if not string match -qr '^[0-9]+$' -- $count
        echo "recent: invalid count '$count'" >&2
        return 1
    end
    command ls -t | head -n $count
end
