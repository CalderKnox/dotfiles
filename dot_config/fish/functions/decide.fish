# =============================================================================
# decide.fish — 从多个选项中随机选择一个
# =============================================================================
# Description : 由原 conf.d/00_aliases.fish 迁入 functions/ 惰性加载目录。
# Usage       : decide <option1> <option2> ...
# Guards      : 少于两个选项返回 1；旧版 fish 无 random choice 时回退
#               random 1 (count $argv)
# Author      : Payne
# =============================================================================
function decide --description 从多个选项中随机选择一个
    if test (count $argv) -lt 2
        echo "Usage: decide <option1> <option2> ..."
        return 1
    end
    set -l idx (random choice $argv)
    # fallback for older fish where `random choice` not available
    if test -z "$idx"
        set idx $argv[(random 1 (count $argv))]
    end
    echo "🎲 决定：$idx"
end
