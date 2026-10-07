# =============================================================================
# makes.fish — 半核并行 make
# =============================================================================
# Description : make -j (__half_cpu_count)，与 zsh 的 makes 一致；
#               helper 在 functions/__half_cpu_count.fish 按名自动加载。
#               由原 conf.d/00_aliases.fish 迁入 functions/ 惰性加载目录。
# Usage       : makes [make 参数...]
# Guards      : 无（make 缺失时错误在调用时暴露）
# Author      : Payne
# =============================================================================
function makes --description "Run make using half the available CPUs"
    make -j (__half_cpu_count) $argv
end
