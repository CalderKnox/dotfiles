#!/bin/sh
# 为 ssh ControlPath 创建 ~/.ssh/sockets（见 private_dot_ssh/private_config）；run_once 幂等，无模板变量故无需 .tmpl 后缀。
mkdir -p "$HOME/.ssh/sockets"
chmod 700 "$HOME/.ssh/sockets"
