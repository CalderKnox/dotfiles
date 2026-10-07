# =============================================================================
# recent.fish — 最近修改的文件
# =============================================================================
# Description : 由原 conf.d/00_aliases.fish 迁入 functions/ 惰性加载目录。
# Usage       : recent [count]  默认 10
# Guards      : ls 错误静默（2>/dev/null）；head 行数 = count + 1（含标题行）
# Author      : Payne
# =============================================================================
function recent --description 'Show recently modified files (default 10)'
    set -l count 10
    if test (count $argv) -gt 0
        set count $argv[1]
    end
    ls -lt 2>/dev/null | head -n (math $count + 1)
end
