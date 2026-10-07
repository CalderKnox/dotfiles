"""Isolated app integration tests. No user config, plugin download, or network."""

import json
import re
import shlex
import unittest
from pathlib import Path

from check import FISH, FUNCS, ROOT, ZSH, Fixture, function_source


class FishRuntime(Fixture):
  def test_repeated_source_continues_without_duplicate_plugin_paths(self):
    config = FISH.parent / "config.fish"
    for source in (config, FISH / "00_env.fish"):
      with self.subTest(source=source.name):
        script = f"source {shlex.quote(str(source))}\nsource {shlex.quote(str(source))}\necho AFTER_RELOAD\n"
        self.assertIn("AFTER_RELOAD", self.ok(self.shell("", script, "fish")))
    script = f"source {shlex.quote(str(config))}\nsource {shlex.quote(str(config))}\ncount (string match -- $fisher_path/functions $fish_function_path)\n"
    self.assertEqual(self.ok(self.shell("", script, "fish")).strip(), "1")

  def test_yazi_allocation_failure_does_not_launch(self):
    self.stub("mktemp", "sys.exit(23)")
    self.stub("yazi")
    result = self.shell(function_source(FUNCS / "y.fish", "y", "fish"), "y\n", "fish")
    self.assertEqual(result.returncode, 23)
    self.assertEqual(self.calls("yazi"), [])

  def test_yazi_failure_preserves_status_directory_and_caller_variable(self):
    destination = self.cwd / "directory with spaces"
    destination.mkdir()
    self.stub(
      "yazi", "Path(sys.argv[-1].split('=', 1)[1]).write_bytes(os.environ['DEST'].encode() + b'\\0')\nsys.exit(23)"
    )
    definition = function_source(FUNCS / "y.fish", "y", "fish")
    result = self.shell(
      definition,
      'set -g cwd sentinel\ny\nset -l rc $status\necho "$rc:$cwd:$PWD"\n',
      "fish",
      {"DEST": str(destination)},
    )
    self.assertIn(f"23:sentinel:{self.cwd.resolve()}", self.ok(result))
    path = Path(self.calls("yazi")[0][-1].split("=", 1)[1])
    self.assertFalse(path.exists())

  def test_yazi_success_navigation_and_no_change(self):
    destination = self.cwd / "directory with spaces"
    destination.mkdir()
    self.stub("yazi", "Path(sys.argv[-1].split('=', 1)[1]).write_bytes(os.environ['DEST'].encode() + b'\\0')")
    definition = function_source(FUNCS / "y.fish", "y", "fish")
    result = self.shell(definition, "y; or exit $status\necho $PWD\ny\n", "fish", {"DEST": str(destination)})
    self.assertEqual(self.ok(result).strip(), str(destination))
    for call in self.calls("yazi"):
      self.assertFalse(Path(call[-1].split("=", 1)[1]).exists())

  def test_yazi_accepts_nul_eof_and_newline_paths(self):
    destination = self.cwd / "directory with spaces"
    destination.mkdir()
    self.stub(
      "yazi",
      "Path(sys.argv[-1].split('=', 1)[1]).write_bytes(os.environ['DEST'].encode() + os.environ['END'].encode())",
    )
    definition = function_source(FUNCS / "y.fish", "y", "fish")
    for terminator in ("", "\n", "NUL"):
      with self.subTest(terminator=terminator):
        # NUL cannot be carried in an environment variable.
        self.stub(
          "yazi",
          "end = b'\\0' if os.environ['END'] == 'NUL' else os.environ['END'].encode()\nPath(sys.argv[-1].split('=', 1)[1]).write_bytes(os.environ['DEST'].encode() + end)",
        )
        result = self.shell(
          definition, "y; or exit $status\necho $PWD\n", "fish", {"DEST": str(destination), "END": terminator}
        )
        self.assertEqual(self.ok(result).strip(), str(destination))

  def test_failed_mise_output_is_not_executed(self):
    source = shlex.quote(str(FISH / "01_activate.fish"))
    definitions = 'function mise\n echo "set -g UNSAFE_INIT executed"\n return 23\nend\n'
    result = self.shell(definitions, f"source {source}\nset -q UNSAFE_INIT; and exit 91\necho GUARDED\n", "fish")
    self.assertEqual(self.ok(result).strip(), "GUARDED")
    self.assertIn("activation failed", result.stderr)

  def test_failed_interactive_initializers_are_not_executed(self):
    source = shlex.quote(str(FISH.parent / "config.fish"))
    definitions = "\n".join(
      f'function {name}\n echo "set -g UNSAFE_INIT executed"\n return 23\nend' for name in ("starship", "zoxide")
    )
    result = self.run_command(
      [
        self.require("fish"),
        "--no-config",
        "--private",
        "-ic",
        definitions + f"\nsource {source}\nset -q UNSAFE_INIT; and exit 91\necho GUARDED\n",
      ],
      env={"TERM": "xterm-256color"},
    )
    self.assertEqual(self.ok(result).strip(), "GUARDED")
    self.assertIn("initialization failed", result.stderr)

  def test_backup_failure_and_missing_files_are_not_reported_as_success(self):
    (self.cwd / "-leading.txt").write_text("fixture")
    self.stub("date", "print('20260101_000000')")
    self.stub("cp", "sys.exit(23)")
    definition = function_source(FUNCS / "bak.fish", "bak", "fish")
    result = self.shell(definition, "bak missing -leading.txt\n", "fish", {"TERM": "xterm-256color"})
    self.assertEqual(result.returncode, 1)
    self.assertNotIn("Backed up", result.stdout)
    self.assertEqual(self.calls("cp"), [["cp", "-f", "--", "-leading.txt", "-leading.txt.20260101_000000.bak"]])

  def test_update_all_mixed_results_continue_and_propagate_failure(self):
    self.stub("uv", "sys.exit(23)")
    self.stub("mise")
    definition = function_source(FUNCS / "update-all.fish", "update-all", "fish")
    result = self.shell(definition, "update-all uv mise pi\n", "fish", {"TERM": "xterm-256color"})
    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
    self.assertEqual(self.calls(), [["uv", "tool", "upgrade", "--all"], ["mise", "upgrade"]])
    self.assertIn("✓ mise done", result.stdout)
    self.assertIn("✗ uv failed", result.stdout)
    self.assertIn("attempted: 2 · skipped: 1 · failed: 1", result.stdout)
    self.assertIn("skipped: pi", result.stdout)
    self.assertIn("failed: uv", result.stdout)
    self.assertIn("1 update(s) failed", result.stdout)
    self.assertIn("pi not found", result.stdout)

  def test_update_all_accepts_rustup_alias_for_rust(self):
    self.stub("rustup")
    definition = function_source(FUNCS / "update-all.fish", "update-all", "fish")
    result = self.shell(definition, "update-all rustup\n", "fish", {"TERM": "xterm-256color"})
    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
    self.assertEqual(self.calls("rustup"), [["rustup", "update"]])
    self.assertIn("✓ rust done", result.stdout)

  def test_update_all_sdk_target_flushes_like_zsh(self):
    self.stub("sdk")
    definition = function_source(FUNCS / "update-all.fish", "update-all", "fish")
    result = self.shell(definition, "update-all sdk\n", "fish", {"TERM": "xterm-256color"})
    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
    self.assertEqual(
      self.calls("sdk"),
      [["sdk", "update"], ["sdk", "upgrade"], ["sdk", "selfupdate"], ["sdk", "flush"]],
    )

  def fish_sdk_block(self):
    source = (FISH / "01_activate.fish").read_text()
    start = source.index("# --- SDKMAN")
    return source[start : source.index("# --- end SDKMAN", start)]

  def test_fish_sdk_stub_absent_without_sdkman_and_lazy_with_it(self):
    block = self.fish_sdk_block()
    # 未安装 SDKMAN：不定义任何函数（update-all 的 sdk 目标随之跳过）
    result = self.shell("", block + "\nfunctions -q sdk; or echo NO_STUB\n", "fish")
    self.assertEqual(self.ok(result).strip(), "NO_STUB")
    # 已安装：桩已定义且惰性——定义本身不 source init；bass 缺失时受控失败
    # 127（不扏 bash 报错、不递归）
    self.sdk_init("export INIT=1\n")
    script = block + "\nfunctions -q sdk; and echo STUB\n"
    self.assertIn("STUB", self.ok(self.shell("", script, "fish")))
    result = self.shell("", block + "\nsdk current\n", "fish")
    self.assertEqual(result.returncode, 127, result.stderr)
    self.assertIn("bass", result.stderr)

  def test_fish_sdk_stub_forwards_args_to_bass_without_eager_init(self):
    self.sdk_init("export INIT=1\n")
    script = (
      self.fish_sdk_block()
      + "\nfunction bass; echo BASS (string join ' ' $argv); end\nsdk current java\n"
    )
    out = self.ok(self.shell("", script, "fish")).strip()
    init = Path(self.env["HOME"]) / ".sdkman/bin/sdkman-init.sh"
    self.assertEqual(out, f"BASS source {init} ;and sdk current java")


