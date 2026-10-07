# =============================================================================
# serve.fish — 快速 HTTP 服务器
# =============================================================================
# Description : 由原 conf.d/00_aliases.fish 迁入 functions/ 惰性加载目录。
# Usage       : serve [port]  默认 8000
# Guards      : 依赖 python3（缺失时错误在调用时暴露）
# Author      : Payne
# =============================================================================
function serve --description 'Start a simple HTTP server (default 8000)'
    set -l port 8000
    if test (count $argv) -gt 0
        set port $argv[1]
    end
    echo (set_color green)"🚀 Server running at http://localhost:$port"(set_color normal)
    python3 -m http.server $port
end
