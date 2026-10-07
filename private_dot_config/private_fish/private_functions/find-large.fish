# =============================================================================
# find-large.fish — 按大小阈值查找大文件
# =============================================================================
# Description : 由原 conf.d/00_aliases.fish 迁入 functions/ 惰性加载目录。
# Usage       : find-large [size]  默认 100M；接受 100M / 500M / 1G 等
# Guards      : find 语法 -size +$size_limit；结果按大小可读输出
# Author      : Payne
# =============================================================================
function find-large --description 'Find large files by size (default 100M)'
    set -l size_limit 100M
    if test (count $argv) -gt 0
        set size_limit $argv[1]
    end
    # +size_limit 为 find 语法（-size +100M）；结果按大小可读输出
    find . -type f -size +$size_limit -exec ls -lh {} \; 2>/dev/null | awk '{ print $9 ": " $5 }' | sort -k2hr
end
