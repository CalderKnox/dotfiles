# 验证与回归

验证只读取仓库源码，使用临时目录、隔离 HOME/XDG 与 stub 命令。**不会**执行
`chezmoi apply`、bootstrap 插件、运行真实更新器/进程 killer 或主动访问网络。
私有 tmux socket 与 `nvim -u NONE -i NONE -n` 不连接用户现有实例。

> 隔离说明：“不联网”靠 stub 与隔离环境实现，不是内核级网络沙箱。个别入口
> （如 `tmux_plugins.py`）会执行调用者提供的插件目录中的代码，无法保证
> 任意外部代码不联网；只应传入可信的插件副本。

## 主要验收入口

CI（`.github/workflows/ci.yaml`，`macos-latest`）在 push/PR 上运行
`actionlint`、`check.py --strict` 与 `fzf_runtime.py`；本文其余入口（negative
controls、terminal parsers、tmux plugins、benchmark）需手动运行。

```sh
python3 docs/validation/check.py --strict
```

需要 Python 3.11+、zsh、fish、luac、git、chezmoi、ssh、sh、tmux、Neovim。
普通运行允许缺少可选解析器时 skipped；`--strict` 将**任何 skipped 视为失败**。

覆盖：

- 每个 Zsh/Fish/Lua 文件逐个语法检查（含 conf.d 六文件、functions/ 惰性函数与
  completions/ 自有补全）；Fish autoload/补全惰性加载的文件名契约
  （functions/<name>.fish 必须定义同名函数、completions/<cmd>.fish 必须
  complete --command <cmd>）；文档列出的 fish functions/conf.d/completions 清单与计数必须与源目录一致；受管配置清单的 JSON/TOML/Git 解析（显式列举的文件，不扫描全仓库）；Git LFS filter 只在 `.gitattributes` 匹配时调用；
- Git 的 Pi 源名 allowlist；`.chezmoiignore` 的 Pi runtime blacklist 覆盖 permission-mode、sessions、npm、missions、tasks、models-store 与 workflows/state fixture，并逐项 mutation-check；`auth.json` 与 credentials 路径由通用敏感路径规则保护。
- 实际渲染的 Zsh/Zim symlink 目标与 private/default 权限契约（不 apply）；`.keep` 占位文件不产生部署目标；
- updater 全参数预检、混合失败、缺失依赖、临时文件失败与 stderr；全部目标缺失（`attempted==0`）时 zsh/fish 均须报“no runnable targets”而非“更新完成”；brew 目标的第三方 `brew cu`（tap `buo/homebrew-cask-upgrade`）不可用时须跳过并提示、不得把 brew 误报为 failed，同时真实 `cu` 失败仍须传播；
- Zsh/Fish yazi 成功/失败/清理/导航（caller 变量哨兵仅 Fish 侧校验）；fish `cdd` 在无 lsd 别名时回退到可移植 `ls`；`uv_resync` 当前为注释模板（未启用），测试仅校验模板存在、启用后自动恢复行为断言；
- fzf 正整数 PID、去重、多选、危险 Ex 行字段、路径选项终止与 ftm 状态；
- SDKMAN 惰性加载、失败不递归、reload 不重复初始化（zsh）；fish 侧 SDKMAN 桩未安装不定义、惰性、经 bass 转发参数；
- completion 冷/热缓存、未来 mtime、同路径降级、NO_CLOBBER、无效生成、编译失败、
  真实 bytecode 消费，以及同/不同二进制的并发加载（不同安装的 stress fixture
  仅把等锁上限延长到 10 秒；另一个检查验证 production 1 秒超时安全跳过）；
- tmux contract stubs 的 cold/reload/能力去重与 XDG/传统/显式路径选择；
- 真实 Neovim 输入的 Insert/Escape/Ctrl-C/Replace/Ctrl-O/Visual、窗口切换、
  augroup 重载及本地 overrides；
- 文档相对链接和 Neovim 架构关键事实；配置文档与实际 proxy、terminal、mise、Pi、Fish shortcut 来源的一致性；bytecode hygiene（每个入口导入项目模块前关闭写字节码，`docs/validation/` 无 `__pycache__`）。

## 历史对照（negative controls）

```sh
python3 docs/validation/negative_controls.py --revision b4e8bac
```

把指定 Git revision 的源码复制到临时目录，运行当前的选定回归。
仅当每个控制都产生**断言失败**、没有 infrastructure errors/skips 时命令成功。
不 checkout、不修改当前 worktree。默认基线为 `b4e8bac`；也可指定包含兼容旧布局源码的其他历史 commit。

## 原生 fzf 行为

```sh
python3 docs/validation/fzf_runtime.py
```

需要 macOS/POSIX PTY 与 fzf；使用不可见的临时控制终端，不是 GUI 自动化。
验证真实 fzf 占位符 quoting、editor 参数以及 plugin-specific Zsh shell 覆盖。

## 实际 tmux 插件版本的离线集成

```sh
python3 docs/validation/tmux_plugins.py \
  --plugin-root ~/.tmux/plugins \
  --tpm-source ~/.config/tmux/plugins/tpm
```

输入目录需包含 Catppuccin 的 `tmux`、`tmux-cpu`、`tmux-battery` 与 TPM。
复制到 disposable HOME 后运行实际 initializer；所有 status collectors 被 stub，
不会主动调用真实 CPU/battery/network 工具。脚本会执行所给插件目录中的代码，
不校验其 Git revision 是否等于 [optimization.md](../optimization.md) 所列
（该表仅为已知良好版本，非自动断言），因此只应传入可信副本；测试只证明这些
输入版本的契约，不能保证所有未来上游版本。

## 终端 parser 与窄场景性能实验

```sh
python3 docs/validation/terminal_parsers.py
python3 docs/validation/benchmark_cache.py --revision b4e8bac
```

前者用本机 Ghostty/kitty parser 校验配置，不开 GUI；后者只测量 stub 二进制
未来 mtime 场景的多次补全加载，报告调用次数和耗时。它**不是**真实 Shell
启动基准，不支持“整体提速百分比”结论。

## 验证边界

不保证插件下载、LSP/registry、网络、GUI、真实 HOME 权限/部署或所有历史工具版本。
HOME 与 destination 必须一起隔离：仓库 SSH 初始化脚本与 symlink 模板使用 HOME，
单改 `chezmoi --destination` 并不构成 apply 沙箱。
