# UltraCode 审查与优化

## 范围、来源与可信度

这个仓库是 macOS chezmoi **配置源目录**，不是单一应用。主要可执行逻辑是 Zsh/Fish
初始化与交互 helpers；tmux、Neovim 和终端配置依赖各自 runtime/plugin 契约。

本轮通过已配置的 `ultracode` 工作流入口做四路源码审查：Zsh、Fish、编辑器/终端、
部署与文档。run ID：`codebase-audit-muwnm02c-u17yfc`。四个审查分支均有详细输出；
独立 validator 两次达到配置的 900000ms 超时，返回 null，因此最后自动生成的
“insufficient evidence”报告**不是干净审查结果**。已恢复原始分支结果，由主代理
逐项核对源码、复现、实施补丁并运行下面列出的验证。没有把审查建议当作测试证明。
补丁后的额外只读 reviewer 也在 1200 秒达到上限，未提交答案；不将其当作通过。
最终验收由主代理的源码复核与实际测试证据完成，而非模型投票。

开始时 worktree 已含前一轮 shell/ignore/文档优化与 32-test 套件；本轮先重新运行，
32/32 通过，再扩展检查。保留既有修改，尤其未改动已有 Pi provider/model、扩展、
thinking/budget 设置；不更改运行时版本选择、代理或用户插件选择。

## 经过核对的架构洞察

1. **加载顺序有语义。** Zim/compinit → aliases → fzf → sdk；EDITOR 在 fzf options
   生成时展开。SDKMAN 应继续惰性加载，补全生成应保持热缓存不调用二进制。
2. **相同“命令字符串”由不同解释器消费。** fzf 的 shell quoting 防止 shell 注入，
   不等于 Neovim `+Ex` 参数安全，也不等于应用的 leading-dash 参数安全。fzf-tab
   的初始化是 Zsh 代码，不能直接继承普通 fzf 的 `sh -c`。
3. **原子 rename 不等于跨文件/身份一致性。** 共享 completion source 与 bytecode
   必须把检查、发布、source 纳入同一锁；只检查“二进制比缓存新”不能识别降级，
   还会在二进制 mtime 来自未来时每次生成。
4. **字节码存在不证明字节码被加载。** 对临时 basename 编译后 rename 的 .zwc
   会被 Zsh 忽略；本轮用不同 text/compiled markers 复现并纠正嵌入源文件名。
5. **tmux 的 -F 是立即展开。** theme 必须先定义模块，再构建 status，最后 collector
   插件替换占位符。重复 @plugin 声明是 TPM 正常源解析契约，不是“只加载最后一个”。
6. **事件名称不能代替 runtime 证据。** Neovim Replace/Virtual Replace 本就触发
   InsertEnter，Ctrl-O 也触发 InsertLeave；真正漏掉的是 Ctrl-C。Fish sourced-file
   guard 的 exit 并不退出整个 shell；该怀疑在实际 Fish 中被否证，未修改。
7. **Git 与 chezmoi 是两个排除域。** 前者按源名防普通提交，后者按目标名防部署；
   都不构成 Pi OS 沙箱。仅用配置文件清单无法证明 runtime deny 规则，因此
   需要合成非 JSON、encrypted/private 前缀等 fixture 与删除规则的 mutation control。

## 优化与行为变化

