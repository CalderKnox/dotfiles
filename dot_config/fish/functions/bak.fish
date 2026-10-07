# =============================================================================
# bak.fish — 批量备份文件（时间戳后缀）
# =============================================================================
# Description : 为每个参数文件生成 <file>.<YYYYmmdd_HHMMSS>.bak 副本。
#               由原 conf.d/00_aliases.fish 迁入 functions/ 惰性加载目录。
# Usage       : bak <file1> <file2> ...
# Guards      : 缺参返回 1；不存在的文件跳过并计失败；command cp -f --
#               防御前导连字符文件名；任一失败返回 1
# Author      : Payne
# =============================================================================
function bak --description "备份文件，添加时间戳后缀"
    if test (count $argv) -eq 0
        echo "Usage: bak <file1> <file2> ..."
        return 1
    end
    set -l date_stamp (date +%Y%m%d_%H%M%S)
    set -l failed 0
    for file in $argv
        if not test -e "$file"
            echo (set_color red)"Error: $file does not exist"(set_color normal) >&2
            set failed 1
            continue
        end
        set -l backup "$file.$date_stamp.bak"
        if command cp -f -- "$file" "$backup"
            echo "Backed up: $file -> $backup"
        else
            echo (set_color red)"Error: failed to back up $file"(set_color normal) >&2
            set failed 1
        end
    end
    return $failed
end
