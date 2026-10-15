#!/usr/bin/env python3
"""Offline source checks and disposable, stubbed dotfiles regression tests.

Requires Python 3.11+. Never applies chezmoi, bootstraps plugins, sources live
HOME configuration, or invokes real updaters, process killers, or network tools.
"""

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import tomllib

# Avoid leaving imported test bytecode inside the chezmoi source tree.
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[2]
ZSH = ROOT / "dot_config/zsh"
FISH = ROOT / "dot_config/fish/conf.d"
FUNCS = ROOT / "dot_config/fish/functions"
FISH_COMPLETIONS = ROOT / "dot_config/fish/completions"


def function_source(path, name, shell="zsh"):
  text = path.read_text()
  if shell == "fish":
    pattern = rf"^function {re.escape(name)}(?:[^\n]*)\n.*?^end$"
  else:
    pattern = rf"^{re.escape(name)}\(\) \{{\n.*?^\}}$"
  match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
  if not match:
    raise AssertionError(f"Cannot extract {name} from {path.relative_to(ROOT)}")
  return match[0] + "\n"


def function_source_optional(path, name, shell="zsh"):
  """Like function_source, but returns None when the definition is absent/commented."""
  try:
    return function_source(path, name, shell)
  except AssertionError:
    return None


class Fixture(unittest.TestCase):
  def sdk_init(self, content):
    """Install a fixture SDKMAN bash init script under the isolated HOME."""
    path = Path(self.env["HOME"]) / ".sdkman/bin/sdkman-init.sh"
    path.parent.mkdir(parents=True)
    path.write_text(content)
  def setUp(self):
    self.temp = tempfile.TemporaryDirectory(prefix="dotfiles-validation-")
    self.addCleanup(self.temp.cleanup)
    self.cwd = Path(self.temp.name)
    self.bin = self.cwd / "bin"
    self.bin.mkdir()
    self.trace = self.cwd / "calls.jsonl"
    home = self.cwd / "home"
    home.mkdir()
    self.env = {
      "HOME": str(home),
      "ZDOTDIR": str(home),
      "XDG_CONFIG_HOME": str(home / ".config"),
      "XDG_DATA_HOME": str(home / ".local/share"),
      "XDG_CACHE_HOME": str(home / ".cache"),
      "XDG_STATE_HOME": str(home / ".local/state"),
      "TMPDIR": str(self.cwd),
      "PATH": f"{self.bin}:/usr/bin:/bin",
      "TERM": "dumb",
      "LC_ALL": "C",
      "TRACE": str(self.trace),
      "PYTHONDONTWRITEBYTECODE": "1",
      "GIT_CONFIG_NOSYSTEM": "1",
      "GIT_CONFIG_GLOBAL": "/dev/null",
      "FZF_DEFAULT_OPTS": "",
    }

  def require(self, tool):
    executable = shutil.which(tool)
    if not executable:
      self.skipTest(f"{tool} is not installed")
    return executable

  def run_command(self, argv, *, script=None, env=None, cwd=None):
    return subprocess.run(
      [str(arg) for arg in argv],
      input=script,
      text=True,
      capture_output=True,
      cwd=cwd or self.cwd,
      env=self.env | (env or {}),
      timeout=20,
      check=False,
    )

  def ok(self, result):
    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
    return result.stdout

  def shell(self, definitions, script, shell="zsh", env=None):
    tool = self.require(shell)
    flags = ["-df"] if shell == "zsh" else ["--no-config", "--private"]
    return self.run_command([tool, *flags], script=definitions + script, env=env)

  def stub(self, name, body="", directory=None):
    path = (directory or self.bin) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
      f"#!{sys.executable}\n"
      "import json, os, sys\nfrom pathlib import Path\n"
      "with open(os.environ['TRACE'], 'a') as trace:\n"
      "    trace.write(json.dumps([Path(sys.argv[0]).name, *sys.argv[1:]]) + '\\n')\n" + body + "\n"
    )
    path.chmod(0o700)
    return path

  def calls(self, name=None):
    calls = [json.loads(line) for line in self.trace.read_text().splitlines()] if self.trace.exists() else []
    return calls if name is None else [call for call in calls if call[0] == name]