| 位置 | 已验证的问题 | 修复与效果 |
| --- | --- | --- |
| Zsh `sdk.zsh` completion loader | 同路径降级 stale cache、未来 mtime 反复生成、并发安装身份混用、临时 basename 字节码不消费 | 内建 stat 身份等值比较；每工具 flock（最多等 1 秒）覆盖检查/发布/source；最终 source 名编译、临时 .zwc 原子发布；失败保留旧数据但跳过错误版本 |
| 同上 SDKMAN | 初始化失败递归；reload 将真实 sdk 覆盖为 lazy stub | 先移除 placeholder；保留初始化状态；未定义实现时明确失败；初始化成功后 reload 不重复 |
| Zsh `aliases.zsh` | backup 混合结果吞失败；破坏性 uv_resync 未启用却与文档不一致 | bak 聚合错误且成功才打印；`uv_resync`（HOME reset）与 Fish 同名函数当前均以注释模板保留、未启用，文档与测试改为描述“禁用模板”而非运行时行为 |
| Zsh `fzf.zsh` | colon 文件名字段可变成 Neovim +Ex；global file actions 缺 --；fzf-tab 预览误用 sh | editor/preview 行号正整数守卫；路径使用 --；普通 sh 与 tab Zsh shell 分离；Ctrl-Y 用 printf、Ctrl-G 使用 POSIX redirection |
| 同上 fkill / ftm | PID 0 会向整个组发信号；提取依赖 sed/awk/xargs；attach 失败被 echo 掩盖 | 全选择校验正整数/去重/独立参数，移除提取 subprocess；保留 ftm attach/error 状态，取消作为无操作 |
| Zsh/Fish initialization | producer 输出部分代码后失败，仍被 eval/source | 成功捕获完整输出才执行，保留现有交互/非交互边界 |
| Fish y / bak | mktemp 失败仍启动、Yazi/cd 状态被 cleanup 掩盖、cwd 污染 caller；copy 失败仍报成功 | 分配守卫、本地 cwd、保留状态与清理；NUL/EOF/换行路径覆盖；backup aggregate status 与 -- |
| `dot_tmux.conf` | 冷启动丢 CPU/battery，RAM 模块未定义；reload 无限追加能力；TPM root 与入口不一致 | theme → status → TPM；现有 tmux-cpu 提供 RAM；能力去重；支持 XDG/传统/显式根目录；manager 缺失提示不再声称 prefix+I 能安装 manager |
| Neovim autocmd | Ctrl-C 后 Normal cursorline 仍关闭 | ModeChanged/WinEnter 根据实际模式更新，初始化及 augroup reload 幂等 |
| kitty 参考配置 | directional split shortcut 缺 splits layout 前提 | 默认 splits 布局并保留其他布局；该参考文件仍不随 chezmoi 部署 |
| Neovim/终端文档 | 旧 extras/empty specs/100 列/keymaps、错误路径/字体/注释模板描述 | 按当前 JSON/Lua/配置修订，加入关键文档契约检查 |

前轮已存在且本轮重新验证的修复：flkill header/多选/失败、frg quoting/rg filename、
fzf 可执行 prefix 与 NO_CLOBBER、Zsh y trap/status、双侧 updater 参数预检、Fish cdd/uv、
Homebrew cleanup presence-style 开关、netcheck 只调用本机 speedtest-cli、Pi Git 源名 allowlist（chezmoi 仍采用运行时黑名单）、
不存在的 sandbox 说明修正。

## 验证证据

可重复命令与隔离边界见 [validation/README.md](validation/README.md)：

```sh
python3 docs/validation/check.py --strict
python3 docs/validation/negative_controls.py --revision b4e8bac
python3 docs/validation/fzf_runtime.py
python3 docs/validation/tmux_plugins.py --plugin-root ~/.tmux/plugins --tpm-source ~/.config/tmux/plugins/tpm
python3 docs/validation/terminal_parsers.py
python3 docs/validation/benchmark_cache.py --revision b4e8bac
git diff --check
```

实际 tmux 集成采用本机源码的副本，不联网安装；collector 都被 stub：

| 插件 | 被检查的 revision |
| --- | --- |
| Catppuccin tmux | `b2f219c00609ea1772bcfbdae0697807184743e4`（2.1.3） |
| tmux-cpu | `bcb110d754ab2417de824c464730c412a3eb2769` |
| tmux-battery | `43832651ede43f54dcf0588727c1957fe648d57d` |
| TPM | `e261deb` |

本轮最初的 runtime 控制暴露了真实缺陷，也暴露了 harness 假设：TERM=dumb 下 Fish
set_color 的输出、macOS `/var` 路径 canonicalization、tmux list-keys 参数差异与
Lua assert 后需要 cquit。已纠正这些假设再验证，不把测试设施错误算成缺陷。

窄场景性能实验在隔离 Zsh 中重复加载 12 次未来 mtime 的同一 stub 二进制，3 个 samples。
后续重跑发现并修正了历史路径布局假设；见下方“后续全仓库对齐”的新 benchmark 结果。该实验
只测 loader 场景，不代表整体 shell 启动提速；系统负载会影响秒数，generator 调用次数才是稳定验收条件。

此前的优化快照记录 **77 tests** 与 **82 个 aggregate 正向检查**（核心回归、fzf、终端 parser、tmux 插件）；完整历史日志为 `.pi/tasks/01a1112b-2930-75bf-a65a-b264b9d7c248-56835/b774d2979.output`。以下“后续全仓库对齐”列出当前验证结果，避免把旧快照数字当作现行计数。

## 第三轮审计（`codebase-audit-mv9o0u60-hzqtov`）

