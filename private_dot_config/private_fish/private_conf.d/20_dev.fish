# =============================================================================
# 20_dev.fish — 开发与构建别名 (Fish)
# =============================================================================
# Description : 开发工具链快捷别名（gh/lazygit、pnpm、Go/Rust、Maven、
#               Python/uv、数据库、AI 助手）。与 zsh 的 dev 段对齐，
#               仅包含 Fish 侧常用的 pnpm/cargo/go/mvn 封装；其余保留
#               为注释模板，按需启用。
# Usage       : 由 Fish 自动 source（conf.d 字典序，2x 为领域层，顺序无关）；
#               无需手动 source；此处别名/函数在非交互 shell 中也会定义。
# Guards      : uv_resync 先检查 uv，再删除 .venv/uv.lock，逐步成功后重建并
#               uv sync --upgrade；仍需在项目根目录主动调用；
#               AI 助手别名 (cla/clp 等) 为普通别名、未加 type -q 守卫，
#               二进制缺失时错误在调用时暴露（属预期）。
# Author      : Payne
# =============================================================================

# ~~~ github-cli 相关 ~~~
alias gopen='gh browse'
alias lg='lazygit'

# ~~~ Node.js 工具 ~~~
# alias ni="npm install"
# alias nid="npm install --save-dev"
# alias nig="npm install -g"
# alias ns="npm start"
# alias nt="npm test"
# alias nr="npm run"
# alias npxl="npx --no-install"

# alias yi="yarn install"
# alias ya="yarn add"
# alias yad="yarn add --dev"
# alias yr="yarn remove"
# alias ys="yarn start"
# alias yt="yarn test"

alias pnpi="pnpm install"
alias pnpa="pnpm add"
alias pnpad="pnpm add -D"
alias pnps="pnpm start"
alias pnpt="pnpm test"

# ~~~ Go 工具 ~~~
alias gob="go build"
alias gor="go run"
alias got="go test"
alias gom="go mod"
alias gomt="go mod tidy"
alias goi="go install"

# ~~~ Rust 工具 ~~~
alias cb="cargo build"
alias cr="cargo run"
alias ct="cargo test"
alias cc="cargo check"
alias ccl="cargo clean"
alias cu="cargo update"

# ~~~ Java/Maven ~~~
alias mvnc="mvn clean"
alias mvni="mvn install"
alias mvnp="mvn package"
alias mvnt="mvn test"
alias mvnci="mvn clean install"

# ~~~ Python 工具 ~~~
alias pipi="pip install"
alias pipid="pip install -e ."
alias pipr="pip uninstall"
alias pipl="pip list"
alias pipu="pip install --upgrade pip"
alias ruff_auto='ruff check --fix --exit-zero . && ruff format .'
alias pip_tsinghua_mirror='python3 -m pip install -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple'
# alias uv_resync='rm -rf .venv uv.lock && bass uv pip sync --allow-empty-requirements <(cat /dev/null) && uv sync --upgrade'
# alias uvsync='rm -rf .venv uv.lock && bass uv pip sync --allow-empty-requirements /dev/null && uv sync --upgrade'

# # ⚠️ 破坏性操作：删除当前目录 .venv 与 uv.lock。注意 zsh 同名函数目标是 $HOME/.venv 与 ~/uv.lock（zsh/aliases.zsh、zsh/README.md 注意事项 1），两侧行为不同，勿混用。
# function uv_resync
#     if not type -q uv
#         echo "uv not found; .venv and uv.lock left unchanged." >&2
#         return 127
#     end
#     rm -rf -- .venv uv.lock; or return
#     uv venv; or return  # 显式创建虚拟环境；失败时不继续 sync
#     uv sync --upgrade
# end


# alias pyserver="python -m http.server 8000"
# alias pyv="python -m venv"

# ~~~ 数据库工具 ~~~
alias mongo-local="mongosh mongodb://localhost:27017"
alias redis-cli="redis-cli -h localhost"
# 原 mysql-local / pg-local 别名已移除：本机无 mysql/psql（含 mise），
# 调用必失败；与 zsh 侧数据库别名清理保持一致


# =============================================================================
# AI 助手
# Agent-Native
# =============================================================================
# alias cla="claude --effort=max"
alias cla="claude"
alias cla-unsafe="claude --dangerously-skip-permissions"
# alias cla="claude --permission-mode auto --effort=max"
# alias cla-unsafe="claude --permission-mode auto --effort=max"

alias clp="opencode"
alias clpconfig="code ~/.config/opencode"
alias claconfig="code ~/.claude"
