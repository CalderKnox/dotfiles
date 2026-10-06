#!/usr/bin/env python3
"""Prove selected regressions fail on the original HEAD, without changing worktree."""

import argparse
import contextlib
import io
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import check
import runtime_checks

sys.dont_write_bytecode = True

CONTROLS = (
  (check.SourceChecks, "test_pi_source_allowlist"),
  (check.ZshHelpers, "test_update_preflight_and_caller_variable"),
  (check.ZshHelpers, "test_flkill_multiselect_is_validated_and_deduplicated"),
  (check.ZshHelpers, "test_frg_uses_shell_quoted_placeholders_and_option_terminators"),
  (check.CompletionCache, "test_refresh_under_no_clobber"),
  (check.CompletionCache, "test_future_binary_mtime_is_still_a_warm_cache_hit"),
  (check.FishHelpers, "test_uv_missing_dependency_preserves_project_state"),
  (check.FishHelpers, "test_cd_failure_does_not_list_or_mask_status"),
  (runtime_checks.FishRuntime, "test_yazi_allocation_failure_does_not_launch"),
  (runtime_checks.FishRuntime, "test_yazi_failure_preserves_status_directory_and_caller_variable"),
  (runtime_checks.ZshRuntime, "test_sdk_failed_init_never_recurses"),
  (runtime_checks.ZshRuntime, "test_sdk_is_lazy_and_not_reset_by_repeated_source"),
  (runtime_checks.ZshRuntime, "test_uv_missing_dependency_preserves_home_scope"),
  (runtime_checks.ZshRuntime, "test_frg_rejects_filename_controlled_ex_commands"),
  (runtime_checks.TmuxRuntime, "test_capability_arrays_remain_unique_after_reloads"),
  (runtime_checks.TmuxRuntime, "test_cold_status_expansion_and_xdg_plugin_path"),
  (runtime_checks.NeovimRuntime, "test_cursorline_real_mode_transitions"),
)
FILES = (
  ".gitignore",
  "dot_tmux.conf",
  "private_dot_config/nvim/lua/config/autocmds.lua",
  "private_dot_config/zsh/aliases.zsh",
  "private_dot_config/zsh/fzf.zsh",
  "private_dot_config/zsh/sdk.zsh",
  "private_dot_config/private_fish/private_conf.d/00_aliases.fish",
  "private_dot_config/private_fish/private_conf.d/01_dev.fish",
)


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--revision", default="HEAD", help="Git revision providing the original source")
  args = parser.parse_args()
  git = shutil.which("git")
  if not git:
    parser.error("git is required")
  repository = check.ROOT
  revision = subprocess.check_output(
    [git, "rev-parse", "--verify", args.revision + "^{commit}"], cwd=repository, text=True
  ).strip()
  print(f"Negative-control revision: {revision}")
  with tempfile.TemporaryDirectory(prefix="dotfiles-negative-controls-") as tmp:
    baseline = Path(tmp)
    for name in FILES:
      data = subprocess.check_output([git, "show", f"{revision}:{name}"], cwd=repository)
      path = baseline / name
      path.parent.mkdir(parents=True, exist_ok=True)
      path.write_bytes(data)
    # Reuse current test definitions with historical configuration files.
    for module in (check, runtime_checks):
      module.ROOT = baseline
      module.ZSH = baseline / "private_dot_config/zsh"
      module.FISH = baseline / "private_dot_config/private_fish/private_conf.d"
    reproduced = 0
    invalid = 0
    for cls, name in CONTROLS:
      test = cls(name)
      stream = io.StringIO()
      with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
        result = unittest.TextTestRunner(stream=stream).run(unittest.TestSuite([test]))
      valid = bool(result.failures) and not result.errors and not result.skipped
      if valid:
        reproduced += 1
        print(f"REPRODUCED {cls.__name__}.{name}")
      else:
        invalid += 1
        print(f"INVALID CONTROL {cls.__name__}.{name}\n{stream.getvalue()}")
    print(f"{reproduced}/{len(CONTROLS)} reproduced; {invalid} invalid controls")
    return 0 if invalid == 0 else 1


if __name__ == "__main__":
  raise SystemExit(main())
