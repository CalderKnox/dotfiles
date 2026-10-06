# =============================================================================
# 02_mise.fish — mise 版本管理器激活
# =============================================================================
# Description : Fish 启动时激活 mise（02_ 前缀保证在 00_env/01_dev 之后加载）。
#               `mise activate fish` 注入 shim 与目录钩子，使 node/go/bun 等
#               由 ~/.config/mise/config.toml 管理的工具自动进入 PATH；
#               版本选择由该文件声明（当前 latest 浮动），此处仅负责激活。
# Usage       : 由 Fish 自动 source（conf.d 目录按字典序加载）；无需手动 source
# Guards      : type -q mise 守卫，未安装 mise 的机器为 no-op；
#               activate 输出幂等，重复 source 安全
# Author      : Payne
# =============================================================================

# mise 激活（存在才启用）
if type -q mise
    if set -l mise_init (mise activate fish)
        printf '%s\n' $mise_init | source
    else
        echo "mise activation failed; output not sourced." >&2
    end
end
