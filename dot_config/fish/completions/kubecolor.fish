# kubecolor → kubectl 彩色包装补全（由 conf.d/00_env.fish 迁入）。
# completions/ 按需加载：仅在实际补全 kubecolor 命令时 source，
# 未安装的机器零开销；kubectl 补全由 symlink_kubectl.fish（OrbStack）提供。
if type -q kubecolor
    complete --command kubecolor --wraps kubectl
end
