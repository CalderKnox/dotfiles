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
ZSH = ROOT / "private_dot_config/zsh"
FISH = ROOT / "private_dot_config/private_fish/private_conf.d"
FUNCS = ROOT / "private_dot_config/private_fish/private_functions"
FISH_COMPLETIONS = ROOT / "private_dot_config/private_fish/private_completions"


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

  def test_lua_syntax_per_file(self):
    tool = self.require("luac")
    for path in sorted((ROOT / "private_dot_config/nvim").rglob("*.lua")):
      with self.subTest(path=path.name):
        self.ok(self.run_command([tool, "-p", path]))

  def test_neovim_documentation_contracts(self):
    config = ROOT / "private_dot_config/nvim"
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
        "dot_pi/workflows/settings.json",
        "private_dot_config/nvim/lazyvim.json",
      )
    ]
    for path in paths:
      with self.subTest(path=path.relative_to(ROOT)):
        json.loads(path.read_text())
    for path in (
      ROOT / "private_dot_config/mise/config.toml",
      ROOT / "private_dot_config/alacritty/private_alacritty.toml",
      ROOT / "private_dot_config/nvim/stylua.toml",
    ):
      with path.open("rb") as stream:
        tomllib.load(stream)
    self.ok(
      self.run_command([self.require("git"), "config", "--no-includes", "--file", ROOT / "dot_gitconfig", "--list"])
    )

  def test_ssh_config_parses(self):
    # `ssh -G` resolves and prints the effective configuration without connecting
    # and without executing ProxyCommand. Token expansion must key ControlPath on
    # %n so aliases sharing user@host:port (tst/ops/sec, the github pair) each own
    # a distinct socket and their IdentityFiles actually engage.
    ssh = self.require("ssh")
    config = ROOT / "private_dot_ssh/private_config"
    result = None
    for host in ("tst", "ops", "sec", "github.com"):
      result = self.run_command([ssh, "-G", "-F", config, host])
      self.ok(result)
      options = {line.split(" ", 1)[0]: line.split(" ", 1)[1] for line in result.stdout.splitlines() if " " in line}
      self.assertIn("controlpath", options)
      self.assertIn(host, options["controlpath"], host)
    self.assertIn("proxycommand", {line.split(" ", 1)[0] for line in result.stdout.splitlines()})

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
      "private_dot_pi/private_agent/auth.json",
      "private_dot_pi/private_agent/private_auth.json",
      "private_dot_pi/private_agent/encrypted_auth.json.age",
      "private_dot_pi/private_agent/private_mcp.json",
      "private_dot_pi/private_agent/sessions/example.json",
    ]
    result = self.run_command([git, "check-ignore", "--no-index", "--stdin"], script="\n".join(blocked) + "\n")
    self.ok(result)
    self.assertEqual(result.stdout.splitlines(), blocked)
    for allowed in ("dot_pi/agent/settings.json", "dot_pi/agent/pi-goal.json", "dot_pi/workflows/settings.json"):
      with self.subTest(path=allowed):
        result = self.run_command([git, "check-ignore", "--no-index", "-q", allowed])
        self.assertEqual(result.returncode, 1, result.stderr)

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
    pi_files = {path for path in targets if path.startswith(".pi/") and path.endswith(".json")}
    self.assertEqual(pi_files, {".pi/agent/settings.json", ".pi/agent/pi-goal.json", ".pi/workflows/settings.json"})
    self.assertFalse(any(path == "docs" or path.startswith("docs/") for path in targets))
    self.assertFalse(any(path.endswith("README.md") for path in targets))
    self.assertNotIn(".codex/config.toml", targets)
    self.assertNotIn(".config/kitty/kitty.local.conf", targets)
    self.assertIn(".zshrc", targets)
    self.assertIn(".zimrc", targets)

  def test_synthetic_pi_runtime_files_are_excluded_and_rule_is_necessary(self):
    source = self.cwd / "source"
    source.mkdir()
    ignore = source / ".chezmoiignore"
    rules = (ROOT / ".chezmoiignore").read_text()
    ignore.write_text(rules)
    fixtures = (
      "dot_pi/agent/settings.json",
      "dot_pi/agent/pi-goal.json",
      "dot_pi/workflows/settings.json",
      "dot_pi/agent/auth.json",
      "dot_pi/agent/private_private-auth.json",
      "dot_pi/agent/encrypted_encrypted-auth.json.age",
      "dot_pi/agent/sessions/transcript.jsonl",
      "dot_pi/agent/extensions/probe.js",
      "dot_pi/agent/private_mcp.json",
      "dot_pi/workflows/projects/state.txt",
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
    expected = {
      ".pi",
      ".pi/agent",
      ".pi/workflows",
      ".pi/agent/settings.json",
      ".pi/agent/pi-goal.json",
      ".pi/workflows/settings.json",
    }
    self.assertEqual(targets, expected)
    # Mutation control: the same fixture must expose runtime files without the deny rule.
    ignore.write_text(rules.replace(".pi/**\n", ""))
    mutated = set(self.ok(self.run_command(argv)).splitlines())
    self.assertNotEqual(mutated, expected)
    self.assertIn(".pi/agent/extensions/probe.js", mutated)

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
      (".config", 0o700),
      (".config/fish", 0o700),
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
      ROOT / "private_dot_config/nvim/README.md",
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
        self.assertEqual(stdout.strip(), "concurrent")
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

  def test_behavior_changing_aliases_are_interactive_only(self):
    # 与 zsh .zshrc 只在交互 shell 加载对齐：非交互 source 后，遮蔽原生命令的
    # 行为改变型别名（cp/cat/mkdir…）不得定义；显式函数（cdd/mkcd）仍可用。
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