class ZshRuntime(Fixture):
  def sdk_block(self):
    source = (ZSH / "sdk.zsh").read_text()
    start = source.index('if [[ -s "$HOME/.sdkman/bin/sdkman-init.sh"')
    return source[start : source.index("########## Android", start)]

  def test_sdk_is_lazy_and_not_reset_by_repeated_source(self):
    self.sdk_init('typeset -g INIT_CALLS=$(( ${INIT_CALLS:-0} + 1 ))\nsdk() { print -r -- "sdk:$*:$INIT_CALLS"; }\n')
    block = self.sdk_block()
    script = "[[ -z ${INIT_CALLS:-} ]] || exit 91\nsdk current\n" + block + "sdk version\n"
    self.assertEqual(self.ok(self.shell(block, script)).splitlines(), ["sdk:current:1", "sdk:version:1"])

  def test_sdk_failed_init_never_recurses(self):
    self.sdk_init("return 23\n")
    result = self.shell("FUNCNEST=8\n" + self.sdk_block(), "sdk current\n")
    self.assertEqual(result.returncode, 23, result.stderr)
    self.assertNotIn("maximum nested", result.stderr)

  def test_backup_mixed_failures_are_not_masked_by_later_success(self):
    (self.cwd / "file.txt").write_text("fixture")
    self.stub("cp")
    definition = function_source(ZSH / "aliases.zsh", "bak")
    result = self.shell(definition, "bak missing file.txt\n")
    self.assertEqual(result.returncode, 1)
    self.assertEqual(len(self.calls("cp")), 1)

  def test_global_fzf_actions_delimit_paths_and_tab_overrides_shell(self):
    source = (ZSH / "fzf.zsh").read_text()
    options = source[source.index("export FZF_DEFAULT_OPTS=") : source.index("# 历史记录搜索")]
    self.stub("nvim")
    self.stub("lsd")
    self.stub("bat")
    self.stub("fzf", "print('one file.txt')")
    self.ok(self.shell("EDITOR=nvim\n", options + "\nfzf --filter=one\n", env={"PATH": f"{self.bin}:/usr/bin:/bin"}))
    self.assertIn("$EDITOR -- {} >/dev/tty 2>&1", options)
    for name in ("two words.txt", "it's.txt", "-leading.txt", "a; echo danger.txt"):
      with self.subTest(path=name):
        template = "nvim -- {}"
        self.ok(self.run_command(["/bin/sh", "-c", template.replace("{}", shlex.quote(name))]))
        self.assertEqual(self.calls("nvim")[-1], ["nvim", "--", name])
    self.assertIn("--icon=always -- {}", source)
    self.assertIn("--line-range :100 -- {}", source)
    self.assertIn("fzf-flags --with-shell='zsh -f -c'", source)

  def test_failed_zsh_initializers_are_not_executed(self):
    rc = (ZSH / "dot_zshrc").read_text()
    start = rc.index("# init（逐项守卫")
    fragment = rc[start : rc.index("# fzf 的键位", start)]
    definitions = "\n".join(
      name + '() { print -r -- "typeset -g UNSAFE_INIT=executed"; return 23; }'
      for name in ("starship", "zoxide", "mise")
    )
    result = self.shell(definitions + "\n", fragment + "\n[[ -z ${UNSAFE_INIT:-} ]] || exit 91\nprint GUARDED\n")
    self.assertEqual(self.ok(result).strip(), "GUARDED")

  def test_frg_rejects_filename_controlled_ex_commands(self):
    self.stub("rg", "print('fixture:12:needle')")
    self.stub("fzf", "sys.stdin.read()")
    definition = function_source(ZSH / "fzf.zsh", "frg")
    self.ok(self.shell(definition, "frg needle\n"))
    args = self.calls("fzf")[0]
    binding = args[args.index("--bind") + 1]
    editor = binding.removeprefix("enter:execute(").removesuffix(")+abort")
    self.stub("nvim")
    for line in ("lua vim.g.boundary_probe=1", "0", "-1", "12foo", "12; echo injected"):
      with self.subTest(line=line):
        command = editor.replace("{1}", shlex.quote("prefix")).replace("{2}", shlex.quote(line))
        self.run_command(["/bin/sh", "-c", command])
        self.assertEqual(self.calls("nvim"), [])

  def test_fkill_validates_and_deduplicates_before_signal(self):
    self.stub("ps", "print('UID PID COMMAND')")
    self.stub("fzf", "print(os.environ['SELECTION'])")
    definition = (
      function_source(ZSH / "fzf.zsh", "fkill") + 'kill() { printf "%s\\n" "$@" > "$KILL_LOG"; return 17; }\n'
    )
    log = self.cwd / "kill-args"
    result = self.shell(
      definition, "fkill TERM\n", env={"SELECTION": "u 123 one\nu 456 two\nu 123 duplicate", "KILL_LOG": str(log)}
    )
    self.assertEqual(result.returncode, 17)
    self.assertEqual(log.read_text().splitlines(), ["-TERM", "--", "123", "456"])
    log.unlink()
    result = self.shell(definition, "fkill\n", env={"SELECTION": "u 123 one\nu 0 invalid", "KILL_LOG": str(log)})
    self.assertEqual(result.returncode, 1)
    self.assertFalse(log.exists())

  def test_ftm_cancellation_and_operational_failures_are_distinct(self):
    self.stub(
      "tmux",
      "print('session') if sys.argv[1] == 'list-sessions' else None\nsys.exit(int(os.environ.get('LIST_STATUS' if sys.argv[1] == 'list-sessions' else 'ATTACH_STATUS', '0')))",
    )
    self.stub("fzf", "print('session')\nsys.exit(int(os.environ.get('FZF_STATUS', '0')))")
    definition = function_source(ZSH / "fzf.zsh", "ftm")
    for env, status in (({"FZF_STATUS": "130"}, 0), ({"ATTACH_STATUS": "23"}, 23), ({"LIST_STATUS": "17"}, 1)):
      with self.subTest(env=env):
        self.assertEqual(self.shell(definition, "ftm\n", env=env).returncode, status)

  def uv_definition(self):
    path = ZSH / "aliases.zsh"
    # Also test the initial alias in before/after negative controls.
    alias = re.search(r"^alias uv_resync=.*$", path.read_text(), re.MULTILINE)
    if alias:
      return alias[0] + "\n"
    try:
      return function_source(path, "uv_resync")
    except AssertionError:
      return None

  def test_uv_missing_dependency_preserves_home_scope(self):
    # Zsh deliberately resets HOME state, unlike Fish's project-relative helper.
    definition = self.uv_definition()
    if definition is None:
      # uv_resync 当前以注释模板保留（见 aliases.zsh）；模板在即契约满足，
      # 取消注释后本测试自动恢复行为断言（不 skip，--strict 保持全绿）。
      self.assertIn("# uv_resync() {", (ZSH / "aliases.zsh").read_text())
      return
    home = Path(self.env["HOME"])
    (home / ".venv").mkdir()
    (home / "uv.lock").write_text("fixture")
    self.stub("rm", "sys.exit(91)")
    result = self.shell(definition, "uv_resync\n")
    self.assertEqual(result.returncode, 127)
    self.assertEqual(self.calls("rm"), [])
    self.assertTrue((home / ".venv").is_dir())
    self.assertEqual((home / "uv.lock").read_text(), "fixture")

  def test_uv_reset_failure_short_circuits_and_paths_are_quoted(self):
    definition = self.uv_definition()
    if definition is None:
      self.assertIn("# uv_resync() {", (ZSH / "aliases.zsh").read_text())
      return
    self.stub("rm", "sys.exit(int(os.environ.get('RM_STATUS', '0')))")
    self.stub("uv", "sys.exit(17)")
    for failure, expected_calls in (("23", []), ("0", [["uv", "sync"]])):
      with self.subTest(reset_status=failure):
        self.trace.unlink(missing_ok=True)
        result = self.shell(definition, "uv_resync\n", env={"RM_STATUS": failure})
        self.assertEqual(result.returncode, 23 if failure == "23" else 17)
        self.assertEqual(self.calls("uv"), expected_calls)
        home = self.env["HOME"]
        self.assertEqual(self.calls("rm"), [["rm", "-rf", "--", f"{home}/.venv", f"{home}/uv.lock"]])


