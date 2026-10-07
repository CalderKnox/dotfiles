# =============================================================================
# filestats.fish — 当前目录文件类型统计
# =============================================================================
# Description : 按扩展名统计文件数（Top 20）。由原 conf.d/00_aliases.fish
#               迁入 functions/ 惰性加载目录。
# Usage       : filestats
# Guards      : find 错误静默（2>/dev/null）
# Author      : Payne
# =============================================================================
function filestats --description 'Show file type statistics in current directory'
    find . -type f 2>/dev/null | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -20
end
