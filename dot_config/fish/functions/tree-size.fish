# =============================================================================
# tree-size.fish — 目录大小可视化（深度 1）
# =============================================================================
# Description : 由原 conf.d/00_aliases.fish 迁入 functions/ 惰性加载目录。
# Usage       : tree-size
# Guards      : command du 绕开 conf.d/10_sys.fish 的 du='du -kh' 别名；
#               -d 1 为 BSD/GNU 通用的深度写法（原 --max-depth=1 仅 GNU du
#               支持，BSD 下静默失败输出为空）
# Author      : Payne
# =============================================================================
function tree-size --description 'Visualize directory sizes'
    # command 绕开 conf.d/10_sys.fish 的 du='du -kh' 别名；-d 1 为 BSD/GNU 通用的深度写法
    # （原 --max-depth=1 仅 GNU du 支持，BSD 下静默失败输出为空）
    command du -h -d 1 2>/dev/null | sort -hr | head -20
end
