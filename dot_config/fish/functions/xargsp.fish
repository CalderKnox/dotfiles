# =============================================================================
# xargsp.fish — 半核并行 xargs
# =============================================================================
# Description : xargs -P (__half_cpu_count)，与 zsh 的 xargsp 一致；
#               helper 在 functions/__half_cpu_count.fish 按名自动加载。
#               由原 conf.d/00_aliases.fish 迁入 functions/ 惰性加载目录。
# Usage       : xargsp [xargs 参数...]
# Guards      : 无（xargs 缺失时错误在调用时暴露）
# Author      : Payne
# =============================================================================
function xargsp --description "Run xargs using half the available CPUs"
    xargs -P (__half_cpu_count) $argv
end