class SourceChecks(Fixture):
  def test_zsh_syntax_per_file(self):
    tool = self.require("zsh")
    for path in sorted(ZSH.glob("*.zsh")) + [ZSH / "dot_zshrc", ZSH / "dot_zimrc"]:
      with self.subTest(path=path.name):
        self.ok(self.run_command([tool, "-dfn", path]))

  def test_fish_syntax_per_file(self):
    tool = self.require("fish")
    paths = [
      FISH.parent / "config.fish",
      *sorted(FISH.glob("*.fish")),
      *sorted(FUNCS.glob("*.fish")),
      *sorted(p for p in FISH_COMPLETIONS.glob("*.fish") if not p.name.startswith("symlink_")),
    ]
    for path in paths:
      with self.subTest(path=path.name):
        self.ok(self.run_command([tool, "--no-config", "--no-execute", path]))

  def test_fish_autoload_files_match_filename(self):
    # fish autoload 按文件名解析：functions/<name>.fish 必须定义 function <name>，
    # 否则首次调用报 unknown function（错误从启动时推迟到调用时暴露）；
    # 其余函数定义必须 __ 前缀（随同名函数一起加载的私有 helper）。
    for path in sorted(FUNCS.glob("*.fish")):
      with self.subTest(path=path.name):
        defined = re.findall(r"^function\s+(\S+)", path.read_text(), re.MULTILINE)
        self.assertIn(path.stem, defined)
        strangers = [name for name in defined if name != path.stem and not name.startswith("__")]
        self.assertEqual(strangers, [], "non-private functions need their own <name>.fish for autoload")

  def test_fish_completion_files_target_their_own_command(self):
    # completions/<cmd>.fish 仅在补全 <cmd> 时加载；文件必须 complete --command <cmd>。
    # symlink_* 为指向外部补全的符号链接（内容非 fish 代码），不往本契约。
    for path in sorted(p for p in FISH_COMPLETIONS.glob("*.fish") if not p.name.startswith("symlink_")):
      with self.subTest(path=path.name):
        commands = re.findall(r"--command\s+(\S+)", path.read_text())
        self.assertIn(path.stem, commands)

  def test_ci_workflow_runs_documented_entrypoints(self):
    # CI 与文档共同声明的入口必须一致，避免任一侧漂移。
    workflow = (ROOT / ".github/workflows/ci.yaml").read_text()
    validation_docs = (ROOT / "docs/validation/README.md").read_text()
    for command in (
      "actionlint -color",
      "python3 docs/validation/check.py --strict",
      "python3 docs/validation/fzf_runtime.py",
    ):
      with self.subTest(command=command):
        self.assertIn(command, workflow)
    for token in ("actionlint", "check.py --strict", "fzf_runtime.py"):
      with self.subTest(document="docs/validation/README.md", token=token):
        self.assertIn(token, validation_docs)

  def test_documentation_lists_fish_inventory(self):
    # 文档对 fish functions/、conf.d/、completions/ 的清单与计数必须与实际源文件一致，
    # 防止目录增删后文档漂移。
    functions = sorted(path.stem for path in FUNCS.glob("*.fish"))
    count = len(functions)
    layout = (ROOT / "docs/layout.md").read_text()
    maintenance = (ROOT / "docs/maintenance.md").read_text()
    for document, text in (
      ("docs/layout.md", layout),
      ("docs/maintenance.md", maintenance),
      ("docs/shell.md", (ROOT / "docs/shell.md").read_text()),
      ("README.md", (ROOT / "README.md").read_text()),
    ):
      with self.subTest(document=document):
        self.assertIn(f"{count} 个", text)
    for document, text in (("docs/layout.md", layout), ("docs/maintenance.md", maintenance)):
      for name in functions:
        with self.subTest(document=document, function=name):
          self.assertIn(name, text)
    conf = sorted(path.stem.removeprefix("dot_") for path in FISH.glob("*.fish"))
    self.assertEqual(
      conf,
      ["00_env", "01_activate", "10_sys", "20_dev", "21_k8s", "22_rev"],
    )
    for name in conf:
      with self.subTest(document="docs/layout.md", conf=name):
        self.assertIn(name, layout)
    completions = sorted(path.name for path in FISH_COMPLETIONS.glob("*.fish"))
    self.assertEqual(
      completions,
      ["kubecolor.fish", "symlink_docker.fish", "symlink_kubectl.fish", "symlink_orbctl.fish"],
    )
    for name in completions:
      with self.subTest(document="docs/layout.md", completion=name):
        self.assertIn(name.removeprefix("symlink_"), layout)

  def test_lua_syntax_per_file(self):
    tool = self.require("luac")
    for path in sorted((ROOT / "dot_config/nvim").rglob("*.lua")):
      with self.subTest(path=path.name):
        self.ok(self.run_command([tool, "-p", path]))

  def test_neovim_documentation_contracts(self):
    config = ROOT / "dot_config/nvim"
    doc = (ROOT / "docs/neovim.md").read_text()
    extras = json.loads((config / "lazyvim.json").read_text())["extras"]
    self.assertEqual(len(extras), len(set(extras)))
    self.assertIn(f"{len(extras)} 个 extras", doc)
    for path in sorted((config / "lua/plugins").glob("*.lua")):
      self.assertIn(path.name, doc)
    self.assertIn('colorcolumn = "120"', (config / "lua/config/options.lua").read_text())
    self.assertIn("120 列", doc)
    self.assertEqual((config / "lua/config/keymaps.lua").read_text().count("vim.keymap.set("), 1)
    self.assertIn("唯一的本地映射", doc)

  def test_static_json_toml_and_git_config(self):
    # Parse only managed configurations; never discover/read runtime credentials.
    paths = [
      ROOT / path
      for path in (
        "dot_pi/agent/settings.json",
        "dot_pi/agent/pi-goal.json",
        "dot_pi/agent/extensions/pi-automode/config.json",
        "dot_pi/workflows/settings.json",
        "dot_config/nvim/lazyvim.json",
      )
    ]
    for path in paths:
      with self.subTest(path=path.relative_to(ROOT)):
        json.loads(path.read_text())
    for path in (
      ROOT / "dot_config/mise/config.toml",
      ROOT / "dot_config/alacritty/alacritty.toml",
      ROOT / "dot_config/nvim/stylua.toml",
    ):
      with path.open("rb") as stream:
        tomllib.load(stream)
    self.ok(
      self.run_command([self.require("git"), "config", "--no-includes", "--file", ROOT / "dot_gitconfig", "--list"])
    )

  def test_proxy_documentation_matches_configuration(self):
    git_config = (ROOT / "dot_gitconfig").read_text()
    ssh_config = (ROOT / "private_dot_ssh/private_config").read_text()
    proxy_match = re.search(r"^\s*proxy = socks5h://127\.0\.0\.1:(\d+)$", git_config, re.MULTILINE)
    self.assertIsNotNone(proxy_match)
    proxy_port = proxy_match[1]
    ssh_proxy_match = re.search(
      # 探活可带 -G/-w 超时（见 private_config 注释）；不变式是它与 git 代理端口一致。
      r"^  ProxyCommand bash -c 'if nc -z(?: -G \d+ -w \d+)? 127\.0\.0\.1 (\d+); then nc -X 5 -x 127\.0\.0\.1:(\d+)",
      ssh_config,
      re.MULTILINE,
    )
    self.assertIsNotNone(ssh_proxy_match)
    self.assertEqual(ssh_proxy_match.groups(), (proxy_port, proxy_port))
    zsh_proxy_match = re.search(
      r'local host="127\.0\.0\.1" port=(\d+)', (ROOT / "dot_config/zsh/aliases.zsh").read_text()
    )
    fish_proxy_match = re.search(
      r"set -l proxy_port (\d+)", (ROOT / "dot_config/fish/functions/onproxy.fish").read_text()
    )
    self.assertIsNotNone(zsh_proxy_match)
    self.assertIsNotNone(fish_proxy_match)
    self.assertEqual(zsh_proxy_match[1], proxy_port)
    self.assertEqual(fish_proxy_match[1], proxy_port)
    for relative in (
      "README.md",
      "docs/getting-started.md",
      "docs/dev-tools.md",
      "docs/maintenance.md",
      "docs/layout.md",
    ):
      with self.subTest(document=relative):
        document = (ROOT / relative).read_text()
        self.assertIn(f"127.0.0.1:{proxy_port}", document)
        self.assertNotIn("5376", document)

  def test_terminal_documentation_matches_active_configuration(self):
    ghostty = (ROOT / "dot_config/ghostty/config").read_text()
    ghostty_theme = re.search(r"^theme = (.+)$", ghostty, re.MULTILINE)[1]
    ghostty_command = re.search(r"^command = (.+)$", ghostty, re.MULTILINE)[1]
    terminal_docs = (ROOT / "docs/terminals.md").read_text()
    self.assertIn(ghostty_theme, terminal_docs)
    self.assertIn(ghostty_command, terminal_docs)
    for relative in ("README.md", "docs/layout.md", "docs/shell.md"):
      self.assertIn(ghostty_command, (ROOT / relative).read_text())
    for relative in ("README.md", "docs/layout.md", "docs/terminals.md"):
      self.assertIn(ghostty_theme, (ROOT / relative).read_text())
    for key in ("quick-terminal-animation-duration", "scrollback-limit", "image-storage-limit"):
      active_setting = next(line for line in ghostty.splitlines() if line.startswith(f"{key} ="))
      self.assertIn(active_setting, terminal_docs)
    alacritty_text = (ROOT / "dot_config/alacritty/alacritty.toml").read_text()
    alacritty = tomllib.loads(alacritty_text)
    self.assertIn(alacritty["font"]["normal"]["family"], terminal_docs)
    self.assertNotIn("[[schemas]]", alacritty_text)
    self.assertIn("#:tombi schema.strict = false", terminal_docs)
    self.assertIn("# schema:", terminal_docs)

  def test_tool_and_shell_documentation_matches_sources(self):
    mise = tomllib.loads((ROOT / "dot_config/mise/config.toml").read_text())["tools"]
    labels = {"bun": "Bun", "deno": "Deno", "go": "Go", "node": "Node.js", "pnpm": "pnpm"}
    for relative in ("docs/dev-tools.md", "docs/maintenance.md"):
      document = (ROOT / relative).read_text()
      for tool, version in mise.items():
        with self.subTest(document=relative, tool=tool):
          self.assertIn(labels[tool], document)
          self.assertIn(str(version), document)

    shortcut_groups = (
      "gob gor got gom gomt goi mvnc mvni mvnp mvnt mvnci "
      "pipi pipid pipr pipl pipu pnpi pnpa pnpad pnps pnpt "
      "cb cr ct cc ccl cu redis-cli mongo-local"
    ).split()
    fish_dev = (ROOT / "dot_config/fish/conf.d/20_dev.fish").read_text()
    shortcut_count = sum(
      re.search(rf"^alias {re.escape(name)}=", fish_dev, re.MULTILINE) is not None for name in shortcut_groups
    )
    self.assertEqual(shortcut_count, 29)
    shell_docs = (ROOT / "docs/shell.md").read_text()
    self.assertIn(f"共 {shortcut_count} 个", shell_docs)
    fish_sys = (ROOT / "dot_config/fish/conf.d/10_sys.fish").read_text()
    zsh_aliases = (ROOT / "dot_config/zsh/aliases.zsh").read_text()
    for alias in ("finder", "iterm", "iterm_ghostty"):
      pattern = rf"^[ \t]*alias {re.escape(alias)}="
      self.assertIsNotNone(re.search(pattern, fish_sys, re.MULTILINE))
      self.assertIsNotNone(re.search(pattern, zsh_aliases, re.MULTILINE))
    for alias in ("lt", "fishsource", "cbcopy", "cbpaste"):
      pattern = rf"^[ \t]*alias {re.escape(alias)}="
      self.assertIsNotNone(re.search(pattern, fish_sys, re.MULTILINE))
      self.assertIsNone(re.search(pattern, zsh_aliases, re.MULTILINE))
    self.assertIn("Fish 侧专属；`finder` 与 `iterm*` 两侧均有", shell_docs)
    for source in (fish_sys, zsh_aliases):
      self.assertIsNone(re.search(r"^\s*alias\s+(?:rm|cp|mv)=", source, re.MULTILINE))
    self.assertIn("`-i` 别名都已注释停用", shell_docs)
    self.assertIn("应用别名在非交互 fish 中也定义", shell_docs)
    fish = self.require("fish")
    for relative, alias in (
      ("dot_config/fish/conf.d/20_dev.fish", "redis-cli"),
      ("dot_config/fish/conf.d/21_k8s.fish", "k"),
    ):
      source = shlex.quote(str(ROOT / relative))
      script = f"source {source}; and functions -q {shlex.quote(alias)}; or exit 1\\n"
      self.ok(self.run_command([fish, "--no-config", "--private", "-c", script]))

    zsh_rc = (ROOT / "dot_config/zsh/dot_zshrc").read_text()
    zsh_aliases_text = (ROOT / "dot_config/zsh/aliases.zsh").read_text()
    fish_env_text = (ROOT / "dot_config/fish/conf.d/00_env.fish").read_text()
    self.assertIn('[[ -n "${LANG:-}" ]] || export LANG=zh_CN.UTF-8', zsh_rc)
    self.assertIn('[[ -n "${EDITOR:-}" ]] || export EDITOR=', zsh_aliases_text)
    self.assertIn('[[ -n "${VISUAL:-}" ]] || export VISUAL=', zsh_aliases_text)
    for variable in ("LANG", "EDITOR", "VISUAL"):
      self.assertIn(f'if not set -q {variable}; or test -z "${variable}"', fish_env_text)
    self.assertIn("未设置或为空时设置默认值", shell_docs)
    environment_cases = (
      ({}, "zh_CN.UTF-8|nvim|nvim"),
      ({"LANG": "", "EDITOR": "", "VISUAL": ""}, "zh_CN.UTF-8|nvim|nvim"),
      ({"LANG": "fr_FR.UTF-8", "EDITOR": "vi", "VISUAL": "vim"}, "fr_FR.UTF-8|vi|vim"),
    )
    lang_guard = next(line.strip() for line in zsh_rc.splitlines() if line.strip().startswith('[[ -n "${LANG:-}" ]]'))
    zsh_script = (
      f"{lang_guard}\nsource {shlex.quote(str(ROOT / 'dot_config/zsh/aliases.zsh'))}\n"
      'print -r -- "$LANG|$EDITOR|$VISUAL"\n'
    )
    fish_script = (
      f"source {shlex.quote(str(ROOT / 'dot_config/fish/conf.d/00_env.fish'))}\n"
      'printf \'%s|%s|%s\\n\' "$LANG" "$EDITOR" "$VISUAL"\n'
    )
    for override, expected in environment_cases:
      for shell, executable, script, flags in (
        ("zsh", self.require("zsh"), zsh_script, ["-dfc"]),
        ("fish", self.require("fish"), fish_script, ["--no-config", "--private", "-c"]),
      ):
        with self.subTest(shell=shell, environment=override):
          result = self.run_command([executable, *flags, script], env=override)
          self.assertEqual(self.ok(result).strip(), expected)

    setup_docs = (ROOT / "docs/getting-started.md").read_text()
    maintenance_docs = (ROOT / "docs/maintenance.md").read_text()
    for excluded in (
      ".config/fish/fish_variables",
      ".codex/config.toml",
      ".claude/settings.json",
      ".orca/",
      ".vscode/",
    ):
      self.assertIn(excluded, setup_docs)
      self.assertIn(excluded, maintenance_docs)
    for truthful_statement in (
      "Fish 无条件定义 `k=kubecolor`",
      "不会 source `~/.cargo/env`",
      "普通 Git 仓库操作不依赖 `git-lfs`",
    ):
      self.assertIn(truthful_statement, setup_docs)
    zsh_rc_source = (ROOT / "dot_config/zsh/dot_zshrc").read_text()
    fish_env_source = (ROOT / "dot_config/fish/conf.d/00_env.fish").read_text()
    self.assertIn('[[ -d "$HOME/.cargo/bin"', zsh_rc_source)
    self.assertIn("test -d ~/.cargo/bin; and fish_add_path -g ~/.cargo/bin", fish_env_source)
    self.assertIsNone(re.search(r"^\s*(?:source|\.)\s+.*\.cargo/env", zsh_rc_source, re.MULTILINE))
    self.assertIsNone(re.search(r"^\s*source\s+.*\.cargo/env", fish_env_source, re.MULTILINE))
    zsh_sdk = (ROOT / "dot_config/zsh/sdk.zsh").read_text()
    fish_k8s = (ROOT / "dot_config/fish/conf.d/21_k8s.fish").read_text()
    self.assertIsNotNone(re.search(r"if command -v kubectl[^\n]*; then\s+alias k='kubectl'", zsh_sdk, re.MULTILINE))
    self.assertIn('alias k="kubecolor"', fish_k8s)
    git_lfs = subprocess.check_output(
      [self.require("git"), "config", "--no-includes", "--file", ROOT / "dot_gitconfig", "--get", "filter.lfs.required"],
      text=True,
    ).strip()
    self.assertEqual(git_lfs, "true")
    maintenance_docs = (ROOT / "docs/maintenance.md").read_text()
    self.assertIn("**/*auth.json*", maintenance_docs)
    self.assertIn("**/hosts.yml", maintenance_docs)
    self.assertIn("由 **/*.md 排除", (ROOT / "README.md").read_text())
    validation_docs = (ROOT / "docs/validation/README.md").read_text()
    self.assertIn("chezmoi、ssh、sh", validation_docs)

  def test_pi_workflow_documentation_matches_settings(self):
    pi_workflows = json.loads((ROOT / "dot_pi/workflows/settings.json").read_text())
    self.assertEqual(pi_workflows["defaultEffort"], "off")
    self.assertTrue(pi_workflows["keywordTriggerEnabled"])
    self.assertEqual(pi_workflows["keywordTriggerWord"], "ultracode")
    pi_dev_docs = (ROOT / "docs/dev-tools.md").read_text()
    self.assertIn("`defaultEffort: off`", pi_dev_docs)
    self.assertIn("`ultracode` 是启用的显式关键词触发器", pi_dev_docs)
    pi_docs = pi_dev_docs + (ROOT / "docs/layout.md").read_text()
    for relative in (
      "dot_pi/agent/settings.json",
      "dot_pi/agent/pi-goal.json",
      "dot_pi/agent/extensions/pi-automode/config.json",
      "dot_pi/workflows/settings.json",
    ):
      self.assertIn(relative, pi_docs)

  def test_documented_disabled_and_fallback_states(self):
    # uv_resync 在两个 shell 中均为注释模板，文档必须说明“未启用/禁用”。
    zsh_aliases = (ZSH / "aliases.zsh").read_text()
    fish_dev = (FISH / "20_dev.fish").read_text()
    self.assertIn("# uv_resync() {", zsh_aliases)
    self.assertIn("# function uv_resync", fish_dev)
    self.assertIsNone(re.search(r"^uv_resync\(\)", zsh_aliases, re.MULTILINE))
    self.assertIsNone(re.search(r"^function uv_resync", fish_dev, re.MULTILINE))
    for relative in ("docs/optimization.md", "docs/validation/README.md", "dot_config/zsh/README.md"):
      with self.subTest(document=relative):
        self.assertIsNotNone(
          re.search(r"uv_resync[^\n]*(未启用|禁用|注释模板)", (ROOT / relative).read_text())
        )
    # 三模块是显式 source，不是 glob。
    zshrc = (ROOT / "dot_config/zsh/dot_zshrc").read_text()
    for module in ("aliases.zsh", "fzf.zsh", "sdk.zsh"):
      with self.subTest(module=module):
        self.assertIn(f'source "$HOME/.config/zsh/{module}"', zshrc)
    self.assertNotIn("*.zsh(N)", zshrc)
    self.assertNotIn("*.zsh(N)", (ROOT / "docs/getting-started.md").read_text())
    # 半核并行：优先 nproc，缺失回退 macOS sysctl。
    self.assertIn("sysctl -n hw.ncpu", zsh_aliases)
    self.assertIn("sysctl -n hw.ncpu", (FUNCS / "__half_cpu_count.fish").read_text())
    self.assertIn("sysctl -n hw.ncpu", (ROOT / "docs/getting-started.md").read_text())
    # SSH 权限说明不得声称 0644 被 ssh 拒绝。
    ssh_config = (ROOT / "private_dot_ssh/private_config").read_text()
    self.assertNotIn("0644 被 ssh 拒绝", ssh_config)
    self.assertNotIn("0644 is rejected", ssh_config)
    # onproxy 注释区分六个路由变量与两个 no_proxy 豁免变量。
    onproxy = (FUNCS / "onproxy.fish").read_text()
    self.assertIn("六个路由变量", onproxy)
    self.assertIn("set -gx no_proxy", onproxy)

  def test_git_lfs_filter_only_runs_for_attributed_files(self):
    git = self.require("git")
    self.stub("git-lfs", "sys.exit(23)")
    env = {"GIT_CONFIG_GLOBAL": str(ROOT / "dot_gitconfig"), "GIT_CONFIG_NOSYSTEM": "1"}

    plain_repo = self.cwd / "plain-repo"
    plain_repo.mkdir()
    self.ok(self.run_command([git, "init", "-q"], cwd=plain_repo, env=env))
    (plain_repo / "notes.txt").write_text("ordinary Git file\n")
    self.ok(self.run_command([git, "add", "notes.txt"], cwd=plain_repo, env=env))
    self.assertEqual(self.calls("git-lfs"), [])

    lfs_repo = self.cwd / "lfs-repo"
    lfs_repo.mkdir()
    self.ok(self.run_command([git, "init", "-q"], cwd=lfs_repo, env=env))
    (lfs_repo / ".gitattributes").write_text("*.bin filter=lfs diff=lfs merge=lfs -text\n")
    (lfs_repo / "payload.bin").write_bytes(b"fixture payload")
    result = self.run_command([git, "add", "payload.bin"], cwd=lfs_repo, env=env)
    self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
    self.assertTrue(self.calls("git-lfs"))

  def test_ssh_config_parses(self):
    # `ssh -G` resolves and prints the effective configuration without connecting
    # or executing ProxyCommand. Paths use fixed safe prefixes for known aliases
    # that share endpoints; all other aliases use only OpenSSH's hashed %C token.
    ssh = self.require("ssh")
    config = ROOT / "private_dot_ssh/private_config"
    result = None
    control_paths = []
    prefixes = {
      "tst": "tst",
      "ops": "ops",
      "sec": "sec",
      "github.com": "github",
      "ssh.github.com": "ssh-github",
    }
    for host, prefix in prefixes.items():
      result = self.run_command([ssh, "-G", "-F", config, host])
      self.ok(result)
      options = {line.split(" ", 1)[0]: line.split(" ", 1)[1] for line in result.stdout.splitlines() if " " in line}
      self.assertIn("controlpath", options)
      self.assertRegex(options["controlpath"], rf"^.*/\.ssh/\.cm-{re.escape(prefix)}-[0-9a-f]{{40}}$")
      self.assertEqual(Path(options["controlpath"]).parent.name, ".ssh")
      # OpenSSH may append a temporary random suffix while creating the socket.
      self.assertLess(len(os.fsencode(options["controlpath"])) + 17, 104)
      control_paths.append(options["controlpath"])
    self.assertEqual(len(control_paths), len(set(control_paths)))
    self.assertIn("proxycommand", {line.split(" ", 1)[0] for line in result.stdout.splitlines()})

    traversal = self.run_command([ssh, "-G", "-F", config, "foo/../../tmp/probe"])
    self.ok(traversal)
    options = {line.split(" ", 1)[0]: line.split(" ", 1)[1] for line in traversal.stdout.splitlines() if " " in line}
    self.assertRegex(options["controlpath"], r"^.*/\.ssh/\.cm-[0-9a-f]{40}$")
    self.assertEqual(Path(options["controlpath"]).parent.name, ".ssh")
    self.assertNotIn("..", Path(options["controlpath"]).parts)

  def test_pi_source_allowlist(self):
    git = self.require("git")
    (self.cwd / ".gitignore").write_text((ROOT / ".gitignore").read_text())
    self.ok(self.run_command([git, "init", "-q"]))
    blocked = [
      "dot_pi/agent/auth.json",
      "dot_pi/agent/private_auth.json",
      "dot_pi/agent/encrypted_auth.json.age",
      "dot_pi/agent/mcp.json",
      "dot_pi/agent/private_mcp.json",
      "dot_pi/agent/sessions/example.json",
      "dot_pi/workflows/projects/run.json",
      "dot_pi/agent/npm/package.json",
      "dot_pi/agent/extensions/probe.js",
    ]
    result = self.run_command([git, "check-ignore", "--no-index", "--stdin"], script="\n".join(blocked) + "\n")
    self.ok(result)
    self.assertEqual(result.stdout.splitlines(), blocked)
    for allowed in (
      "dot_pi/agent/settings.json",
      "dot_pi/agent/pi-goal.json",
      "dot_pi/agent/extensions/pi-automode/config.json",
      "dot_pi/workflows/settings.json",
    ):
      with self.subTest(path=allowed):
        result = self.run_command([git, "check-ignore", "--no-index", "-q", allowed])
        self.assertEqual(result.returncode, 1, result.stderr)

  def test_vscode_repository_allowlist(self):
    git = self.require("git")
    (self.cwd / ".gitignore").write_text((ROOT / ".gitignore").read_text())
    self.ok(self.run_command([git, "init", "-q"]))
    for allowed in (".vscode/settings.json", ".vscode/extensions.json"):
      with self.subTest(path=allowed):
        result = self.run_command([git, "check-ignore", "--no-index", "-q", allowed])
        self.assertEqual(result.returncode, 1, result.stderr)
    for blocked in (".vscode/launch.json", "dot_config/.vscode/settings.json"):
      with self.subTest(path=blocked):
        result = self.run_command([git, "check-ignore", "--no-index", "-q", blocked])
        self.assertEqual(result.returncode, 0, result.stderr)

  def test_chezmoi_source_boundaries_without_apply(self):
    tool = self.require("chezmoi")
    config = self.cwd / "empty.toml"
    config.write_text("")
    result = self.run_command(
      [
        tool,
        "--source",
        ROOT,
        "--destination",
        self.env["HOME"],
        "--config",
        config,
        "--persistent-state",
        self.cwd / "state.boltdb",
        "managed",
      ]
    )
    targets = set(self.ok(result).splitlines())
    ignored_result = self.run_command(
      [
        tool,
        "--source",
        ROOT,
        "--destination",
        self.env["HOME"],
        "--config",
        config,
        "--persistent-state",
        self.cwd / "state.boltdb",
        "ignored",
      ]
    )
    ignored = set(self.ok(ignored_result).splitlines())
    pi_files = {path for path in targets if path.startswith(".pi/") and path.endswith(".json")}
    self.assertEqual(
      pi_files,
      {
        ".pi/agent/settings.json",
        ".pi/agent/pi-goal.json",
        ".pi/agent/extensions/pi-automode/config.json",
        ".pi/workflows/settings.json",
      },
    )
    self.assertFalse(any(path == "docs" or path.startswith("docs/") for path in targets))
    self.assertFalse(any(path.endswith("README.md") for path in targets))
    self.assertFalse(any(path == ".vscode" or path.startswith(".vscode/") for path in targets))
    self.assertFalse(any(path.endswith("/.keep") for path in targets | ignored))
    self.assertNotIn(".pi/agent/permission-mode", targets)
    self.assertIn(".pi/agent/permission-mode", ignored)
    self.assertFalse(any(path == ".vscode" or path.startswith(".vscode/") for path in ignored))
    self.assertFalse(any(path == ".orca" or path.startswith(".orca/") for path in targets | ignored))
    self.assertIn(".codex/config.toml", ignored)
    self.assertNotIn(".codex/config.toml", targets)
    self.assertNotIn(".config/kitty/kitty.local.conf", targets)
    self.assertIn(".zshrc", targets)
    self.assertIn(".zimrc", targets)

  def test_synthetic_pi_runtime_data_is_excluded_and_rules_are_necessary(self):
    source = self.cwd / "source"
    source.mkdir()
    ignore = source / ".chezmoiignore"
    rules = (ROOT / ".chezmoiignore").read_text()
    ignore.write_text(rules)
    fixtures = (
      "dot_pi/agent/settings.json",
      "dot_pi/agent/pi-goal.json",
      "dot_pi/agent/extensions/pi-automode/config.json",
      "dot_pi/workflows/settings.json",
      "dot_pi/agent/auth.json",
      "dot_pi/agent/permission-mode/custom.json",
      "dot_pi/agent/private_private-auth.json",
      "dot_pi/agent/encrypted_encrypted-auth.json.age",
      "dot_pi/agent/sessions/transcript.jsonl",
      "dot_pi/agent/npm/package.json",
      "dot_pi/agent/missions/run.json",
      "dot_pi/agent/tasks/run.json",
      "dot_pi/agent/credentials/provider.json",
      "dot_pi/agent/models-store/state.json",
      "dot_pi/workflows/state/run.json",
      "dot_pi/agent/extensions/probe.js",
      "dot_pi/agent/private_mcp.json",
      "dot_pi/workflows/projects/state.txt",
      "dot_vscode/settings.json",
      "dot_orca/state.json",
    )
    for name in fixtures:
      path = source / name
      path.parent.mkdir(parents=True, exist_ok=True)
      path.write_text("{}")
    config = self.cwd / "empty.toml"
    config.write_text("")
    argv = [
      self.require("chezmoi"),
      "--source",
      source,
      "--destination",
      self.env["HOME"],
      "--config",
      config,
      "--persistent-state",
      self.cwd / "state.boltdb",
      "managed",
    ]
    targets = set(self.ok(self.run_command(argv)).splitlines())
    # 黑名单策略：仅运行时数据被排除；其余源文件（含 extensions 探针）按设计部署。
    expected = {
      ".pi",
      ".pi/agent",
      ".pi/agent/extensions",
      ".pi/agent/extensions/pi-automode",
      ".pi/workflows",
      ".pi/workflows/projects",
      ".pi/agent/settings.json",
      ".pi/agent/pi-goal.json",
      ".pi/agent/extensions/pi-automode/config.json",
      ".pi/agent/extensions/probe.js",
      ".pi/agent/mcp.json",
      ".pi/workflows/settings.json",
      ".pi/workflows/projects/state.txt",
    }
    self.assertEqual(targets, expected)
    # Mutation control: the same fixture must expose runtime files without the deny rules.
    ignore.write_text("".join(line + "\n" for line in rules.splitlines() if not line.startswith(".pi/")))
    mutated = set(self.ok(self.run_command(argv)).splitlines())
    self.assertNotEqual(mutated, expected)
    self.assertIn(".pi/agent/sessions/transcript.jsonl", mutated)
    for target in (
      ".pi/agent/npm/package.json",
      ".pi/agent/missions/run.json",
      ".pi/agent/tasks/run.json",
      ".pi/agent/models-store/state.json",
      ".pi/workflows/state/run.json",
    ):
      self.assertIn(target, mutated)
    # Auth-named and credentials paths remain excluded by the global sensitive-name rules.
    for sensitive_target in (
      ".pi/agent/auth.json",
      ".pi/agent/private-auth.json",
      ".pi/agent/encrypted-auth.json.age",
      ".pi/agent/credentials/provider.json",
    ):
      self.assertNotIn(sensitive_target, mutated)

    # Each Pi-only runtime rule must exclude its own fixture. The credentials
    # directory is intentionally covered by the separate global sensitive-name guard.
    required_rules = (
      (".pi/agent/permission-mode", ".pi/agent/permission-mode/custom.json"),
      (".pi/agent/sessions/**", ".pi/agent/sessions/transcript.jsonl"),
      (".pi/agent/npm/**", ".pi/agent/npm/package.json"),
      (".pi/agent/missions/**", ".pi/agent/missions/run.json"),
      (".pi/agent/tasks/**", ".pi/agent/tasks/run.json"),
      (".pi/agent/models-store/**", ".pi/agent/models-store/state.json"),
      (".pi/workflows/state/**", ".pi/workflows/state/run.json"),
    )
    for rule, target in required_rules:
      with self.subTest(rule=rule):
        ignore.write_text("".join(line + "\n" for line in rules.splitlines() if line != rule))
        without_rule = set(self.ok(self.run_command(argv)).splitlines())
        self.assertIn(target, without_rule)

  def test_no_unexpected_top_level_deploy_target(self):
    """Adding a root-level source that renders into $HOME must be a conscious change.

    The deploy boundary is a name blacklist (see .chezmoiignore's own comment), so today
    nothing fails if a maintainer adds a root `scripts/` or `pyproject.toml`: chezmoi matches
    by TARGET name and a non-dot source name renders straight into $HOME. Pin the exact set of
    depth-1 managed targets so such an addition fails until reviewed. Note `.github/` is absent
    only because its source name starts with a dot — an implicit invariant no other test states.
    """
    config = self.cwd / "empty.toml"
    config.write_text("")
    argv = [
      self.require("chezmoi"),
      "--source",
      ROOT,
      "--destination",
      self.env["HOME"],
      "--config",
      config,
      "--persistent-state",
      self.cwd / "state.boltdb",
      "managed",
    ]
    top_level = {line.split("/", 1)[0] for line in self.ok(self.run_command(argv)).splitlines()}
    self.assertEqual(
      top_level,
      {
        ".codex",
        ".config",
        ".gitconfig",
        ".gitignore_global",
        ".pi",
        ".ssh",
        ".tmux.conf",
        ".zimrc",
        ".zshrc",
      },
      "根级部署目标集变了：请确认新条目确实应渲染进 $HOME（否则加入 .chezmoiignore 或改为 dot_ 源名）",
    )
    self.assertNotIn(".github", top_level)

  def test_hygiene_rules_exclude_nested_targets(self):
    """.chezmoiignore patterns are anchored to the source root.

    A bare pattern such as `node_modules/` never matches `.config/*/node_modules/`;
    only the `**/` form reaches nested targets. This is the failure the file's own
    comment warns about, and it shipped: `**.log` excluded nothing (so a nested
    `*.log` would be rendered into $HOME) and `node_modules/` / `.pnpm-store/`
    were root-anchored. Each fixture below sits at depth >= 2 on purpose — a
    root-anchored rule leaves it in `managed` and fails the assertion.
    """
    source = self.cwd / "source"
    source.mkdir()
    ignore = source / ".chezmoiignore"
    rules = (ROOT / ".chezmoiignore").read_text()
    ignore.write_text(rules)
    # (rule as written in .chezmoiignore, nested source fixture, expected target)
    excluded = (
      ("**/*.local", "dot_config/nested/keep.local", ".config/nested/keep.local"),
      ("**/*.local.*", "dot_config/nested/keep.local.conf", ".config/nested/keep.local.conf"),
      ("**/*.bak", "dot_config/nested/keep.bak", ".config/nested/keep.bak"),
      ("**/*.log*", "dot_config/nested/run.log", ".config/nested/run.log"),
      ("**/*.log*", "dot_config/nested/run.log.1", ".config/nested/run.log.1"),
      ("**/*.md", "dot_config/nested/notes.md", ".config/nested/notes.md"),
      ("**/LICENSE", "dot_config/nested/LICENSE", ".config/nested/LICENSE"),
      ("**/*token*", "dot_config/nested/my-token.txt", ".config/nested/my-token.txt"),
      ("**/*secret*", "dot_config/nested/db.secret", ".config/nested/db.secret"),
      ("**/*credential*", "dot_config/nested/key.credential", ".config/nested/key.credential"),
      ("**/*auth.json*", "dot_config/nested/auth.json", ".config/nested/auth.json"),
      ("**/hosts.yml", "dot_config/nested/hosts.yml", ".config/nested/hosts.yml"),
      ("**/node_modules/", "dot_config/nested/node_modules/dep.js", ".config/nested/node_modules/dep.js"),
      ("**/.pnpm-store/", "dot_config/nested/dot_pnpm-store/state.json", ".config/nested/.pnpm-store/state.json"),
      ("**/.DS_Store", "dot_config/nested/dot_DS_Store", ".config/nested/.DS_Store"),
    )
    for _, fixture, _ in excluded:
      path = source / fixture
      path.parent.mkdir(parents=True, exist_ok=True)
      path.write_text("{}")
    # Positive control: an ordinary config file must still deploy, so a rule that
    # over-matched could not pass this test by excluding everything.
    (source / "dot_config/nested/keep.conf").write_text("ok\n")
    config = self.cwd / "empty.toml"
    config.write_text("")
    argv = [
      self.require("chezmoi"),
      "--source",
      source,
      "--destination",
      self.env["HOME"],
      "--config",
      config,
      "--persistent-state",
      self.cwd / "state.boltdb",
      "managed",
    ]
    targets = set(self.ok(self.run_command(argv)).splitlines())
    self.assertIn(".config/nested/keep.conf", targets)
    for rule, _, target in excluded:
      with self.subTest(rule=rule, target=target):
        self.assertNotIn(target, targets)
    # Mutation control: dropping the rule must expose its fixture, proving that
    # rule (not another pattern) is what excludes it.
    for rule, _, target in excluded:
      with self.subTest(rule=rule, mutation="drop"):
        ignore.write_text("".join(line + "\n" for line in rules.splitlines() if line != rule))
        without_rule = set(self.ok(self.run_command(argv)).splitlines())
        self.assertIn(target, without_rule)

  def test_ignore_patterns_are_globstar_prefixed_or_intentionally_rooted(self):
    """Invariant, not enumeration: no *new* root-anchored pattern can slip in.

    test_hygiene_rules_exclude_nested_targets proves a fixed set of rules works, but a
    maintainer who later adds e.g. `build/` or `*.tmp` (root-anchored, silently missing
    nested targets) gets no signal — the failure class this repo has now hit three times.
    This test derives its expectation from the real file: every pattern must either start
    with `**/` (matches at any depth) or appear in ROOT_ANCHORED below, each of which is a
    deliberate exact-path target. A new slashless/bare pattern fails until it is either
    fixed to `**/...` or consciously allow-listed here.
    """
    # Patterns that are CORRECTLY anchored at a fixed source path (not name-anywhere rules):
    # the Pi runtime blacklist, the repo-only docs/ dir, and exact machine-local config paths.
    ROOT_ANCHORED = {
      ".pi/agent/permission-mode",
      ".pi/agent/sessions/**",
      ".pi/agent/npm/**",
      ".pi/agent/missions/**",
      ".pi/agent/tasks/**",
      ".pi/agent/models-store/**",
      ".pi/workflows/state/**",
      "docs/",
      ".config/fish/fish_variables",
      ".codex/config.toml",
      ".claude/settings.json",
    }
    patterns = [
      line.strip()
      for line in (ROOT / ".chezmoiignore").read_text().splitlines()
      if line.strip() and not line.strip().startswith("#")
    ]
    for pattern in patterns:
      if pattern.startswith("**/") or pattern in ROOT_ANCHORED:
        continue
      with self.subTest(pattern=pattern):
        self.fail(
          f".chezmoiignore 模式 {pattern!r} 不以 `**/` 开头：它会锚定源根、对嵌套目标静默失效"
          f"（历史已发生三次）。若确为固定路径锚定，请加入本测试的 ROOT_ANCHORED 集合。"
        )
    # Guard the allowlist itself against rot: an entry that no longer exists in the file
    # means this test is silently excusing nothing.
    self.assertTrue(ROOT_ANCHORED <= set(patterns), "ROOT_ANCHORED 含已不存在的模式")

  def test_chezmoi_rendered_symlinks_and_permission_contracts(self):
    config = self.cwd / "empty.toml"
    config.write_text("")
    result = self.run_command(
      [
        self.require("chezmoi"),
        "--source",
        ROOT,
        "--destination",
        self.env["HOME"],
        "--config",
        config,
        "--persistent-state",
        self.cwd / "state.boltdb",
        "dump",
        "--format=json",
      ]
    )
    targets = json.loads(self.ok(result))
    for name in ("zshrc", "zimrc"):
      self.assertEqual(targets[f".{name}"]["type"], "symlink")
      self.assertEqual(targets[f".{name}"]["linkname"], f"{self.env['HOME']}/.config/zsh/.{name}")
    for name, mode in (
      (".config", 0o755),
      (".config/fish", 0o755),
      (".ssh", 0o700),
      (".ssh/config", 0o600),
      (".pi", 0o755),
      (".pi/agent/settings.json", 0o644),
    ):
      with self.subTest(path=name):
        self.assertEqual(targets[name]["perm"], mode)

  def test_relative_documentation_links_exist(self):
    paths = [
      ROOT / "README.md",
      *sorted((ROOT / "docs").rglob("*.md")),
      ZSH / "README.md",
      ROOT / "dot_config/nvim/README.md",
    ]
    checked = 0
    for path in paths:
      for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text()):
        if re.match(r"[a-zA-Z]+:", target) or target.startswith("#"):
          continue
        target = target.split("#", 1)[0]
        with self.subTest(document=path.relative_to(ROOT), target=target):
          self.assertTrue((path.parent / target).exists())
          checked += 1
    self.assertGreater(checked, 50)

  def test_validation_modules_suppress_bytecode_and_stay_clean(self):
    validation = ROOT / "docs/validation"
    guard = "sys.dont_write_bytecode = True"
    project_import = re.compile(r"^[ \t]*(?:import|from)\s+(?:check|runtime_checks)\b", re.MULTILINE)
    for path in sorted(validation.glob("*.py")):
      if path.name == "runtime_checks.py":
        continue  # library module; only imported by scripts that set the guard first
      with self.subTest(script=path.name):
        text = path.read_text()
        self.assertIn(guard, text)
        imported = project_import.search(text)
        self.assertIsNotNone(imported, f"{path.name} should import a project module")
        self.assertLess(
          text.index(guard),
          imported.start(),
          f"{path.name} must disable bytecode before importing a project module",
        )
    self.assertFalse((validation / "__pycache__").exists(), "docs/validation must not contain __pycache__")


