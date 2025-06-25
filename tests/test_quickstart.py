from __future__ import annotations

from pathlib import Path
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "quickstart.sh"


def run_quickstart(
  dest: Path, remote: str | None = None, push: bool = False, branch: str | None = None
) -> None:
  env = os.environ.copy()
  env["QUICKSTART_TEMPLATE_REPO"] = str(ROOT)
  cmd = [str(SCRIPT), "-C", str(dest)]
  if remote:
    cmd += ["-u", remote]
  if branch:
    cmd += ["-b", branch]
  if push:
    cmd.append("--push")
  subprocess.run(cmd, check=True, env=env)


def test_quickstart_initializes_repo(tmp_path: Path) -> None:
  run_quickstart(tmp_path)
  result = subprocess.run(
    ["git", "-C", str(tmp_path), "rev-list", "--count", "HEAD"],
    capture_output=True,
    text=True,
    check=True,
  )
  assert result.stdout.strip() == "1"


def test_quickstart_configures_remote(tmp_path: Path) -> None:
  remote = "git@example.com:repo.git"
  run_quickstart(tmp_path, remote=remote)
  result = subprocess.run(
    ["git", "-C", str(tmp_path), "remote", "get-url", "origin"],
    capture_output=True,
    text=True,
    check=True,
  )
  assert result.stdout.strip() == remote


def test_quickstart_pushes_to_remote(tmp_path: Path) -> None:
  project_dir = tmp_path / "proj"
  remote_repo = tmp_path / "remote.git"
  subprocess.run(["git", "init", "--bare", str(remote_repo)], check=True)
  run_quickstart(project_dir, remote=str(remote_repo), push=True)
  result = subprocess.run(
    ["git", "--git-dir", str(remote_repo), "rev-list", "--count", "HEAD"],
    capture_output=True,
    text=True,
    check=True,
  )
  assert result.stdout.strip() == "1"


def test_quickstart_removes_script(tmp_path: Path) -> None:
  run_quickstart(tmp_path)
  assert not (tmp_path / "quickstart.sh").exists()


def test_quickstart_uses_branch_mapping(tmp_path: Path) -> None:
  src = "feature"
  dst = "foobar"
  subprocess.run(["git", "-C", str(ROOT), "branch", src], check=True)
  try:
    run_quickstart(tmp_path, branch=f"{src}:{dst}")
    result = subprocess.run(
      ["git", "-C", str(tmp_path), "rev-parse", "--abbrev-ref", "HEAD"],
      capture_output=True,
      text=True,
      check=True,
    )
    assert result.stdout.strip() == dst
  finally:
    subprocess.run(["git", "-C", str(ROOT), "branch", "-D", src], check=True)
