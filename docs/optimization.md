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
| Zsh `aliases.zsh` | uv 缺失时先删除 HOME 状态；backup 混合结果吞失败 | uv 前置检查 + 独立引用路径/`--` + 步骤短路；仍保留 HOME reset 作用域；bak 聚合错误且成功才打印 |
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

## 后续全仓库对齐

第二轮并行审查发现并修复了以下当前文档/验证错位：

- 将所有 Git/SSH/Zsh/Fish 代理说明统一到源配置的 `7890`，并用回归测试比较端口来源。
- 同步 Ghostty Frappe、`direct:` Fish 命令、有效 quick-terminal/内存限制；同步 Alacritty 字体与 Tombi 指令注释（仅记源意图，不声称已验证 LSP 执行）；修正 mise Node 固定版本与 Zsh locale 守卫说明。
- 补全 Pi 四个配置的映射，并明确 Git 是四配置 source allowlist、chezmoi 是已知 runtime blacklist；不改变此既有部署策略。synthetic fixture 现逐条 mutation-test permission-mode 与六条 Pi 专用 runtime blacklist 规则，auth/credentials 由通用敏感路径规则验证。
- SSH ControlPath 改到既有 `~/.ssh/` 目录，使用 `%C` 哈希与已知别名的固定安全前缀，避免缺失的 sockets placeholder 和 `%n` 原始主机名导致的路径穿越；`ssh -G` 回归覆盖同端点别名及含 `../` 的恶意别名。
- 将根 `.vscode/` 的 Git 跟踪收紧为只跟踪 `extensions.json` 与 `settings.json`，并验证新增/嵌套文件仍被忽略；该 literal dot-source 目录当前不是 chezmoi target，相关 ignore pattern 为防御性规则。
- 修正文档中的 VS Code Git-editor 前置要求、关闭的 `rm/cp/mv -i` 别名、Fish-only shortcut 数量/范围、`k` shell 差异、Cargo PATH 初始化、Git LFS 条件依赖及 sensitive-name ignore patterns。
- 修复 concurrent completion 测试：生产锁等待超时后允许安全跳过；随后仍要求新进程加载完整发布缓存。
- 修复基准脚本对旧 `private_dot_config/zsh/sdk.zsh` 路径的探测，并在所有 Python 验证入口导入项目模块前禁止写 `.pyc`；negative controls 默认改用兼容旧布局的历史提交。新增 bytecode-hygiene 测试，断言每个入口在导入项目模块前关闭写字节码且 `docs/validation/` 无 `__pycache__`；并新增 fish 清单一致性测试，断言文档中的 functions/conf.d/completions 清单、名称与计数与源目录一致（据此发现并修正 maintenance.md 函数枚举漏项）。

当前验证结果：

- `python3 docs/validation/check.py --strict`：**85 passed，0 skipped**。
- `python3 docs/validation/negative_controls.py`：**17/17 reproduced，0 invalid controls**；默认 baseline 为 `b4e8bac`。
- `fzf_runtime.py`：**2 passed**；`terminal_parsers.py`：**2 passed**；本机插件副本上的 `tmux_plugins.py`：**1 passed**。
- 合计 **90 个正向检查**（85+2+2+1），均来自上述独立成功的入口。
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
- Zsh uv reset 仍作用于 HOME，Fish reset 仍作用于项目目录；两者都是主动调用的
  破坏性操作，不是无损同步。
- `bak` 保留 shell 原有命名与覆盖策略，不保证并发同一时间戳备份的事务性。
- symlink 模板使用 HOME；指定另一个 destination 而不隔离 HOME
  不构成安全 apply 沙箱。常规 HOME 部署契约没有改变。
- 浮动 mise/plugin 选择保留；本次验证覆盖所列本机版本，不保证所有历史或未来版本。
- **没有测量真实 shell 全链路启动时间，不声明整体提速百分比。** 可证明的性能收益是
  generator/提取子进程调用数、真实 bytecode 消费和不再增长的 reload 状态。