class ZshHelpers(Fixture):
  def updater(self):
    return function_source(ZSH / "aliases.zsh", "update-all")

  def test_update_preflight_and_caller_variable(self):
    self.stub("uv")
    result = self.shell(self.updater(), 'name=sentinel\nupdate-all uv typo\nrc=$?\nprint -r -- "$rc:$name"\n')
    self.ok(result)
    self.assertIn("1:sentinel", result.stdout)
    self.assertEqual(self.calls(), [])

  def test_update_mixed_results_and_stderr(self):
    self.stub("uv", "print('upgrade failed', file=sys.stderr)\nsys.exit(23)")
    self.stub("mise")
    result = self.shell(self.updater(), "update-all uv mise pi\n")
    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
    self.assertEqual(self.calls(), [["uv", "tool", "upgrade", "--all"], ["mise", "upgrade"]])
    self.assertIn("1/2 target(s) failed", result.stdout)
    self.assertIn("upgrade failed", result.stdout)
    self.assertIn("pi not found", result.stdout)
    self.assertEqual(list(self.cwd.glob("update-all.*")), [])

  def test_update_allocation_failure_does_not_run_target(self):
    self.stub("uv")
    self.stub("mktemp", "sys.exit(23)")
    result = self.shell(self.updater(), "update-all uv\n")
    self.assertEqual(result.returncode, 1)
    self.assertEqual(self.calls("uv"), [])
    self.assertIn("Cannot allocate stderr file", result.stderr)

  def brew_stub(self, with_cu):
    """A brew whose `commands` output advertises (or omits) the tap-provided `cu`."""
    listed = "install\\nlist\\nupgrade\\ncleanup" + ("\\ncu" if with_cu else "")
    self.stub(
      "brew",
      f"if sys.argv[1] == 'commands':\n    print('{listed}')\n    raise SystemExit(0)\n"
      f"if sys.argv[1] == 'cu':\n    raise SystemExit(1 if not {with_cu!r} else 0)\n"
      "raise SystemExit(0)",
    )

  def test_update_brew_tolerates_missing_cask_upgrade_tap(self):
    # `brew cu` 由第三方 tap（buo/homebrew-cask-upgrade）提供，不在 brew 核心内。原先把它硬接进
    # && 链：未装该 tap 时 `brew cu` 返回非零 → 整条链短路 → brew 被误报为失败，且 cleanup 被跳过。
    self.brew_stub(with_cu=False)
    result = self.shell(self.updater(), "update-all brew\n")
    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
    self.assertIn("✓ brew done", result.stdout)
    self.assertIn("brew cu 不可用", result.stderr)
    self.assertNotIn(["brew", "cu", "-y", "-a"], self.calls("brew"))
    self.assertIn(["brew", "cleanup", "--prune=all"], self.calls("brew"))

  def test_update_brew_runs_cask_upgrade_when_tap_is_present(self):
    self.brew_stub(with_cu=True)
    result = self.shell(self.updater(), "update-all brew\n")
    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
    self.assertIn(["brew", "cu", "-y", "-a"], self.calls("brew"))

  def test_update_brew_propagates_a_real_cask_upgrade_failure(self):
    # 探测命中但 `brew cu` 真的失败时必须照旧计入失败，不能被守卫吞掉。
    self.stub(
      "brew",
      "if sys.argv[1] == 'commands':\n    print('install\\ncu')\n    raise SystemExit(0)\n"
      "if sys.argv[1] == 'cu':\n    sys.exit(23)\n"
      "raise SystemExit(0)",
    )
    result = self.shell(self.updater(), "update-all brew\n")
    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
    self.assertIn("✗ brew failed", result.stdout)

  def test_yazi_failure_cleanup_and_trap_preservation(self):
    self.stub("yazi", "sys.exit(23)")
    definition = function_source(ZSH / "aliases.zsh", "y")
    result = self.shell(
      definition,
      "trap 'true' INT TERM HUP\nbefore=$(trap)\ny\nrc=$?\nafter=$(trap)\n[[ $before == $after ]] || exit 91\nprint -r -- $rc\n",
    )
    self.assertEqual(self.ok(result).strip(), "23")
    cwd_file = self.calls("yazi")[0][-1].split("=", 1)[1]
    self.assertTrue(Path(cwd_file).is_relative_to(self.cwd))
    self.assertFalse(Path(cwd_file).exists())

  def test_yazi_navigation_and_no_change_are_successful(self):
    destination = self.cwd / "directory with spaces"
    destination.mkdir()
    self.stub("yazi", "Path(sys.argv[-1].split('=', 1)[1]).write_bytes(os.environ['DEST'].encode() + b'\\0')")
    result = self.shell(
      function_source(ZSH / "aliases.zsh", "y"), 'y || exit $?\nprint -r -- "$PWD"\ny\n', env={"DEST": str(destination)}
    )
    self.assertEqual(self.ok(result).strip(), str(destination))
    for call in self.calls("yazi"):
      self.assertFalse(Path(call[-1].split("=", 1)[1]).exists())

  def test_yazi_allocation_failure_does_not_launch(self):
    self.stub("mktemp", "sys.exit(23)")
    self.stub("yazi")
    result = self.shell(function_source(ZSH / "aliases.zsh", "y"), "y\n")
    self.assertEqual(result.returncode, 23)
    self.assertEqual(self.calls("yazi"), [])

  def setup_lsof(self):
    self.stub("lsof", "print('COMMAND PID USER')")
    self.stub("fzf", "print(os.environ.get('SELECTION', ''), end='')\nsys.exit(int(os.environ.get('FZF_STATUS', '0')))")
    return (
      function_source(ZSH / "fzf.zsh", "flkill")
      + 'LSOF_PREVIEW="preview"\nkill() { printf "%s\\n" "$@" > "$KILL_LOG"; return ${KILL_STATUS:-0}; }\n'
    )

  def test_flkill_multiselect_is_validated_and_deduplicated(self):
    log = self.cwd / "kill-args"
    result = self.shell(
      self.setup_lsof(), "flkill\n", env={"SELECTION": "a 123 u\nb 456 u\nc 123 u\n", "KILL_LOG": str(log)}
    )
    self.ok(result)
    self.assertEqual(log.read_text().splitlines(), ["-9", "--", "123", "456"])
    self.assertIn("--header-lines=1", self.calls("fzf")[0])

  def test_flkill_invalid_selection_never_kills(self):
    definitions = self.setup_lsof()
    for invalid in ("COMMAND PID USER", "a -1 u", "a 0 u", "a nope u", "a 123 u\nb invalid u"):
      with self.subTest(selection=invalid):
        log = self.cwd / "kill-args"
        result = self.shell(definitions, "flkill\n", env={"SELECTION": invalid, "KILL_LOG": str(log)})
        self.assertEqual(result.returncode, 1)
        self.assertFalse(log.exists())

  def test_flkill_cancellation_empty_and_kill_failure(self):
    definitions = self.setup_lsof()
    log = self.cwd / "kill-args"
    for status in ("0", "130"):
      self.ok(self.shell(definitions, "flkill\n", env={"FZF_STATUS": status, "KILL_LOG": str(log)}))
      self.assertFalse(log.exists())
    result = self.shell(
      definitions, "flkill\n", env={"SELECTION": "a 123 u", "KILL_LOG": str(log), "KILL_STATUS": "17"}
    )
    self.assertEqual(result.returncode, 17)

  def test_frg_uses_shell_quoted_placeholders_and_option_terminators(self):
    self.stub("rg", "print('one file.txt:12:needle')")
    self.stub("fzf", "sys.stdin.read()")
    definition = function_source(ZSH / "fzf.zsh", "frg")
    self.ok(self.shell(definition, "frg needle 'one file.txt'\n"))
    self.assertIn("--with-filename", self.calls("rg")[0])
    self.assertIn("--no-heading", self.calls("rg")[0])
    args = self.calls("fzf")[0]
    preview = args[args.index("--preview") + 1]
    binding = args[args.index("--bind") + 1]
    self.assertNotIn("'{1}'", preview + binding)
    editor = binding.removeprefix("enter:execute(").removesuffix(")+abort")
    self.stub("bat")
    self.stub("nvim")
    for filename in ("two words.txt", "it's.txt", "a; echo danger.txt", "-leading.txt"):
      with self.subTest(filename=filename):
        for template in (preview, editor):
          command = template.replace("{1}", shlex.quote(filename)).replace("{2}", shlex.quote("12"))
          self.ok(self.run_command(["/bin/sh", "-c", command]))
        self.assertEqual(self.calls("bat")[-1][-2:], ["--", filename])
        self.assertEqual(self.calls("nvim")[-1][1:], ["+12", "--", filename])

  def test_lsof_preview_needs_no_awk_subprocess(self):
    source = (ZSH / "fzf.zsh").read_text()
    template = re.search(r"^LSOF_PREVIEW='([^']*)'$", source, re.MULTILINE)[1]
    self.stub("ps")
    self.stub("awk", "sys.exit(91)")
    self.ok(self.run_command(["/bin/sh", "-c", template.replace("{2}", shlex.quote("123"))]))
    self.assertEqual(self.calls("ps"), [["ps", "-fp", "123"]])
    self.assertEqual(self.calls("awk"), [])


