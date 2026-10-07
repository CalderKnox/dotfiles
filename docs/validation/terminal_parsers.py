#!/usr/bin/env python3
"""Native, no-GUI Ghostty/kitty parsing using disposable HOME/XDG paths."""

import json
import sys
import unittest
from pathlib import Path

from check import ROOT, Fixture

sys.dont_write_bytecode = True


class TerminalParsers(Fixture):
  def test_kitty_configuration_and_splits_layout(self):
    path = ROOT / "dot_config/kitty/kitty.local.conf"
    script = """
from kitty.config import load_config
bad = []
options = load_config(PATH, accumulate_bad_lines=bad)
assert not bad, str(bad)
assert options.enabled_layouts[0].startswith('splits'), options.enabled_layouts
assert options.font_size == 15.0
print('kitty configuration parsed; splits layout selected')
""".replace("PATH", json.dumps(str(path)))
    self.ok(self.run_command([self.require("kitty"), "+runpy", script]))

  def test_ghostty_native_configuration_parser(self):
    tool = Path("/Applications/Ghostty.app/Contents/MacOS/ghostty")
    if not tool.is_file():
      self.skipTest("Ghostty application not installed at standard macOS path")
    config = ROOT / "dot_config/ghostty/config"
    result = self.run_command([tool, "+validate-config", f"--config-file={config}"])
    self.ok(result)
    self.assertNotIn("error:", result.stderr.lower())


if __name__ == "__main__":
  result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TerminalParsers))
  raise SystemExit(0 if result.wasSuccessful() and not result.skipped else 1)
