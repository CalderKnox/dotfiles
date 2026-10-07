# =============================================================================
# serve.fish — 快速 HTTP 服务器
# =============================================================================
# Description : 由原 conf.d/00_aliases.fish 迁入 functions/ 惰性加载目录。
# Usage       : serve [port]  默认 8000
# Guards      : 依赖 python3（缺失时错误在调用时暴露）；端口仅接受纯数字，
#               且仅绑定 127.0.0.1（局域网不可见，与横幅声明一致）
# Author      : Payne
# =============================================================================
function serve --description 'Start a simple HTTP server (default 8000)'
    set -l port 8000
    if test (count $argv) -gt 0
        set port $argv[1]
    end
    if not string match -qr '^[0-9]+$' -- $port
        echo "serve: invalid port '$port'" >&2
        return 1
    end
    echo (set_color green)"🚀 Server running at http://localhost:$port"(set_color normal)
    python3 -m http.server $port --bind 127.0.0.1
end
