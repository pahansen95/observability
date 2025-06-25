#!/usr/bin/env python3
"""Layer 4: Developer Experience - Configure git hooks and helper scripts."""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

from helpers.bootstrap.state import BootstrapState
from helpers.utils import configure_logging, run_command
import helpers.tools.python as pytools

logger = logging.getLogger(__name__)


def install_pre_commit_hooks(project_root: Path) -> dict[str, Any]:
  """Install pre-commit hooks in the repository."""
  result = {"pre_commit": {"installed": False, "error": None}}

  pre_commit = project_root / pytools.resolve_venv_path("default") / "bin" / "pre-commit"

  if not pre_commit.exists():
    result["pre_commit"]["error"] = "pre-commit not found"
    logger.warning("pre-commit not available, skipping hook installation")
    return result

  try:
    run_command([str(pre_commit), "install"], check=True)
    result["pre_commit"]["installed"] = True
    logger.info("Pre-commit hooks installed successfully")
  except subprocess.CalledProcessError as e:
    result["pre_commit"]["error"] = str(e)
    logger.error("Failed to install pre-commit hooks: %s", e)

  return result


def verify_pre_commit_hooks(project_root: Path) -> dict[str, Any]:
  """Check if pre-commit hooks are installed."""
  hooks_dir = project_root / ".git" / "hooks" / "pre-commit"
  return {"pre_commit": {"installed": hooks_dir.exists()}}


def verify_helper_scripts(project_root: Path) -> dict[str, Any]:
  """Verify helper scripts are accessible."""
  result = {"helpers": {"available": [], "missing": []}}

  helpers_dir = project_root / "helpers"
  expected_helpers = [
    "bootstrap",
    "tool",
    "tools/build.py",
    "tools/test.py",
    "tools/format.py",
    "tools/lint.py",
    "tools/docs.py",
    "tools/python.py",
    "tools/cache.py",
  ]

  for helper in expected_helpers:
    helper_path = helpers_dir / helper
    if helper_path.exists():
      result["helpers"]["available"].append(helper)
    else:
      result["helpers"]["missing"].append(helper)

  if result["helpers"]["missing"]:
    logger.warning("Missing helpers: %s", ", ".join(result["helpers"]["missing"]))
  else:
    logger.info("All helper scripts verified")

  return result


def run(
  state: BootstrapState,
  *,
  skip_pre_commit: bool = False,
) -> BootstrapState:
  """Execute the developer experience layer."""

  project_root = Path(state.project_root)
  layer_results: dict[str, Any] = {}

  if not skip_pre_commit:
    pre_res = install_pre_commit_hooks(project_root)
    state.record_decision("pre_commit", "install" if pre_res["pre_commit"]["installed"] else "skip")
    layer_results.update(pre_res)
    verify_res = verify_pre_commit_hooks(project_root)
    state.record_verification("pre_commit", verify_res)
    layer_results.update(verify_res)

  verify_helpers = verify_helper_scripts(project_root)
  state.record_verification("helpers", verify_helpers)
  layer_results.update(verify_helpers)

  state.layer = 4
  state.layers.append({"layer": 4, "name": "developer_experience", "results": layer_results})

  return state


def main() -> None:
  """Configure developer experience components."""
  parser = argparse.ArgumentParser(description="Layer 4: Developer Experience")
  parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
  parser.add_argument("--skip-pre-commit", action="store_true", help="Skip pre-commit setup")
  args = parser.parse_args()

  configure_logging(args.verbose)

  # Read input state from stdin
  if not sys.stdin.isatty():
    try:
      input_state = json.load(sys.stdin)
      logger.debug("Received input state: %s", input_state)
    except json.JSONDecodeError:
      logger.warning("Failed to parse input JSON, using defaults")
      input_state = {}
  else:
    input_state = {}

  if "project_root" not in input_state:
    input_state["project_root"] = str(Path.cwd())

  state = BootstrapState.from_dict(input_state)
  state = run(
    state,
    skip_pre_commit=args.skip_pre_commit,
  )

  # Output state to stdout
  json.dump(state.to_dict(), sys.stdout, indent=2)
  print()  # Newline for readability

  logger.info("Layer 4 configuration complete")


if __name__ == "__main__":
  main()
