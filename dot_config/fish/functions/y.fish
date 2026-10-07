# =============================================================================
# y.fish — yazi 包装：退出时自动 cd 到最后浏览的目录
# =============================================================================
# Description : 由原 conf.d/00_aliases.fish 迁入 functions/ 惰性加载目录。
#               mktemp 落盘 cwd、退出码透传、tmp 清理与 NUL/换行终止兼容。
# Usage       : y [yazi 参数...]
# Guards      : mktemp 失败即刻返回不启动 yazi；read -z 在 EOF 仍赋值，
#               兼容无终止符路径和 NUL 终止格式
# Author      : Payne
# =============================================================================
function y --description 'yazi wrapper: cd to last dir on exit'
    set -l tmpdir /tmp
    set -q TMPDIR; and test -n "$TMPDIR"; and set tmpdir "$TMPDIR"
    set -l tmp (command mktemp "$tmpdir/yazi-cwd.XXXXXX")
    or return $status
    test -n "$tmp"; or return 1
    set -l cwd
    command yazi $argv --cwd-file="$tmp"
    set -l rc $status
    if test $rc -eq 0
        # read 在 EOF 仍赋值；兼容 yazi 无终止符路径和 NUL 终止格式。
        read -z cwd <"$tmp"
        # 旧封装宣称兼容换行终止；仅在原值不是有效目录时去掉尾部换行。
        if not test -d "$cwd"
            set cwd (string trim --right --chars \n -- "$cwd")
        end
        if test -n "$cwd"; and test "$cwd" != "$PWD"; and test -d "$cwd"
            builtin cd -- "$cwd"
            set rc $status
        end
    end
    command rm -f -- "$tmp"
    return $rc
end