class NeovimRuntime(Fixture):
  def nvim(self, script):
    lua = self.cwd / "test.lua"
    lua.write_text(script)
    command = (
      "lua local ok, err = xpcall(function() dofile("
      + json.dumps(str(lua))
      + ') end, debug.traceback); if not ok then io.stderr:write(err .. "\\n"); vim.cmd("cquit 1") end'
    )
    return self.run_command(
      [self.require("nvim"), "--headless", "-u", "NONE", "-i", "NONE", "-n", "-c", command],
      env={"NVIM_LOG_FILE": str(self.cwd / "nvim.log")},
    )

  def test_cursorline_real_mode_transitions(self):
    output = self.cwd / "modes.json"
    source = ROOT / "dot_config/nvim/lua/config/autocmds.lua"
    script = (
      "local source = "
      + json.dumps(str(source))
      + "\n"
      + """
dofile(source)
local results = {}
local steps = {
  {"i", "insert"}, {"<C-C>", "ctrl-c"}, {"R", "replace"}, {"<Esc>", "escape"},
  {"i", "insert-again"}, {"<C-O>", "ctrl-o"}, {"l", "insert-resumed"}, {"<Esc>", "normal"},
  {"v", "visual"}, {"<Esc>", "normal-again"},
}
local function step(index)
  if index > #steps then
    vim.fn.writefile({vim.json.encode(results)}, OUTPUT)
    vim.cmd("qa!")
    return
  end
  vim.api.nvim_input(vim.api.nvim_replace_termcodes(steps[index][1], true, false, true))
  vim.defer_fn(function()
    results[#results + 1] = {label=steps[index][2], mode=vim.fn.mode(1), cursorline=vim.wo.cursorline}
    step(index + 1)
  end, 20)
end
vim.schedule(function() step(1) end)
""".replace("OUTPUT", json.dumps(str(output)))
    )
    self.ok(self.nvim(script))
    results = json.loads(output.read_text())
    self.assertEqual(len(results), 10)
    for state in results:
      with self.subTest(state=state):
        self.assertEqual(state["cursorline"], state["mode"] == "n")
    self.assertEqual([s["mode"] for s in results[:4]], ["i", "n", "R", "n"])

  def test_autocmd_reload_and_window_entry_are_idempotent(self):
    source = ROOT / "dot_config/nvim/lua/config/autocmds.lua"
    self.ok(
      self.nvim(
        """
local source = SOURCE
dofile(source)
local first = #vim.api.nvim_get_autocmds({group="HighlightCursorLine"})
dofile(source)
assert(#vim.api.nvim_get_autocmds({group="HighlightCursorLine"}) == first)
assert(vim.wo.cursorline, "cursorline should be initialized in Normal mode")
vim.cmd("vsplit")
assert(vim.wo.cursorline, "new Normal window should have cursorline")
vim.wo.cursorline = false
vim.cmd("wincmd w")
vim.cmd("wincmd w")
assert(vim.wo.cursorline, "window entry should refresh mode-dependent option")
vim.cmd("qa!")
""".replace("SOURCE", json.dumps(str(source)))
      )
    )

  def test_local_options_keymap_and_plugin_specs(self):
    config = ROOT / "dot_config/nvim"
    self.ok(
      self.nvim(
        """
local config = CONFIG
dofile(config .. "/lua/config/options.lua")
dofile(config .. "/lua/config/keymaps.lua")
assert(vim.opt.colorcolumn:get()[1] == "120")
assert(vim.opt.scrolloff:get() == 8)
assert(not vim.opt.modeline:get())
assert(vim.g.lazyvim_python_lsp == "pyrefly")
assert(vim.fn.maparg("jk", "i") == "<Esc>")
assert(dofile(config .. "/lua/plugins/colorscheme.lua")[1].opts.colorscheme == "catppuccin")
assert(dofile(config .. "/lua/plugins/sidekick.lua")[1].opts.nes.enabled == false)
local tools = dofile(config .. "/lua/plugins/mason.lua")[1].opts.ensure_installed
assert(vim.tbl_contains(tools, "pyrefly"))
assert(vim.tbl_contains(tools, "rust-analyzer"))
vim.cmd("qa!")
""".replace("CONFIG", json.dumps(str(config)))
      )
    )


