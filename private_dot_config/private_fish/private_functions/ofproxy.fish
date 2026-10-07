# =============================================================================
# ofproxy.fish — 关闭终端代理
# =============================================================================
# Description : 清除 onproxy 设置的六个代理环境变量。由原 conf.d/
#               00_aliases.fish 迁入 functions/ 惰性加载目录。
# Usage       : ofproxy；开启用 onproxy（onproxy.fish）
# Guards      : 仅 set -e 清除变量，无外部依赖
# Author      : Payne
# =============================================================================
function ofproxy --description 关闭终端代理
    set -e all_proxy
    set -e http_proxy
    set -e https_proxy
    set -e ALL_PROXY
    set -e HTTP_PROXY
    set -e HTTPS_PROXY
    echo -e "⛵️ 终端代理已关闭。"
end