第三轮 `ultracode` 审查（5 项并行检查 + cross-validation）确认了以下文档与源不一致，均已核对源文件后修复：

- **`uv_resync` 禁用却描述为可用**（最有影响）：Zsh `aliases.zsh` 与 Fish `conf.d/20_dev.fish` 中两个定义均为注释模板、未启用，但 `optimization.md`、`validation/README.md`、`dot_config/zsh/README.md` 与 `20_dev.fish` 头部都把它当生效行为描述。已全部改为“注释模板/未启用”，并说明测试仅校验模板存在、启用后自动恢复行为断言。
- **模块加载方式**：`docs/getting-started.md` 曾称 `.zshrc` 用 glob `for file in *.zsh(N)` 加载三模块；`dot_zshrc` 实为显式逐文件 `source`（aliases→fzf→sdk），已改正文与文档一致。
- **CPU 数探测**：`makes`/`xargsp` 曾称依赖 coreutils `nproc`；实现与 Fish 侧均在 `nproc` 缺失时回退 `sysctl -n hw.ncpu`，文档已补回退说明。
- **SSH 权限措辞**：`private_dot_ssh/private_config` 曾称 `0644 被 ssh 拒绝`；OpenSSH 只拒绝 group/other 可写的配置，`0600` 是隐私收紧而非硬性要求，已在源注释校正。
- **`onproxy` 注释**：原称“仅六个代理变量”，实际另设 `no_proxy`/`NO_PROXY`，注释已列为“六个路由变量 + 两个回环豁免变量”。
- **验证范围措辞**：`validation/README.md` 已注明 JSON/TOML 解析为显式清单、tmux 真插件入口不校验 revision 也不沙箱隔离、caller 变量哨兵仅 Fish 侧校验。
- 新增 `test_documented_disabled_and_fallback_states` 锁定上述文档/源一致性，防回归。

审计同时确认：`docs/layout.md`/`getting-started.md` 的源边界声明、ControlPath 设计、`.vscode`/`.keep` 规则、敏感名模式均与实现一致（审计报告中的 83/88 计数为其启动时快照，已由本轮 87/92 取代）。

## 第四轮审计（本机 ultracode 工作流 + 主代理独立复核）

第四轮以 9 域并行读取、每域洞察双镜对抗验证（源码准确性 / 行为反例）复核，并由主代理独立执行命令复现。只记录亲自复现的结论，未复现的模型投票不计入证据。核心发现是**一类反复出现的静默失效**：

- `.chezmoiignore` 模式**锚定在源根**：缺少 `**/` 前缀的规则只匹配仓库根，嵌套目标照常部署——与全局 `.gitignore`（无内部斜杠的模式匹配任意层级）语义相反，两种写法极易混淆，是同一份心智模型在两处得到相反结果。
- 现存三处回归：`**.log`（**只匹配仓库根、不匹配嵌套**——与 `*.log` 等效；任何 `dot_config/*/x.log` 都会被渲染进 `$HOME`。仓库内 `nvim.log` 恰好位于根目录故被排除，不能作为“已覆盖”的证据）、`node_modules/`、`.pnpm-store/`（后两者同样根锚定，嵌套依赖目录会部署）。
- 已改为 `**/*.log*`（同时覆盖轮转/压缩后的 `.log.1` / `.log.gz`）、`**/node_modules/`、`**/.pnpm-store/`；`**/.DS_Store` 因自带前缀本就正确。三处旧写法均以隔离 fixture 逐一复现为“部署”，新写法逐一复现为“排除”。
- 同一失配类此前**已发生两次**并有文档记录：源名失配的 `dot_gitconfig` / `**/dot_git` 与拼写错误 `**/REAMDME.md`（见 getting-started.md）。本轮为**第三次**，说明缺的不是单点修复而是**测试守卫**。
- 根因是覆盖缺口：`check.py` 只对 7 条 `.pi/*` 运行时规则做嵌套 fixture + mutation control，其余规则（含全部卫生规则）仅以**文档字符串**断言，从不验证其是否真能排除目标。已新增 `test_hygiene_rules_exclude_nested_targets`：15 组嵌套 fixture 逐条断言“规则生效”，并删除该规则后断言 fixture 暴露（mutation control），另加正向对照（普通配置仍部署，防止“全都排除”蒙混）。负向对照已验证：把三处规则改回旧写法后该测试按预期失败。此类回归至此**首次具备自动守卫**。
- 顺带修正三处把失效写法当生效描述的文档（`maintenance.md`、`getting-started.md`、`layout.md`），并在 `maintenance.md` 增加“根锚定陷阱”告警与新规则必须用 `**/` 前缀的约定。

