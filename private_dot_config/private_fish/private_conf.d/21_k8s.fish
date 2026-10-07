# =============================================================================
# 21_k8s.fish — Kubernetes / 容器别名 (Fish)
# =============================================================================
# Description : kubectl/krew 快捷别名（k=kubecolor 彩色包装）。由原
#               conf.d/00_aliases.fish 迁入，与 zsh 侧 sdk.zsh 的
#               k→kubecolor 对齐；kubecolor 补全在 completions/kubecolor.fish
#               （按需加载，不在启动时注册）。
# Usage       : 由 Fish 自动 source（conf.d 字典序，2x 为领域层，顺序无关）；
#               别名在非交互 shell 中也会定义。
# Guards      : 别名未加 type -q 守卫，kubecolor/krew 缺失时错误在调用时
#               暴露（属预期，与 20_dev 的 AI 助手别名策略一致）
# Author      : Payne
# =============================================================================

# ---------------------------------------------------------------------------
# Kubernetes / 容器 (与 zsh sdk.zsh 的 k→kubecolor 一致，fish 侧别名形态)
# ---------------------------------------------------------------------------
alias k="kubecolor"
alias kk="k krew"
alias kg="kubectl get"
alias kl="kubectl logs"
alias kd="kubectl describe"