class FzfPrefix(Fixture):
  def setUp(self):
    super().setUp()
    self.arm = self.cwd / "arm"
    self.intel = self.cwd / "intel"
    self.linux = self.cwd / "linux"
    self.manual = Path(self.env["HOME"]) / ".fzf"
    source = (ZSH / "fzf.zsh").read_text()
    start = source.index("FZF_PREFIX_CACHE=")
    end = source.index("# 唯一初始化点")
    self.probe = source[start:end]
    # Replace only installation constants, not the discovery algorithm;
    # never create/remove files in the real Homebrew prefix.
    for original, replacement in (
      ("/opt/homebrew/opt/fzf", self.arm),
      ("/usr/local/opt/fzf", self.intel),
      ("/usr/bin/fzf", self.linux / "bin/fzf"),
    ):
      self.probe = self.probe.replace(original, str(replacement))
    self.probe = self.probe.replace('FZF_PREFIX="/usr"', f'FZF_PREFIX="{self.linux}"')
    self.prefix_cache = Path(self.env["HOME"]) / ".cache/zsh/fzf_prefix"
    self.prefix_cache.parent.mkdir(parents=True, exist_ok=True)

  def test_incomplete_preferred_installation_is_skipped_and_path_is_unique(self):
    (self.arm / "bin").mkdir(parents=True)
    self.stub("fzf", directory=self.intel / "bin")
    script = "setopt NO_CLOBBER\n" + self.probe + self.probe + 'print -r -- "$FZF_PREFIX"\nprint -r -- "$PATH"\n'
    lines = self.ok(self.shell("", script)).splitlines()
    self.assertEqual(lines[0], str(self.intel))
    self.assertEqual(lines[1].split(":").count(str(self.intel / "bin")), 1)
    self.assertEqual(self.prefix_cache.read_text().strip(), str(self.intel))
    self.assertEqual(self.calls("fzf"), [])

  def test_invalid_cache_self_heals_and_manual_installation_works(self):
    self.prefix_cache.write_text(str(self.arm))
    self.stub("fzf", directory=self.manual / "bin")
    result = self.shell("", self.probe + 'print -r -- "$FZF_PREFIX"\n')
    self.assertEqual(self.ok(result).strip(), str(self.manual))
    self.assertEqual(self.prefix_cache.read_text().strip(), str(self.manual))

  def test_valid_cache_retains_priority_over_other_installations(self):
    self.stub("fzf", directory=self.arm / "bin")
    self.stub("fzf", directory=self.manual / "bin")
    self.prefix_cache.write_text(str(self.manual))
    result = self.shell("", self.probe + 'print -r -- "$FZF_PREFIX"\n')
    self.assertEqual(self.ok(result).strip(), str(self.manual))

  def test_absent_installation_does_not_write_empty_cache_or_modify_path(self):
    result = self.shell("", "before=$PATH\n" + self.probe + "[[ $PATH == $before && -z ${FZF_PREFIX:-} ]]\n")
    self.ok(result)
    self.assertFalse(self.prefix_cache.exists())


