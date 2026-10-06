#!/usr/bin/env python3
"""Offline integration against explicitly supplied, locally installed tmux plugins.

Copies plugins to a disposable HOME, uses a private server, and substitutes all
status collector commands. Never installs/updates plugins or uses a live socket.
"""

import argparse
import re
import shutil
import sys
import unittest
from pathlib import Path

from runtime_checks import TmuxRuntime

sys.dont_write_bytecode = True


class InstalledPlugins(TmuxRuntime):
  plugin_root = None
  tpm_source = None

  def test_real_plugin_initializers_cold_and_reload(self):
    plugins = Path(self.env["HOME"]) / ".config/tmux/plugins"
    sources = {
      "tpm": self.tpm_source,
      "tmux": self.plugin_root / "tmux",
      "tmux-cpu": self.plugin_root / "tmux-cpu",
      "tmux-battery": self.plugin_root / "tmux-battery",
    }
    for name, source in sources.items():
      self.assertTrue(source.is_dir(), f"Missing required plugin: {source}")
      shutil.copytree(source, plugins / name, ignore=shutil.ignore_patterns(".git", "tests"))
    # Every call to tmux by copied shell scripts must use this exact private socket.
    tmux_proxy = self.bin / "tmux"
    tmux_proxy.write_text(
      f"#!{sys.executable}\nimport os,sys\nos.execv({self.tmux!r}, [{self.tmux!r}, '-S', {str(self.socket)!r}, *sys.argv[1:]])\n"
    )
    tmux_proxy.chmod(0o700)
    # Update server PATH so run-shell/plugin subprocesses inherit the proxy.
    self.ok(self.run_tmux("set-environment", "-g", "PATH", self.env["PATH"]))
    for name, entry in (("tmux-cpu", "cpu.tmux"), ("tmux-battery", "battery.tmux")):
      code = (plugins / name / entry).read_text()
      collectors = set(re.findall(r"#\(\$CURRENT_DIR/scripts/([\w.-]+\.sh)", code))
      self.assertTrue(collectors)
      for collector in collectors:
        path = plugins / name / "scripts" / collector
        path.write_text("#!/bin/sh\nprintf 'fixture-value'\n")
        path.chmod(0o700)
    # This optional plugin entry probes hardware through helpers; neutralize it.
    battery_probe = plugins / "tmux-battery/battery_enabled.tmux"
    if battery_probe.exists():
      battery_probe.write_text("#!/bin/sh\nexit 0\n")
    self.load_config()
    status = self.option("status-right")
    for collector in ("cpu_percentage.sh", "ram_percentage.sh", "battery_percentage.sh"):
      self.assertIn(collector, status)
    for unresolved in ("#{cpu_percentage}", "#{ram_percentage}", "#{battery_percentage}"):
      self.assertNotIn(unresolved, status)
    for _ in range(2):
      self.load_config()
      self.assertEqual(self.option("status-right"), status)
    self.assertEqual(self.option("terminal-overrides").splitlines().count("xterm-256color:RGB"), 1)
    self.assertEqual(self.option("terminal-features").splitlines().count("xterm*:extkeys"), 1)


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument(
    "--plugin-root", type=Path, required=True, help="Directory containing tmux, tmux-cpu, tmux-battery"
  )
  parser.add_argument(
    "--tpm-source", type=Path, required=True, help="TPM installation directory (containing tpm executable)"
  )
  args = parser.parse_args()
  InstalledPlugins.plugin_root = args.plugin_root.resolve()
  InstalledPlugins.tpm_source = args.tpm_source.resolve()
  # Only the explicit real-plugin test; inherited contract tests run in check.py.
  suite = unittest.TestSuite([InstalledPlugins("test_real_plugin_initializers_cold_and_reload")])
  result = unittest.TextTestRunner(verbosity=2).run(suite)
  return 0 if result.wasSuccessful() and not result.skipped else 1


if __name__ == "__main__":
  raise SystemExit(main())
