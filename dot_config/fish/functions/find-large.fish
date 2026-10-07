# =============================================================================
# find-large.fish — 按大小阈值查找大文件
# =============================================================================
# Description : 由原 conf.d/00_aliases.fish 迁入 functions/ 惰性加载目录。
# Usage       : find-large [size]  默认 100M；接受 100M / 500M / 1G 等
# Guards      : size 参数校验（数字+可选 K/M/G/T 后缀）；du -h {} + 批量管道
#               制表符分隔、路径原样输出，含空格路径安全
# Author      : Payne
# =============================================================================
function find-large --description 'Find large files by size (default 100M)'
    set -l size_limit 100M
    if test (count $argv) -gt 0
        set size_limit $argv[1]
    end
    if not string match -qr '^[0-9]+[KMGT]?$' -- $size_limit
        echo "find-large: invalid size '$size_limit' (expected e.g. 100M, 500M, 1G)" >&2
        return 1
    end
    # -size +$size_limit 为 find 语法；du -h {} + 一次批量传递，输出按大小降序
    find . -type f -size +$size_limit -exec du -h {} + 2>/dev/null | sort -hr
end
