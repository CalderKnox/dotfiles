# =============================================================================
# 01_activate.fish — 工具链激活 (mise / SDKMAN)
# =============================================================================
# Description : Fish 启动时的激活层（01_ 前缀保证紧随 00_env 的 PATH 收敛之后
#               加载，mise shim 因此覆盖 Homebrew/系统同名二进制）。
#               `mise activate fish` 注入 shim 与目录钩子，使 node/go/bun 等
#               由 ~/.config/mise/config.toml 管理的工具自动进入 PATH；
#               版本选择由该文件声明（当前 latest 浮动），此处仅负责激活。
#               starship/zoxide 等交互初始化仍留在 config.fish 的
#               status is-interactive 块（仅交互 shell 生效）；另含 SDKMAN
#               惰性桩（见文末，与 zsh 侧 sdk.zsh 同契约）。
# Usage       : 由 Fish 自动 source（conf.d 目录按字典序加载）；无需手动 source
# Guards      : type -q mise 守卫，未安装 mise 的机器为 no-op；
#               activate 输出幂等，重复 source 安全；SDKMAN 桩仅在
#               ~/.sdkman/bin/sdkman-init.sh 存在且无同名函数时定义
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

# --- SDKMAN 惰性桩（与 zsh 侧 sdk.zsh 同契约；差异：init 为 bash 脚本）---
# sdkman-init.sh 是 bash 脚本，函数体无法回传 fish，故与 zsh 的“接管式”惰性
# 加载不同：桩在首次及后续每次调用时，经 fisher 插件 edc/bass 在子 bash 中
# source init 并转发命令。注意 bass v2（__bass.py）把各参数空格拼接后直接交
# bash -c 执行，不识别旧版 ';and'/';or' 约定，故此处传 bash 原生 '&&' 字面参数
# （source 失败则不执行 sdk，且失败状态码经 bass 回传）；PATH/JAVA_HOME 等
# 导出变量由 bass 差量回传本会话
# （多次调用 PATH 可能累积重复项，可接受）。JAVA_HOME 与 candidate PATH 注入
# 因此延迟到首次 sdk 调用；未安装 SDKMAN（init 文件缺失）时不定义任何内容，
# update-all 的 sdk 目标随之跳过；已存在同名 sdk 函数时不覆盖。
if test -s "$HOME/.sdkman/bin/sdkman-init.sh"; and not functions -q sdk
    function sdk --description 'SDKMAN! lazy wrapper (bash init forwarded via bass)'
        if not type -q bass
            echo "sdk: fisher plugin edc/bass is required to run SDKMAN's bash init." >&2
            return 127
        end
        bass source "$HOME/.sdkman/bin/sdkman-init.sh" '&&' sdk $argv
    end
end
# --- end SDKMAN ---
