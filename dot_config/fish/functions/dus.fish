# =============================================================================
# dus.fish — 目录磁盘占用汇总（排序）
# =============================================================================
# Description : 由原 conf.d/00_aliases.fish 迁入 functions/ 惰性加载目录。
# Usage       : dus
# Guards      : command du 绕过 du→'du -h -d 2' 别名（-sh 与别名自带 -d 2 冲突）；错误静默，
#               按人类可读大小降序
# Author      : Payne
# =============================================================================
function dus --description 'Disk usage summary (sorted)'
    command du -sh */ 2>/dev/null | sort -hr
end