### 工作流超时与本轮证据来源

本轮 9 域映射全部返回（约 70 条候选洞察），但每个洞察的双镜验证子代理在该非标准 provider 下大面积挂起（journal 停止增长十余分钟，与历史记录的 validator 超时同因）。因此**未把模型投票当作证据**：由主代理逐条以只读命令亲自复现，仅保留复现通过的条目。以下为除 `.chezmoiignore` 外，经独立复现并修复的条目。

### 测试自身可被欺骗（根因治理）

- `test_tool_and_shell_documentation_matches_sources` 的“快捷别名 29 个”断言是**自证**：测试内硬编码 29 个名字，再统计这些名字在 `20_dev.fish` 中是否存在——只能证明“清单里的名字还在”，新增别名不会改变计数（该文件实有 39 条 `^alias`）。已改为由源推导（`全部 alias − 显式登记的非快捷别名`），新增别名会改变计数并强制同步文档。负向对照：临时新增 `alias goz=` 后该测试按预期失败。
- `test_documentation_lists_fish_inventory` 用裸 `assertIn(name, text)` 断言函数名出现在文档中，对单字母函数 `y` 是**空断言**（字母 y 几乎必然出现在正文）。已改为词边界正则。负向对照：移除 `layout.md` 中独立的 `y` 词条后该测试按预期失败。
- 新增 `dot_zshrc` 三模块 source **顺序**断言：原测试只断言三条 `source` 字符串“存在”，与顺序无关，把 `fzf.zsh` 挪到 `aliases.zsh` 之前仍会通过——而 `fzf.zsh` 在 source 时展开 `$EDITOR`，顺序即语义。负向对照：交换顺序后该断言按预期失败。
- 新增 `test_fish_plugin_inventory_matches_documentation`：`fish_plugins` 的插件数此前**无任何**验证，增删插件不触发失败、文档“13 插件”可静默漂移。改为由源文件推导计数并对照四处文档声明。负向对照：追加第 14 个插件后该测试按预期失败。

### 已复现并修复的源码/文档不一致

| 位置 | 复现结论 | 修复 |
| --- | --- | --- |
| fish `update-all.fish` | 全部请求目标缺失时**无** `attempted==0` 分支（zsh 侧有），会误报 “✨ All updates completed”；文件头却声称“记账与 zsh 对齐” | 补 `attempted==0` → “⚠️ no runnable targets” 并 `return 0`；新增 `test_update_all_with_no_runnable_target_matches_zsh`（负向对照已验证） |
| fish `conf.d/10_sys.fish` `cdd` | `ls -la --group-directories-first` 在无 lsd 别名（非交互）时被 BSD `/bin/ls` 拒绝，错误被 `2>/dev/null` 吞掉，静默无输出 | 回退 `or command ls -la`；新增 `test_cdd_falls_back_when_lsd_alias_is_absent`（负向对照已验证） |
| fish `ofproxy.fish` | 注释称“清除六个代理变量”，实际 unset 八个（含 `no_proxy`/`NO_PROXY`）；同一第三轮只修了 `onproxy` 孪生 | 注释改为“六个路由变量 + 两个 no_proxy” |
| fish `dus.fish` / `tree-size.fish` | 注释引用 `du='du -kh'` 别名，实际别名为 `du -h -d 2`（已与 zsh 对齐后遗留） | 注释更正为实际别名 |
| `dot_config/zsh/sdk.zsh` | `ANDROID_NDK_HOME` 硬编码 `/opt/homebrew`，而同文件/同树其它 Homebrew 引用均用 `${HOMEBREW_PREFIX:-/opt/homebrew}` | 改用 `${HOMEBREW_PREFIX:-/opt/homebrew}`（Intel 前缀兼容） |
| `docs/layout.md:45` | 称 `aliases.zsh` 新增“三别名 chezc/chezdf/chezap”，源文件实为四个（漏 `chezs`） | 更正为四别名 |
| `docs/layout.md` / `docs/shell.md` / `docs/terminals.md` | 三处称 Ghostty 保留 `zsh -l` / `tmux` 注释方案，但 `dot_config/ghostty/config` 中并无这些 token；真实注释方案在 `alacritty.toml` | 从 Ghostty 描述中删除该错误声明 |
| `README.md` / `dot_config/zsh/fzf.zsh` / `dot_config/zsh/README.md` | fzf 版本引用三处不一致（0.74.3 / 0.74.4 / 0.74.5），本机为 0.74.5 | 统一为 0.74.5 |
| `dot_config/zsh/fzf.zsh` `find_large_files` | 直接调用 `fd` 无守卫（缺失即 `command not found`），而 `dot_config/zsh/README.md:78` 称 fd“缺省回退 `rg`”——该回退实际只作用于 `FZF_DEFAULT_COMMAND`/`FZF_ALT_C_COMMAND` | 增加 `command -v fd` 守卫，缺失回退 `find`；文档更正为“FZF 走 rg 回退、`find_large_files` 走 find 回退” |
| `docs/getting-started.md:145` | 称 `gh` 依赖 `dot_gitconfig` 的 `socks5h` 代理，但该代理锚定 `[http "https://github.com"]`，**不匹配** `gh` 的 `api.github.com` | 更正为：`gh` 的 API 走 HTTPS，依赖 `onproxy` 导出的 `https_proxy`，与 `dot_gitconfig` 无关 |
| `docs/getting-started.md` / `docs/maintenance.md` | 硬编码 `managed` 目标数（`59→55`、曾达 81/82），与 README「勿依赖历史硬编码数量」自相矛盾，实测为 80 | 改为“以 `chezmoi managed` 实测为准”，保留历史叙述但去掉会过期的数字