class CompletionCache(Fixture):
  def setUp(self):
    super().setUp()
    self.cache = self.cwd / "cache"
    self.binary = self.stub(
      "docker",
      "sys.stdout.write(os.environ.get('COMPLETION_SCRIPT', 'typeset -g COMPLETION_LOADED=first\\n'))\nsys.exit(int(os.environ.get('GEN_STATUS', '0')))",
    )
    self.definitions = (
      function_source(ZSH / "sdk.zsh", "_load_cached_completion")
      + 'compdef() { :; }\n_ZSH_CACHE_DIR="$CACHE"\nsetopt NO_CLOBBER\n'
    )
    self.env["CACHE"] = str(self.cache)

  def test_cold_and_warm_cache_only_generate_once(self):
    result = self.shell(
      self.definitions,
      '_load_cached_completion docker\n_load_cached_completion docker\nprint -r -- "$COMPLETION_LOADED"\n',
    )
    self.assertEqual(self.ok(result).strip(), "first")
    self.assertEqual(self.calls("docker"), [["docker", "completion", "zsh"]])
    self.assertEqual(len(list(self.cache.iterdir())), 3)
    self.assertTrue((self.cache / "docker-completion.zsh.lock").exists())
    # Reload in a fresh shell: compiled temporary filenames must not break loading.
    result = self.shell(self.definitions, '_load_cached_completion docker\nprint -r -- "$COMPLETION_LOADED"\n')
    self.assertEqual(self.ok(result).strip(), "first")
    self.assertEqual(len(self.calls("docker")), 1)

  def test_concurrent_same_binary_refresh_keeps_complete_cache(self):
    self.stub(
      "docker", "import time\nprint('typeset -g COMPLETION_LOADED=concurrent')\nsys.stdout.flush()\ntime.sleep(0.1)"
    )
    executable = self.require("zsh")
    script = self.definitions + '_load_cached_completion docker\nprint -r -- "$COMPLETION_LOADED"\n'
    jobs = [
      subprocess.Popen(
        [executable, "-dfc", script],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=self.cwd,
        env=self.env,
      )
      for _ in range(4)
    ]
    try:
      for job in jobs:
        stdout, stderr = job.communicate(timeout=20)
        self.assertEqual(job.returncode, 0, stderr)
        # Production deliberately skips completion loading after a 1-second lock
        # timeout. Under load, an empty result is safe; the final fresh process
        # below must still consume the fully published cache.
        self.assertIn(stdout.strip(), ("", "concurrent"), stderr)
    finally:
      for job in jobs:
        if job.poll() is None:
          job.kill()
          job.wait()
    self.assertEqual(
      {path.name for path in self.cache.iterdir()},
      {"docker-completion.zsh", "docker-completion.zsh.zwc", "docker-completion.zsh.lock"},
    )
    self.assertEqual(len(self.calls("docker")), 1)
    self.ok(self.run_command([executable, "-dfn", self.cache / "docker-completion.zsh"]))
    result = self.shell(self.definitions, '_load_cached_completion docker\nprint -r -- "$COMPLETION_LOADED"\n')
    self.assertEqual(self.ok(result).strip(), "concurrent")

  def test_refresh_under_no_clobber(self):
    self.ok(self.shell(self.definitions, "_load_cached_completion docker\n"))
    os.utime(self.binary, (time.time() + 2, time.time() + 2))
    result = self.shell(
      self.definitions,
      '_load_cached_completion docker\nprint -r -- "$COMPLETION_LOADED"\n',
      env={"COMPLETION_SCRIPT": "typeset -g COMPLETION_LOADED=second\n"},
    )
    self.assertEqual(self.ok(result).strip(), "second")
    self.assertEqual(len(self.calls("docker")), 2)

  def test_failure_empty_and_invalid_output_preserve_existing_cache(self):
    self.ok(self.shell(self.definitions, "_load_cached_completion docker\n"))
    cache = self.cache / "docker-completion.zsh"
    original = cache.read_bytes()
    os.utime(self.binary, (time.time() + 2, time.time() + 2))
    cases = ({"GEN_STATUS": "23"}, {"COMPLETION_SCRIPT": ""}, {"COMPLETION_SCRIPT": "if then\n"})
    for env in cases:
      with self.subTest(env=env):
        self.ok(self.shell(self.definitions, "_load_cached_completion docker\n", env=env))
        self.assertEqual(cache.read_bytes(), original)
        self.assertEqual(
          {p.name for p in self.cache.iterdir()}, {cache.name, cache.name + ".zwc", cache.name + ".lock"}
        )

  def test_compiled_cache_is_actually_used_after_atomic_publication(self):
    self.ok(self.shell(self.definitions, "_load_cached_completion docker\n"))
    cache = self.cache / "docker-completion.zsh"
    header = cache.read_text().splitlines()[0]
    cache.write_text(header + "\ntypeset -g COMPLETION_LOADED=text_not_bytecode\n")
    os.utime(cache, (1, 1))
    result = self.shell(self.definitions, '_load_cached_completion docker\nprint -r -- "$COMPLETION_LOADED"\n')
    self.assertEqual(self.ok(result).strip(), "first")
    self.assertEqual(len(self.calls("docker")), 1)

  def test_compilation_failure_falls_back_to_source(self):
    definitions = self.definitions + "zcompile() { return 23; }\n"
    result = self.shell(definitions, '_load_cached_completion docker\nprint -r -- "$COMPLETION_LOADED"\n')
    self.assertEqual(self.ok(result).strip(), "first")
    self.assertFalse((self.cache / "docker-completion.zsh.zwc").exists())
    self.ok(self.shell(definitions, "_load_cached_completion docker\n"))
    self.assertEqual(len(self.calls("docker")), 1)

  def test_concurrent_different_installations_load_their_own_completion(self):
    executable = self.require("zsh")
    jobs = []
    # Publish both immutable fixture binaries before spawning any reader.
    # Host/code-signing overhead may exceed 1 second. Stress the same locking
    # protocol with a test-only 10-second bound; production timeout/skip is tested separately.
    for name in ("a", "b"):
      directory = self.cwd / name
      directory.mkdir()
      binary = directory / "docker"
      binary.write_text(f"#!/bin/sh\nsleep 0.02\nprintf '%s\\n' 'typeset -g COMPLETION_LOADED={name}'\n")
      binary.chmod(0o700)
    for index in range(4):
      name = "a" if index % 2 == 0 else "b"
      directory = self.cwd / name
      env = self.env | {"PATH": f"{directory}:{self.bin}:/usr/bin:/bin"}
      definitions = self.definitions.replace("flock -t 1 -i", "flock -t 10 -i")
      self.assertIn("flock -t 10 -i", definitions)
      script = definitions + '_load_cached_completion docker\nprint -r -- "$COMPLETION_LOADED"\n'
      jobs.append(
        (
          name,
          subprocess.Popen(
            [executable, "-dfc", script],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.cwd,
            env=env,
          ),
        )
      )
    try:
      for name, job in jobs:
        stdout, stderr = job.communicate(timeout=20)
        self.assertEqual(job.returncode, 0, stderr)
        self.assertEqual(stdout.strip(), name)
    finally:
      for _, job in jobs:
        if job.poll() is None:
          job.kill()
        job.communicate()

  def test_default_lock_timeout_skips_instead_of_loading_an_unchecked_cache(self):
    self.ok(self.shell(self.definitions, "_load_cached_completion docker\n"))
    executable = self.require("zsh")
    lock = self.cache / "docker-completion.zsh.lock"
    holder_script = f'zmodload zsh/system\nzsystem flock -f lock_fd {shlex.quote(str(lock))}\nprint READY\nread answer\n'
    holder = subprocess.Popen([executable, "-dfc", holder_script], stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                              cwd=self.cwd, env=self.env)
    try:
      self.assertEqual(holder.stdout.readline().strip(), "READY")
      result = self.shell(self.definitions, '_load_cached_completion docker\n[[ -z ${COMPLETION_LOADED:-} ]]\n')
      self.ok(result)
      self.assertEqual(len(self.calls("docker")), 1)
    finally:
      holder.communicate("release\n", timeout=20)

  def test_future_binary_mtime_is_still_a_warm_cache_hit(self):
    os.utime(self.binary, (time.time() + 3600, time.time() + 3600))
    # Isolate clock-skew invalidation from the separate NO_CLOBBER regression.
    definitions = self.definitions + "unsetopt NO_CLOBBER\n"
    self.ok(self.shell(definitions, "_load_cached_completion docker\n_load_cached_completion docker\n"))
    self.assertEqual(len(self.calls("docker")), 1)

  def test_same_path_downgrade_invalidates_identity(self):
    self.ok(self.shell(self.definitions, "_load_cached_completion docker\n"))
    self.stub("docker", "print('typeset -g COMPLETION_LOADED=downgraded')")
    os.utime(self.binary, (1, 1))
    result = self.shell(self.definitions, '_load_cached_completion docker\nprint -r -- "$COMPLETION_LOADED"\n')
    self.assertEqual(self.ok(result).strip(), "downgraded")
    self.assertEqual(len(self.calls("docker")), 2)

  def test_binary_switch_and_function_wrapper_do_not_reuse_wrong_cache(self):
    self.ok(self.shell(self.definitions, "_load_cached_completion docker\n"))
    new_bin = self.cwd / "older-installation"
    replacement = self.stub("docker", "print('typeset -g COMPLETION_LOADED=other')", new_bin)
    os.utime(replacement, (1, 1))
    result = self.shell(
      self.definitions + "docker() { return 91; }\n",
      '_load_cached_completion docker\nprint -r -- "$COMPLETION_LOADED"\n',
      env={"PATH": f"{new_bin}:{self.bin}:/usr/bin:/bin"},
    )
    self.assertEqual(self.ok(result).strip(), "other")
    self.assertIn(str(replacement), (self.cache / "docker-completion.zsh").read_text().splitlines()[0])


