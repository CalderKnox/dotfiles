# =============================================================================
# update-all.fish — 一键更新所有开发环境 (fish 版)
# =============================================================================
# Description : 声明式批量更新（由原 conf.d/00_aliases.fish 迁入 functions/
#               惰性加载目录，首次调用时才 source）。与 zsh 侧 aliases.zsh 的
#               update-all 记账对齐：attempted/skipped/failed 三计数 + 名称
#               列表 + 每目标 ✓/✗；Rust 目标名本侧为 rust（zsh 为 rustup），
#               rustup 作为别名一并接受（跨 shell 肌肉记忆兼容）。
#               auto-update = onproxy + update-all 的薄包装定义在
#               auto-update.fish（按名自动加载）。
# Usage       : update-all [targets...]  无参全量；有参按名过滤（rustup≈rust）
# 任务: brew / rust / tldr / uv / mise / pi / sdk（sdk 未安装时跳过）
# Guards      : type -q 逐项守卫，未装跳过并计入 skipped；失败计数与耗时统计；
#               先验证全部目标名，避免 typo 时先更新一半再报错
# Author      : Payne
# =============================================================================
function update-all --description "一键更新所有开发环境 (fish 版)"
    # 任务名 fish 侧为 rust；sdk 仍按 type -q 守卫，未安装时跳过。
    set -l tasks brew rust tldr uv mise pi sdk

    set -l targets
    if test (count $argv) -eq 0
        set targets $tasks
    else
        # rustup → rust 归一化（zsh 侧目标名，两侧肌肉记忆等价）
        for arg in $argv
            if test $arg = rustup
                set -a targets rust
            else
                set -a targets $arg
            end
        end
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
    set -l attempted_names
    set -l skipped_names
    set -l failed_names
    set -l start_time (date +%s)

    for name in $targets
        echo (set_color --bold blue)"═══ Updating $name ═══"(set_color normal)

        switch $name
            case brew
                if type -q brew
                    set -a attempted_names $name
                    if brew update -f && brew upgrade -f --greedy-latest -y && brew cu -y -a && brew cleanup --prune=all
                        echo (set_color green)"✓ $name done"(set_color normal)
                    else
                        set failed (math $failed + 1)
                        set -a failed_names $name
                        echo (set_color red)"✗ $name failed"(set_color normal)
                    end
                else
                    set -a skipped_names $name
                    echo (set_color yellow)"⚠️  $name not found, skipped"(set_color normal)
                end

            case rust
                if type -q rustup
                    set -a attempted_names $name
                    if rustup update
                        echo (set_color green)"✓ $name done"(set_color normal)
                    else
                        set failed (math $failed + 1)
                        set -a failed_names $name
                        echo (set_color red)"✗ $name failed"(set_color normal)
                    end
                else
                    set -a skipped_names $name
                    echo (set_color yellow)"⚠️  $name not found, skipped"(set_color normal)
                end

            case tldr
                if type -q tldr
                    set -a attempted_names $name
                    if tldr --update
                        echo (set_color green)"✓ $name done"(set_color normal)
                    else
                        set failed (math $failed + 1)
                        set -a failed_names $name
                        echo (set_color red)"✗ $name failed"(set_color normal)
                    end
                else
                    set -a skipped_names $name
                    echo (set_color yellow)"⚠️  $name not found, skipped"(set_color normal)
                end

            case uv
                if type -q uv
                    set -a attempted_names $name
                    if uv tool upgrade --all
                        echo (set_color green)"✓ $name done"(set_color normal)
                    else
                        set failed (math $failed + 1)
                        set -a failed_names $name
                        echo (set_color red)"✗ $name failed"(set_color normal)
                    end
                else
                    set -a skipped_names $name
                    echo (set_color yellow)"⚠️  $name not found, skipped"(set_color normal)
                end

            case mise
                if type -q mise
                    set -a attempted_names $name
                    if mise upgrade
                        echo (set_color green)"✓ $name done"(set_color normal)
                    else
                        set failed (math $failed + 1)
                        set -a failed_names $name
                        echo (set_color red)"✗ $name failed"(set_color normal)
                    end
                else
                    set -a skipped_names $name
                    echo (set_color yellow)"⚠️  $name not found, skipped"(set_color normal)
                end

            case pi
                if type -q pi
                    set -a attempted_names $name
                    if pi update --all
                        echo (set_color green)"✓ $name done"(set_color normal)
                    else
                        set failed (math $failed + 1)
                        set -a failed_names $name
                        echo (set_color red)"✗ $name failed"(set_color normal)
                    end
                else
                    set -a skipped_names $name
                    echo (set_color yellow)"⚠️  $name not found, skipped"(set_color normal)
                end

            case sdk
                if type -q sdk
                    set -a attempted_names $name
                    if sdk update && sdk upgrade && sdk selfupdate && sdk flush
                        echo (set_color green)"✓ $name done"(set_color normal)
                    else
                        set failed (math $failed + 1)
                        set -a failed_names $name
                        echo (set_color red)"✗ $name failed"(set_color normal)
                    end
                else
                    set -a skipped_names $name
                    echo (set_color yellow)"⚠️  $name not found, skipped"(set_color normal)
                end
        end
        echo ""
    end

    set -l duration (math (date +%s) - $start_time)
    set -l mins (math -s0 "$duration / 60")
    set -l secs (math -s0 "$duration % 60")

    # 记账摘要（与 zsh 侧对齐）：attempted/skipped/failed + 名称列表
    echo (set_color --bold)"   attempted: "(count $attempted_names)" · skipped: "(count $skipped_names)" · failed: $failed"(set_color normal)
    if set -q skipped_names[1]
        echo (set_color yellow)"   skipped: "(string join ", " $skipped_names)(set_color normal)
    end

    if test $failed -eq 0
        # 耗时拼接需引号分断：fish 双引号内 {$mins} 的花括号按字面输出，${mins} 为语法错误
        echo (set_color --bold green)"✨ All updates completed in "$mins"m"$secs"s"(set_color normal)
    else
        echo (set_color --bold red)"   failed: "(string join ", " $failed_names)(set_color normal)
        echo (set_color --bold red)"⚠️  $failed update(s) failed, completed in "$mins"m"$secs"s"(set_color normal)
        return 1
    end
end
