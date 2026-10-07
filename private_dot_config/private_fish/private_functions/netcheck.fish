# =============================================================================
# netcheck.fish — 网络快速诊断
# =============================================================================
# Description : 外网 IP / DNS / 下载测速三连。由原 conf.d/00_aliases.fish
#               迁入 functions/ 惰性加载目录。
# Usage       : netcheck
# Guards      : 只运行本机已安装的 speedtest-cli，不下载并执行可变的
#               远程 Python 源码；缺失时返回 127
# Author      : Payne
# =============================================================================
function netcheck --description 'Quick network diagnostics'
    echo (set_color cyan)"🌐 External IP:"(set_color normal)
    curl -s --max-time 5 https://icanhazip.com
    echo

    echo (set_color cyan)"📡 DNS Test:"(set_color normal)
    dig google.com +short +time=2 +tries=1 2>/dev/null | head -1
    echo

    echo (set_color cyan)"⚡ Speed Test (Download):"(set_color normal)
    # 只运行本机已安装的 speedtest-cli，不下载并执行可变的远程 Python 源码。
    if not type -q speedtest-cli
        echo "speedtest-cli not found; install it before running the speed test." >&2
        return 127
    end
    speedtest-cli --no-upload --simple
end