class FishHelpers(Fixture):
  def test_cd_failure_does_not_list_or_mask_status(self):
    self.stub("ls")
    definition = function_source(FISH / "10_sys.fish", "cdd", "fish")
    # Fish may autoload an ls wrapper that probes -F/--color using subprocesses.
    # Define the fixture wrapper explicitly so this test measures only cdd.
    definition += "function ls\n command ls $argv\nend\n"
    result = self.shell(definition, "cdd missing-directory\n", "fish")
    self.assertNotEqual(result.returncode, 0)
    self.assertEqual(self.calls("ls"), [])
    destination = self.cwd / "target"
    destination.mkdir()
    self.ok(self.shell(definition, "cdd target\n", "fish"))
    self.assertEqual(len(self.calls("ls")), 1)

  def test_uv_missing_dependency_preserves_project_state(self):
    definition = function_source_optional(FISH / "20_dev.fish", "uv_resync", "fish")
    if definition is None:
      # uv_resync 当前以注释模板保留（见 20_dev.fish）；模板在即契约满足，
      # 取消注释后本测试自动恢复行为断言（不 skip，--strict 保持全绿）。
      self.assertIn("# function uv_resync", (FISH / "20_dev.fish").read_text())
      return
    (self.cwd / ".venv").mkdir()
    lock = self.cwd / "uv.lock"
    lock.write_text("fixture")
    self.stub("rm", "sys.exit(91)")
    result = self.shell(definition, "uv_resync\n", "fish")
    self.assertEqual(result.returncode, 127)
    self.assertEqual(self.calls(), [])
    self.assertTrue((self.cwd / ".venv").is_dir())
    self.assertEqual(lock.read_text(), "fixture")

  def test_uv_steps_short_circuit_and_preserve_status(self):
    definition = function_source_optional(FISH / "20_dev.fish", "uv_resync", "fish")
    if definition is None:
      self.assertIn("# function uv_resync", (FISH / "20_dev.fish").read_text())
      return
    self.stub("rm", "sys.exit(int(os.environ.get('RM_STATUS', '0')))")
    self.stub(
      "uv", "key = 'VENV_STATUS' if sys.argv[1] == 'venv' else 'SYNC_STATUS'\nsys.exit(int(os.environ.get(key, '0')))"
    )
    definition = function_source(FISH / "20_dev.fish", "uv_resync", "fish")
    cases = [
      ({"RM_STATUS": "23"}, 23, []),
      ({"VENV_STATUS": "23"}, 23, [["uv", "venv"]]),
      ({"SYNC_STATUS": "17"}, 17, [["uv", "venv"], ["uv", "sync", "--upgrade"]]),
      ({}, 0, [["uv", "venv"], ["uv", "sync", "--upgrade"]]),
    ]
    for env, expected, uv_calls in cases:
      with self.subTest(env=env):
        self.trace.unlink(missing_ok=True)
        result = self.shell(definition, "uv_resync\n", "fish", env)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        self.assertEqual(self.calls("uv"), uv_calls)
        self.assertEqual(self.calls("rm"), [["rm", "-rf", "--", ".venv", "uv.lock"]])

  def test_fish_update_preflight(self):
    self.stub("uv")
    definition = function_source(FUNCS / "update-all.fish", "update-all", "fish")
    result = self.shell(definition, "update-all uv typo\n", "fish")
    self.assertEqual(result.returncode, 1)
    self.assertEqual(self.calls(), [])

  def test_homebrew_cleanup_defaults_and_inherited_opt_out(self):
    script = f"source {shlex.quote(str(FISH / '00_env.fish'))}\nif set -q HOMEBREW_NO_INSTALL_CLEANUP\n echo $HOMEBREW_NO_INSTALL_CLEANUP\nelse\n echo UNSET\nend\n"
    self.assertEqual(self.ok(self.shell("", script, "fish")).strip(), "UNSET")
    self.assertEqual(self.ok(self.shell("", script, "fish", {"HOMEBREW_NO_INSTALL_CLEANUP": "1"})).strip(), "1")

  def test_10_sys_command_wrappers_are_interactive_only(self):
    # 10_sys.fish 的指定系统命令包装只在交互 shell 定义；开发/Kubernetes 别名
    # 在非交互 Fish 中也会定义，另由 SourceChecks.test_active_configuration_documentation_matches_sources 检查。
    script = f"source {shlex.quote(str(FISH / '10_sys.fish'))}\n"
    script += "functions -q cp; and echo CP_DEFINED\nfunctions -q cat; and echo CAT_DEFINED\nfunctions -q cdd; and echo CDD_DEFINED\n"
    out = self.ok(self.shell("", script, "fish"))
    self.assertEqual(out.splitlines(), ["CDD_DEFINED"])

  def test_netcheck_uses_local_speedtest_without_remote_code_execution(self):
    self.stub("curl", "print('fixture IP')")
    self.stub("dig", "print('fixture DNS')")
    definition = function_source(FUNCS / "netcheck.fish", "netcheck", "fish")
    result = self.shell(definition, "netcheck\n", "fish")
    self.assertEqual(result.returncode, 127)
    self.stub("speedtest-cli", "sys.exit(17)")
    result = self.shell(definition, "netcheck\n", "fish")
    self.assertEqual(result.returncode, 17)
    self.assertEqual(self.calls("speedtest-cli"), [["speedtest-cli", "--no-upload", "--simple"]])
    self.assertTrue(all("raw.githubusercontent.com" not in " ".join(call) for call in self.calls()))


if __name__ == "__main__":
  # Import after definitions so the integration checks can reuse the fixtures.
  sys.modules["check"] = sys.modules[__name__]
  import runtime_checks

  if "--strict" in sys.argv:
    sys.argv.remove("--strict")
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(runtime_checks))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.skipped:
      print("Strict validation requires every parser/runtime; skipped tests are failures.", file=sys.stderr)
    sys.exit(0 if result.wasSuccessful() and not result.skipped else 1)
  # Named unittest selections remain supported; the default includes integration checks.
  if len(sys.argv) == 1:
    for name in ("FishRuntime", "ZshRuntime", "NeovimRuntime", "TmuxRuntime"):
      globals()[name] = getattr(runtime_checks, name)
  unittest.main(verbosity=2)
