# ~/.config/fish/config.fish
# Main Fish shell configuration — sourced for each new shell instance.
# Guarded by __fish_config_loaded so re-sourcing is a no-op (idempotent startup).
# Related: PATH/env lives in conf.d/00_env.fish (fish_add_path, idempotent),
# mise activation in conf.d/01_activate.fish, and plugin declarations in
# fish_plugins (managed by fisher, installed under $fisher_path).

if set -q __fish_config_loaded
    exit
end
set -g __fish_config_loaded

# ---------------------------------------------------------------------------
# fisher 插件独立目录，退出 chezmoi 管理域
# ---------------------------------------------------------------------------
# fisher 把插件安装到 $fisher_path（~/.config/fish/fisher），不再写入本仓库
# 管理的 functions/completions；按 fisher 官方模式把插件目录前插进
# 函数/补全搜索路径，插件自带的 conf.d 片段存在才 source。
set -g fisher_path ~/.config/fish/fisher

set --prepend fish_function_path $fisher_path/functions
set --prepend fish_complete_path $fisher_path/completions

if test -d $fisher_path/conf.d
    for file in $fisher_path/conf.d/*.fish
        builtin source $file 2>/dev/null
    end
end

if status is-interactive
    # Interactive-only prompt: initialize starship when installed.
    # `type -q` guard makes this a no-op on machines without starship,
    # keeping non-interactive / CI startup fast.
    # 生成成功后才执行完整输出；失败的 producer 不得把部分代码送进 source。
    if type -q starship
        if set -l starship_init (starship init fish)
            printf '%s\n' $starship_init | source
        else
            echo "starship initialization failed; output not sourced." >&2
        end
    end
    if type -q zoxide
        if set -l zoxide_init (zoxide init fish)
            printf '%s\n' $zoxide_init | source
        else
            echo "zoxide initialization failed; output not sourced." >&2
        end
    end
end