### 已复现但**未**修改（保留待决）

- **`luac` 版本门与实际解释器不符（已补门）**：`check.py` 用宿主 `luac`（本机 5.5.1）做语法门，而 Neovim 用 LuaJIT（Lua 5.1）；5.3+ 专有语法（如 `//` 整除）可过门而在 Neovim 加载时崩溃。且 `init.lua` / `lua/config/lazy.lua` **仅**有此语法检查，从不被 `-u NONE` 运行时测试加载。已新增 `test_lua_syntax_under_neovim_luajit`：用 Neovim 自身的 LuaJIT 经 `loadfile` 编译每个配置（只编译不执行），使语法门与真实运行时解释器一致；宿主 `luac -p` 保留为快速前置门。负向对照：向 `options.lua` 注入 `local _ = 7 // 2` 后 `luac -p` 仍通过、新门按预期失败。
- **CI 工具不锁版本**：`ci.yaml:45` `brew install actionlint chezmoi fish fzf lua neovim tmux` 全不锁版本，且 dependabot 仅覆盖 `github-actions`，无任何机制跟踪这些 formula——门禁二进制可因上游发布而无仓库改动变红。
- **代理只开不关**：zsh `auto-update` 与 fish `auto-update.fish` 均调用 `onproxy` 而从不 `ofproxy`，更新后代理变量持续生效至手动清除（属设计取向，需人工确认是否改为“用完还原”）。
- **`find_large_files` 无 fd 回退**：`fzf.zsh` 中 `fd` 无守卫（`fd` 缺失即报“command not found”），而 `dot_config/zsh/README.md:78` 称“`fd`（缺省回退 `rg`）”——该回退实际只接在 `FZF_DEFAULT_COMMAND` / `FZF_ALT_C_COMMAND`，与函数无关。
- **其它已复现条目**：`.codex/` 与 `.config/kitty/` 空目录仍被 `managed` 创建（文档称“不部署”）；`ProxyCommand` 探活无 `-w` 超时；`gitconfig` 的 `[http "https://github.com"]` 不覆盖 `api.github.com`（文档称 `gh` 依赖它）；全局 `[user]` 身份写入每个 commit；Neovim 侧 `mason.lua` 装 `typescript-language-server` 而 LazyVim 用 `vtsls`、`pyrefly` 依赖浮动 lspconfig、`~/.config/nvim` 同时是独立 git 仓库、`lazyvim.json` 混入 LazyVim 运行时记账；`fish_plugins` 的“13”无测试；终端硬编码 `/opt/homebrew/bin/fish` 无回退（tmux 独有回退链）、`tmux` truecolor 覆写仅命中 `xterm-256color`；`ControlPath` 手工前缀无自动校验。均已在审计记录中留证，未改动行为。

## 第五轮审计（重设计 / 重分析 / 再验证 / 外部真值）

本轮**刻意更换视角**：不再找"文档与源码漂移"（前三轮已扫过），而是 redesign（架构是否合适）、reanalysis（真实缺陷）、review（整体风险）、revalidation（推翻既有结论），并**首次联网核验外部真值**。工作流 6 个视角、16 个 agent 全部返回（本次 verify 阶段未像前几轮那样超时）。

