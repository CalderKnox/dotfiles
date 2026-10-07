# =============================================================================
# onproxy.fish — 启用终端代理
# =============================================================================
# Description : 设置 HTTP/HTTPS + SOCKS5 代理环境变量（与 dot_gitconfig /
#               ssh config 同端口 5376，统一为 5376）。由原 conf.d/
#               00_aliases.fish 迁入 functions/ 惰性加载目录。
# Usage       : onproxy；关闭用 ofproxy（ofproxy.fish）
# Guards      : 仅 set -gx 六个代理变量，无外部依赖
# Author      : Payne
# =============================================================================
function onproxy --description "启用终端代理 (127.0.0.1:5376, socks5/http)"
    set -l proxy_host "127.0.0.1"
    set -l proxy_port 5376
    set -l proxy_url "http://$proxy_host:$proxy_port"
    set -l socks_url "socks5h://$proxy_host:$proxy_port"

    set -gx all_proxy "$socks_url"
    set -gx http_proxy "$proxy_url"
    set -gx https_proxy "$proxy_url"
    set -gx ALL_PROXY "$socks_url"
    set -gx HTTP_PROXY "$proxy_url"
    set -gx HTTPS_PROXY "$proxy_url"
    # 回环豁免（与 zsh 侧一致）：本机/localhost 流量不走代理
    set -gx no_proxy "localhost,127.0.0.1,::1"
    set -gx NO_PROXY "localhost,127.0.0.1,::1"

    echo -e "🚀 终端代理已开启："
    echo -e "   HTTP/HTTPS: $proxy_url"
    echo -e "   SOCKS5: $socks_url"
end
