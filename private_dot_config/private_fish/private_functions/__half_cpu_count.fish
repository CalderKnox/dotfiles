# =============================================================================
# __half_cpu_count.fish — 半核 CPU 数计算（makes/xargsp 的私有 helper）
# =============================================================================
# Description : 返回可用 CPU 数的一半（最小 1）。双下划线前缀使 fish 补全
#               隐藏该函数；makes/xargsp 调用时经 functions/ 按名自动加载。
# Usage       : 内部 helper，勿直接调用；以 (__half_cpu_count) 形式展开
# Guards      : nproc/sysctl 双路径探测；输出非数字时回退 1
# Author      : Payne
# =============================================================================
function __half_cpu_count --description "Return half the available CPU count, minimum 1"
    set -l cpu_count 1
    if type -q nproc
        set cpu_count (nproc)
    else if type -q sysctl
        set cpu_count (sysctl -n hw.ncpu 2>/dev/null)
    end
    if not string match -qr '^[0-9]+$' -- $cpu_count
        set cpu_count 1
    end
    set -l half_count (math "max(1, floor($cpu_count / 2))")
    echo $half_count
end