### 外部真值（首次联网核验，全部实测）

- **CI action SHA pin 正确且为最新**：`actions/checkout@3d3c42e5…` = `v7.0.1`、`actions/setup-python@5fda3b95…` = `v7.0.0`，两者与上游 tag 逐一相符，且正是上游最新发布（2026-07-20）。此前只把它们当"未核验的信任项"，现已证实。
- **README 版本表全部实测一致**：chezmoi v2.73.1 · zsh 5.9 · Fish 4.9.3 · fzf 0.74.5 · tmux 3.8 · Neovim 0.12.6；`mise` 的 `node = 24.19.0` 与已安装 v24.19.0 相符。
- **`optimization.md` 的 tmux 插件 revision 表**四项（Catppuccin `b2f219c`、tmux-cpu `bcb110d`、tmux-battery `4383265`、TPM `e261deb`）与本地 checkout 逐一相符。
- **无凭据泄露**：扫描全部 tracked 文件未发现 API key / token / 私钥；公开仓库的暴露面仅为 `dot_gitconfig` 中的个人邮箱与 localhost 代理（README 已提示 fork 前脱敏），`private_config` 仅含示例主机与密钥*名*。
- **发现：维护者链接已失效**——账号由 `azwpayne` 更名为 `CalderKnox`（同一 repo id 1346001910；`github.com/azwpayne` 现为 404），而 `README.md:146` 的链接与 `dot_gitconfig:20` 的 `name` 仍指旧名。**因涉及公开身份，未擅自改动**，列为待决事项。

### 自我纠错（再验证推翻了上一轮我自己写的文字）

- `optimization.md` 曾把 `**.log` 描述为"完全不匹配"，与同一提交里我写的源码注释（"只锚定仓库根"）自相矛盾。实测 `**.log` ≡ `*.log`：**匹配根级、不匹配嵌套**；根目录的 `nvim.log` 确实被排除，不能当作"意外未外泄"。已更正叙述。
- `maintenance.md` 一边声明"不要依赖硬编码 `managed` 计数"，一边写"（当前实测 80）"。已删除该数字。
- `sdk.zsh` 注释称 `ANDROID_NDK_HOME` 的改法"与同一文件其它 Homebrew 引用一致"，但该文件并无其它 Homebrew 引用。已改为指向 `dot_zshrc` / `fzf.zsh` 的既有惯例。

### 新修复（每项均已复现并配负向对照）

| 位置 | 已复现的问题 | 修复 |
| --- | --- | --- |
| `docs/validation/fzf_runtime.py` | 用裸 `unittest.main()`，**skip 视为通过**：fzf 缺失时 CI 第二道门变绿却零断言执行，与套件"任何 skip 即失败"的声明冲突 | 与 `check.py` / `terminal_parsers.py` / `tmux_plugins.py` 统一 skip 语义；隐藏 fzf 时现按预期返回非零 |
| zsh `aliases.zsh` + fish `update-all.fish` | `brew cu`（**第三方 tap** `buo/homebrew-cask-upgrade` 提供，非 brew 核心）被硬接进 `&&` 链：未装该 tap 的机器把 brew 整体误报为 failed，且 `brew cleanup` 被跳过 | 先探测 `brew commands` 再决定是否跑 cask 升级；不可用则跳过并在 stderr 提示，**真失败仍传播非零**。新增 3 个 zsh + 2 个 fish 回归测试，负向对照已验证 |
| `private_dot_ssh/private_config` | 探活 `nc -z 127.0.0.1 7890` **无超时**：7890 半开（SYN 被接受、无响应）时阻塞到内核 connect 超时（约 75s），拖垮每个 `github.com` 连接 | 改为 `nc -z -G 2 -w 2`（`-G` 已确认受支持）；`ssh -G` 解析通过，端口关闭时 4ms 返回 |
| fish `conf.d/21_k8s.fish` | `kg`/`kl`/`kd` 调用**裸 `kubectl`**（不着色），而 zsh 经 `kubecolor` 包装（着着色），文件注释却称"与 zsh 一致" | 增加受 `type -q kubecolor` 守卫的 `kubectl` 包装，与 `sdk.zsh:136` 等价；有 kubecolor 时着色、无则回落原生。注释与 getting-started 更正 |

### 新增守卫（负向对照均已验证）

