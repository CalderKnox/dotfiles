# =============================================================================
# update-all.fish — 一键更新所有开发环境 (fish 版)
# =============================================================================
# Description : 声明式批量更新（由原 conf.d/00_aliases.fish 迁入 functions/
#               惰性加载目录，首次调用时才 source）。Rust 目标名为 rust，
#               zsh 为 rustup。auto-update = onproxy + update-all 的薄包装
#               定义在 auto-update.fish（按名自动加载）。
# Usage       : update-all [targets...]  无参全量；有参按名过滤
# 任务: brew / rust / tldr / uv / mise / pi / sdk（sdk 未安装时跳过）
# Guards      : type -q / command -q 逐项守卫，未装跳过；失败计数与耗时统计；
#               先验证全部目标名，避免 typo 时先更新一半再报错
# Author      : Payne
# =============================================================================
function update-all --description "一键更新所有开发环境 (fish 版)"
    # 保持本 shell 的目标名 rust；sdk 仍按 type -q 守卫，未安装时跳过。
    set -l tasks brew rust tldr uv mise pi sdk

    set -l targets
    if test (count $argv) -eq 0
        set targets $tasks
    else
        set targets $argv
    end

    # 先验证全部目标，避免 update-all uv typo 先更新 uv 再报错。
    set -l name
    for name in $targets
        if not contains -- $name $tasks
            echo "Unknown target: $name" >&2
            echo "Available: "(string join ", " $tasks) >&2
            return 1
        end
    end

    set -l failed 0
    set -l start_time (date +%s)

    for name in $targets
        echo (set_color --bold blue)"═══ Updating $name ═══"(set_color normal)

        switch $name
            case brew
                if type -q brew
                    brew update -f && brew upgrade -f --greedy-latest -y && brew cu -y -a && brew cleanup --prune=all
                    or set failed (math $failed + 1)
                else
                    echo (set_color yellow)"⚠️  brew not found, skipped"(set_color normal)
                end

            case rust
                if type -q rustup
                    rustup update
                    or set failed (math $failed + 1)
                else
                    echo (set_color yellow)"⚠️  rustup not found, skipped"(set_color normal)
                end

            case tldr
                if type -q tldr
                    tldr --update
                    or set failed (math $failed + 1)
                else
                    echo (set_color yellow)"⚠️  tldr not found, skipped"(set_color normal)
                end

            case uv
                if type -q uv
                    uv tool upgrade --all
                    or set failed (math $failed + 1)
                else
                    echo (set_color yellow)"⚠️  uv not found, skipped"(set_color normal)
                end

            case mise
                if type -q mise
                    mise upgrade
                    or set failed (math $failed + 1)
                else
                    echo (set_color yellow)"⚠️  mise not found, skipped"(set_color normal)
                end

            case pi
                if type -q pi
                    pi update --all
                    or set failed (math $failed + 1)
                else
                    echo (set_color yellow)"⚠️  pi not found, skipped"(set_color normal)
                end

            case sdk
                if type -q sdk
                    sdk update && sdk upgrade && sdk selfupdate
                    or set failed (math $failed + 1)
                else
                    echo (set_color yellow)"⚠️  sdk not found, skipped"(set_color normal)
                end
        end
        echo ""
    end

    set -l duration (math (date +%s) - $start_time)
    set -l mins (math -s0 "$duration / 60")
    set -l secs (math -s0 "$duration % 60")

    if test $failed -eq 0
        # 耗时拼接需引号分断：fish 双引号内 {$mins} 的花括号按字面输出，${mins} 为语法错误
        echo (set_color --bold green)"✨ All updates completed in "$mins"m"$secs"s"(set_color normal)
    else
        echo (set_color --bold red)"⚠️  $failed update(s) failed, completed in "$mins"m"$secs"s"(set_color normal)
        return 1
    end
end
