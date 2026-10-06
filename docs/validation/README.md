# 验证与回归

验证只读取仓库源码，使用临时目录、隔离 HOME/XDG 与 stub 命令。**不会**执行
`chezmoi apply`、bootstrap 插件、运行真实更新器/进程 killer 或访问网络。
私有 tmux socket 与 `nvim -u NONE -i NONE -n` 不连接用户现有实例。

## 主要验收入口

```sh
python3 docs/validation/check.py --strict
```

需要 Python 3.11+、zsh、fish、luac、git、chezmoi、sh、tmux、Neovim。
普通运行允许缺少可选解析器时 skipped；`--strict` 将**任何 skipped 视为失败**。

覆盖：

- 每个 Zsh/Fish/Lua 文件逐个语法检查；JSON、TOML、Git 与初始化脚本解析；
- Git 的 Pi 源名 allowlist；含非 JSON、加密/属性前缀与扩展脚本的合成 chezmoi
  部署 fixture，并验证删除 deny 规则确实使测试失效；
- 实际渲染的 Zsh/Zim symlink 目标与 private/default 权限契约（不 apply）；
- updater 全参数预检、混合失败、缺失依赖、临时文件失败与 stderr；
- Zsh/Fish yazi 成功/失败/清理/caller 变量；uv destructive reset 依赖与短路；
- fzf 正整数 PID、去重、多选、危险 Ex 行字段、路径选项终止与 ftm 状态；
- SDKMAN 惰性加载、失败不递归、reload 不重复初始化；
- completion 冷/热缓存、未来 mtime、同路径降级、NO_CLOBBER、无效生成、编译失败、
  真实 bytecode 消费，以及同/不同二进制的并发加载（不同安装的 stress fixture
  仅把等锁上限延长到 10 秒；另一个检查验证 production 1 秒超时安全跳过）；
- tmux contract stubs 的 cold/reload/能力去重与 XDG/传统/显式路径选择；
- 真实 Neovim 输入的 Insert/Escape/Ctrl-C/Replace/Ctrl-O/Visual、窗口切换、
  augroup 重载及本地 overrides；
- 文档相对链接和 Neovim 架构关键事实。

## 历史对照（negative controls）

```sh
python3 docs/validation/negative_controls.py --revision HEAD
```

把指定 Git revision 的源码复制到临时目录，运行当前的选定回归。
仅当每个控制都产生**断言失败**、没有 infrastructure errors/skips 时命令成功。
不 checkout、不修改当前 worktree。可用具体 commit 替代 HEAD 重复实验。

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
不会调用真实 CPU/battery/network 工具。测试只证明这些输入版本的契约，不能
保证所有未来上游版本；具体 revisions 见 [optimization.md](../optimization.md)。

## 终端 parser 与窄场景性能实验

```sh
python3 docs/validation/terminal_parsers.py
python3 docs/validation/benchmark_cache.py --revision HEAD
```

前者用本机 Ghostty/kitty parser 校验配置，不开 GUI；后者只测量 stub 二进制
未来 mtime 场景的多次补全加载，报告调用次数和耗时。它**不是**真实 Shell
启动基准，不支持“整体提速百分比”结论。

## 验证边界

不保证插件下载、LSP/registry、网络、GUI、真实 HOME 权限/部署或所有历史工具版本。
HOME 与 destination 必须一起隔离：仓库 SSH 初始化脚本与 symlink 模板使用 HOME，
单改 `chezmoi --destination` 并不构成 apply 沙箱。