- **`test_ignore_patterns_are_globstar_prefixed_or_intentionally_rooted`**：把"根锚定陷阱"从**枚举**升级为**不变式**——任何新的不带 `**/` 前缀的 `.chezmoiignore` 模式都会失败，除非显式加入 `ROOT_ANCHORED` 白名单（当前 11 条，均为刻意固定路径）。负向对照：追加 `*.tmp` 后按预期失败。这是该缺陷类（已发生三次）**首次具备结构性守卫**，而非"把已修的四条写进清单"。
- **`test_no_unexpected_top_level_deploy_target`**：固定 depth-1 部署目标集（9 项），使"新增根级源文件静默渲染进 `$HOME`"失败。负向对照：加入 `root_probe.conf` 后按预期失败。同时首次断言了 `.github` 不部署这一此前只靠"源名以点开头"的隐式不变式。
- 新增的 5 个 brew 回归测试与上文 hygiene/不变式测试**均已加入 `negative_controls.py`**（现 **20/20**），即它们对历史基线 `b4e8bac` 确实失败——覆盖上一轮"新测试无对照"的缺口。

## 后续全仓库对齐

第二轮并行审查发现并修复了以下当前文档/验证错位：

- 将所有 Git/SSH/Zsh/Fish 代理说明统一到源配置的 `7890`，并用回归测试比较端口来源。
- 同步 Ghostty Frappe、`direct:` Fish 命令、有效 quick-terminal/内存限制；同步 Alacritty 字体与 Tombi 指令注释（仅记源意图，不声称已验证 LSP 执行）；修正 mise Node 固定版本与 Zsh locale 守卫说明。
- 补全 Pi 四个配置的映射，并明确 Git 是四配置 source allowlist、chezmoi 是已知 runtime blacklist；不改变此既有部署策略。synthetic fixture 现逐条 mutation-test permission-mode 与六条 Pi 专用 runtime blacklist 规则，auth/credentials 由通用敏感路径规则验证。
- SSH ControlPath 改到既有 `~/.ssh/` 目录，使用 `%C` 哈希与已知别名的固定安全前缀，避免缺失的 sockets placeholder 和 `%n` 原始主机名导致的路径穿越；`ssh -G` 回归覆盖同端点别名及含 `../` 的恶意别名。
- 将根 `.vscode/` 的 Git 跟踪收紧为只跟踪 `extensions.json` 与 `settings.json`，并验证新增/嵌套文件仍被忽略；该 literal dot-source 目录当前不是 chezmoi target，相关 ignore pattern 为防御性规则。
- 修正文档中的 VS Code Git-editor 前置要求、关闭的 `rm/cp/mv -i` 别名、Fish-only shortcut 数量/范围、`k` shell 差异、Cargo PATH 初始化、Git LFS 条件依赖及 sensitive-name ignore patterns。
- 修复 concurrent completion 测试：生产锁等待超时后允许安全跳过；随后仍要求新进程加载完整发布缓存。
- 修复基准脚本对旧 `private_dot_config/zsh/sdk.zsh` 路径的探测，并在所有 Python 验证入口导入项目模块前禁止写 `.pyc`；negative controls 默认改用兼容旧布局的历史提交。新增 bytecode-hygiene 测试，断言每个入口在导入项目模块前关闭写字节码且 `docs/validation/` 无 `__pycache__`；并新增 fish 清单一致性测试，断言文档中的 functions/conf.d/completions 清单、名称与计数与源目录一致（据此发现并修正 maintenance.md 函数枚举漏项）；新增 CI 一致性测试，断言 `.github/workflows/ci.yaml` 与 validation README 声明的入口一致。

当前验证结果：

- `python3 docs/validation/check.py --strict`：**99 passed，0 skipped**。
- `python3 docs/validation/negative_controls.py`：**20/20 reproduced，0 invalid controls**；默认 baseline 为 `b4e8bac`。
- `fzf_runtime.py`：**2 passed**；`terminal_parsers.py`：**2 passed**；本机插件副本上的 `tmux_plugins.py`：**1 passed**。
- 合计 **104 个正向检查**（99+2+2+1），但**必须区分 CI 可复现的部分**：CI 只运行 `check.py --strict` 与 `fzf_runtime.py` = **101**；`terminal_parsers.py`（2）与 `tmux_plugins.py`（1）需 macOS GUI 应用与本机插件副本，**只在本地运行、CI 不执行**。此前把 97 说成"均来自独立成功的入口"会让人误以为 CI 覆盖 97——这是自我纠正。
- 各入口的 skip 语义已统一：`check.py`、`fzf_runtime.py`、`terminal_parsers.py`、`tmux_plugins.py` 在**任何 skip 时都返回非零**。`fzf_runtime.py` 此前用裸 `unittest.main()`（skip 视为通过），fzf 缺失会让 CI 第二道门变绿却零断言执行，已修复。
- 历史 benchmark `--revision b4e8bac` 自动找到 `private_dot_config/zsh/sdk.zsh`：baseline generator calls **12/12/12**，worktree **1/1/1**。某次记录的 median 为 **1.0287s → 0.6294s**；后续审计的 wall time 波动更大，因此这些秒数只作历史快照，generator 调用次数才是稳定结果。不作整体启动提速声明。
- `ruff check --isolated docs/validation/*.py`、`actionlint -color .github/workflows/ci.yaml`、`git diff --check` 均通过；验证目录无 `__pycache__`。

