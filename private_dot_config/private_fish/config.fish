# ~/.config/fish/config.fish
# Fish 主配置 —— 每个新 shell 实例都会 source。
# 以 __fish_config_loaded 守卫，重复 source 为空操作（幂等启动）。
# 相关文件: PATH/环境变量在 conf.d/00_env.fish（fish_add_path，幂等），
# fzf 键位在 conf.d/fzf.fish（fzf_configure_bindings），
# 插件清单在 fish_plugins（由 fisher 管理）。

if set -q __fish_config_loaded
    exit
end
set -g __fish_config_loaded

if status is-interactive
    # 仅交互式提示符: 已安装时初始化 starship。
    # `type -q` 守卫使未装 starship 的机器上为空操作，
    # 保持非交互 / CI 启动速度。
    type -q starship; and starship init fish | source
    type -q zoxide; and zoxide init fish | source
end