class TmuxRuntime(Fixture):
  def setUp(self):
    super().setUp()
    self.tmux = self.require("tmux")
    self.socket = self.cwd / "tmux.sock"
    self.ok(self.run_tmux("-f", "/dev/null", "new-session", "-d", "-s", "validation", "/usr/bin/tail -f /dev/null"))
    self.addCleanup(lambda: self.run_tmux("kill-server"))

  def run_tmux(self, *args):
    return self.run_command([self.tmux, "-S", self.socket, *args])

  def option(self, name):
    return self.ok(self.run_tmux("show-options", "-gqv", name)).strip()

  def load_config(self):
    config = Path(self.env["HOME"]) / ".tmux.conf"
    config.write_text((ROOT / "dot_tmux.conf").read_text())
    self.ok(self.run_tmux("source-file", config))

  def install_plugin_contract_stubs(self):
    # Model only documented init contracts, not arbitrary external plugin code.
    plugins = Path(self.env["HOME"]) / ".config/tmux/plugins"
    theme = plugins / "tmux/catppuccin.tmux"  # TPM uses repo basename "tmux".
    theme.parent.mkdir(parents=True)
    options = self.cwd / "theme.conf"
    options.write_text(
      "\n".join(
        f'set -g @catppuccin_status_{name} "[{name.upper()}]"'
        for name in ("application", "cpu", "ram", "session", "uptime", "battery")
      )
      + "\n"
    )
    command = f"{shlex.quote(self.tmux)} -S {shlex.quote(str(self.socket))} source-file {shlex.quote(str(options))}"
    theme.write_text("#!/bin/sh\n" + command + "\n")
    theme.chmod(0o700)
    tpm = plugins / "tpm/tpm"
    tpm.parent.mkdir(parents=True)
    # The supported source list must include the XDG install directory.
    tpm.write_text(
      "#!/bin/sh\n"
      + f'{shlex.quote(self.tmux)} -S {shlex.quote(str(self.socket))} show-environment -g TMUX_PLUGIN_MANAGER_PATH > "$HOME/plugin-path"\n'
      + command
      + "\n"
    )
    tpm.chmod(0o700)

  def test_capability_arrays_remain_unique_after_reloads(self):
    for _ in range(3):
      self.load_config()
    self.assertEqual(self.option("terminal-overrides").splitlines().count("xterm-256color:RGB"), 1)
    self.assertEqual(self.option("terminal-features").splitlines().count("xterm*:extkeys"), 1)
    self.assertIn("linux*:AX@", self.option("terminal-overrides"))

  def test_cold_status_expansion_and_xdg_plugin_path(self):
    self.install_plugin_contract_stubs()
    self.load_config()
    for name in ("CPU", "RAM", "BATTERY"):
      self.assertIn(f"[{name}]", self.option("status-right"))
    plugin_path = Path(self.env["HOME"]) / "plugin-path"
    self.assertEqual(
      plugin_path.read_text().strip(), f"TMUX_PLUGIN_MANAGER_PATH={self.env['HOME']}/.config/tmux/plugins/"
    )
    first = self.option("status-right")
    self.load_config()
    self.assertEqual(self.option("status-right"), first)

  def test_traditional_tpm_installation_is_supported(self):
    self.install_plugin_contract_stubs()
    home = Path(self.env["HOME"])
    (home / ".tmux").mkdir()
    (home / ".config/tmux/plugins").rename(home / ".tmux/plugins")
    self.load_config()
    path = (home / "plugin-path").read_text().strip()
    self.assertEqual(path, f"TMUX_PLUGIN_MANAGER_PATH={home}/.tmux/plugins/")
    self.assertIn("[CPU]", self.option("status-right"))

  def test_explicit_tpm_path_is_respected(self):
    self.install_plugin_contract_stubs()
    home = Path(self.env["HOME"])
    custom = self.cwd / "plugins with spaces"
    (home / ".config/tmux/plugins").rename(custom)
    self.ok(self.run_tmux("set-environment", "-g", "TMUX_PLUGIN_MANAGER_PATH", str(custom) + "/"))
    self.load_config()
    self.assertEqual((home / "plugin-path").read_text().strip(), f"TMUX_PLUGIN_MANAGER_PATH={custom}/")
    self.assertIn("[CPU]", self.option("status-right"))

  def test_missing_plugins_leave_core_tmux_configuration_usable(self):
    self.load_config()
    self.assertEqual(self.option("mouse"), "on")
    self.assertEqual(self.option("history-limit"), "100000")
    self.assertTrue(self.option("default-shell").endswith(("fish", "bash")))
    bindings = self.ok(self.run_tmux("list-keys", "-T", "prefix"))
    self.assertTrue(any(re.search(r"prefix\s+r\s+source-file", line) for line in bindings.splitlines()))


if __name__ == "__main__":
  unittest.main(verbosity=2)