没有运行 `chezmoi apply`、外网更新器或 GUI 视觉验收。`.chezmoiignore` 保持已记录的 Pi runtime blacklist（不是 deployment allowlist）；本仓库仍未附完整 `LICENSE` 文本，README 已明确提示该分发前置事项。

## 保留边界与兼容性决定

- 未 apply 到真实 HOME，未执行真实更新器/killer，也未 bootstrap 编辑器或联网；
  native terminal parser 不等于 GUI 体验或字体渲染验证。
- `frg` 仍不提供可靠 colon 文件名导航；危险非数字行字段被拒绝，但完整 NUL/结构化
  协议属于另外的功能改造。
- executable stat 不是密码学内容 hash，也不识别保持不变的 shim 后端；这里的 Docker/
  kubectl 解析为实际本机二进制。锁文件保留是正确的稳定 inode 协议，不是泄漏。
- Fish conf.d 的非交互 aliases 边界与 alternate-XDG Fisher 迁移保持既有行为；所有测试
  必须同时隔离 HOME/XDG，不能只设 alternate XDG。
- `uv_resync`（Zsh 目标 HOME、Fish 目标项目目录）当前在两个 shell 中都以注释模板
  保留、**未启用**；对应测试只校验模板存在，启用后会自动恢复行为断言。将来若启用，
  它仍是主动调用的破坏性操作，不是无损同步。
- `bak` 保留 shell 原有命名与覆盖策略，不保证并发同一时间戳备份的事务性。
- symlink 模板使用 HOME；指定另一个 destination 而不隔离 HOME
  不构成安全 apply 沙箱。常规 HOME 部署契约没有改变。
- 浮动 mise/plugin 选择保留；本次验证覆盖所列本机版本，不保证所有历史或未来版本。
- **没有测量真实 shell 全链路启动时间，不声明整体提速百分比。** 可证明的性能收益是
  generator/提取子进程调用数、真实 bytecode 消费和不再增长的 reload 状态。
- **属"所有权决策"、记录但未改**：① `lazyvim.json` 混入 LazyVim 运行时键（`version`/`install_version`/`news`）而它同时是 chezmoi 管理目标——剥离 volatile 键并不能阻止 LazyVim 回写，而不管理则失去 extras 的跨机复现，需人工定夺哪一侧是唯一真源；② `fisher` 会覆写 chezmoi 管理的 `~/.config/fish/fish_plugins`（`fisher.fish:4,220` 证实清单路径为 `$__fish_config_dir`）——把清单迁到 `$fisher_path` 会失去"新机自带 13 插件"，保留则每次 `fisher update` 后需 `apply` 复原头部注释；③ fish 侧的 `k=kubecolor` 仍为**无条件**别名（与 zsh 的 `command -v kubecolor` 守卫不同），已在 getting-started 说明但未改为守卫式，以保留既有行为。
- **需独立一轮的设计项（已复现，本轮不动）**：`.chezmoiroot` 结构化部署集（一次性搬移约 70 文件）；zsh/fish 单一真源 + 跨 shell 一致性测试（手工镜像的别名已漂移）；`sdk.zsh` 中并发敏感的补全缓存引擎与声明式 env 混居于每个交互启动路径；`mason` 的 19 个包名仅 2 个被断言、`lazyvim.json` extras 仅校验计数（需 opt-in 的 `neovim_inventory.py`）；harness 的能力分层（`--strict` 可移植 vs `--strict-runtime` 需 socket/PTY）；文档清单由生成器产出而非 grep 断言。
- **zsh SDKMAN 桩在初始化失败后不可重试**（`unfunction sdk` 先于 `source`），与"失败不得递归"的守卫耦合；现测只断言不递归。改为"成功后解除、失败重装可重试"需同时保持递归守卫，留待独立改动。
