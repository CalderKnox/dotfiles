# =============================================================================
# 01_rev.fish — 逆向工程工具 (Fish)
# =============================================================================
# Description : Android 逆向与投屏工具封装（jadx-gui、scrcpy）。
#               后台启动、失败回退与路径守卫；与 zsh 的 jdx/scr 对齐
#               但适配 Fish 的 `type -q` / `test -e` 守卫与 disown 语义。
# Usage       : 由 Fish 自动 source；函数在交互时调用，缺装时黄字提示
#               不阻断启动。
# Guards      : jadx-gui/scrcpy/JEB 均带存在性守卫；jobs disown 避免挂起
# Author      : Payne
# =============================================================================
# 原 pkid 别名已移除：指向的 ~/Applications/ApkScan-PKID.jar 已不存在
# （与 zsh 侧 aliases.zsh 同因移除），java 虽在但调用必失败
# 原 jeb 函数已移除：指向的 JEB 目录已不存在，
# （与 zsh 侧 aliases.zsh 保持一致；需要时从 git 历史找回）

function jdx --description '后台启动 jadx-gui 反编译 (fish 包装)'
    if not type -q jadx-gui
        echo (set_color red)"❌ jadx-gui not found — brew install jadx"(set_color normal)
        return 1
    end
    jadx-gui $argv >/dev/null 2>&1 &
    disown (jobs -lp | tail -1) 2>/dev/null
end

function scrcpyd --description '后台启动 scrcpy 投屏 (fish 包装)'
    if not type -q scrcpy
        echo (set_color red)"❌ scrcpy not found — brew install scrcpy"(set_color normal)
        return 1
    end
    scrcpy $argv >/dev/null 2>&1 &
    disown (jobs -lp | tail -1) 2>/dev/null
end
