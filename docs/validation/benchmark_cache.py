#!/usr/bin/env python3
"""Reproducible stub-only completion-loader comparison; not shell startup timing."""

import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.dont_write_bytecode = True

from check import ROOT, CompletionCache, function_source  # noqa: E402


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--revision", default="b4e8bac8513ef949d1c3af6c7d99b633b986898d")
  parser.add_argument("--loads", type=int, default=12)
  parser.add_argument("--samples", type=int, default=3)
  args = parser.parse_args()
  if args.loads < 1 + 1 or args.samples < 1:
    parser.error("loads must be >=2 and samples >=1")
  git = shutil.which("git")
  if not git:
    parser.error("git is required")
  revision = subprocess.check_output(
    [git, "rev-parse", "--verify", f"{args.revision}^{{commit}}"], cwd=ROOT, text=True
  ).strip()
  candidates = ("dot_config/zsh/sdk.zsh", "private_dot_config/zsh/sdk.zsh")
  source_path = None
  for candidate in candidates:
    result = subprocess.run(
      [git, "cat-file", "-e", f"{revision}:{candidate}"],
      cwd=ROOT,
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
    )
    if result.returncode == 0:
      source_path = candidate
      break
  if source_path is None:
    parser.error(f"no Zsh SDK source found in {args.revision}; checked: {', '.join(candidates)}")
  baseline = subprocess.check_output([git, "show", f"{revision}:{source_path}"], cwd=ROOT, text=True)
  with tempfile.TemporaryDirectory(prefix="cache-benchmark-source-") as tmp:
    source = Path(tmp) / "sdk.zsh"
    source.write_text(baseline)
    old = function_source(source, "_load_cached_completion")
  measurements = {}
  for label in ("baseline", "worktree"):
    samples = []
    generated = []
    for _ in range(args.samples):
      fixture = CompletionCache()
      fixture.setUp()
      try:
        # Known problematic but realistic clock-skew case; fixed identity must
        # avoid regenerating on every load without claiming whole-shell speed.

        os.utime(fixture.binary, (time.time() + 3600, time.time() + 3600))
        definitions = fixture.definitions
        if label == "baseline":
          definitions = old + 'compdef() { :; }\n_ZSH_CACHE_DIR="$CACHE"\n'
        start = time.perf_counter()
        result = fixture.shell(definitions, "_load_cached_completion docker\n" * args.loads)
        fixture.ok(result)
        samples.append(time.perf_counter() - start)
        generated.append(len(fixture.calls("docker")))
      finally:
        fixture.doCleanups()
    measurements[label] = {
      "median_seconds": round(statistics.median(samples), 4),
      "samples_seconds": [round(x, 4) for x in samples],
      "generator_calls": generated,
    }
  print(
    json.dumps(
      {
        "scenario": "future-mtime stub executable; repeated loader in isolated zsh",
        "baseline_revision": revision,
        "baseline_source": source_path,
        "loads_per_sample": args.loads,
        "measurements": measurements,
      },
      indent=2,
    )
  )
  return 0 if measurements["worktree"]["generator_calls"] == [1] * args.samples else 1


if __name__ == "__main__":
  raise SystemExit(main())
